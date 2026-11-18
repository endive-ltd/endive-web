"""Geometry engine for the 'blank page' emblem concepts.

Strands are smooth centre lines (open or closed) with a width profile. The engine
finds every crossing, works out a consistent over/under weave (2-colouring of
passages), cuts the under-strand with an even gap, adds inline grooves that taper
to sharp points as the band dives under or thins out, and returns shapely shapes
per strand plus soft-shadow shapes for depth. Leaves are pointed lens shapes
with an optional tapering mid-rib.
"""
import math
import numpy as np
from shapely.geometry import Polygon, LineString, Point, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

# ---------------- curve helpers -------------------------------------------
def resample(P, n, closed):
    P = np.asarray(P, float)
    Q = np.r_[P, P[:1]] if closed else P
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(Q, axis=0).T))]
    u = np.linspace(0, d[-1], n, endpoint=not closed)
    return np.c_[np.interp(u, d, Q[:, 0]), np.interp(u, d, Q[:, 1])]

def arclen(P, closed):
    Q = np.r_[P, P[:1]] if closed else P
    seg = np.hypot(*np.diff(Q, axis=0).T)
    s = np.r_[0, np.cumsum(seg)]
    return s[:len(P)], s[-1]

def normals(P, closed):
    if closed:
        T = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    else:
        T = np.gradient(P, axis=0)
    T = T / np.maximum(np.linalg.norm(T, axis=1)[:, None], 1e-12)
    return np.c_[-T[:, 1], T[:, 0]], T

def bezier(pts, n=200):
    """Cubic bezier chain: pts = [p0, c1, c2, p1, c1, c2, p2, ...]."""
    pts = np.asarray(pts, float); out = []
    for i in range(0, len(pts) - 1, 3):
        p0, c1, c2, p1 = pts[i:i + 4]
        t = np.linspace(0, 1, n, endpoint=False)[:, None]
        out.append((1 - t) ** 3 * p0 + 3 * (1 - t) ** 2 * t * c1 + 3 * (1 - t) * t ** 2 * c2 + t ** 3 * p1)
    out.append(pts[-1:])
    return np.vstack(out)

def catmull(pts, closed=True, n=60, alpha=0.5):
    """Centripetal Catmull-Rom through control points (smooth, no overshoot)."""
    P = np.asarray(pts, float)
    if closed:
        P = np.r_[P[-1:], P, P[:2]]
    else:
        P = np.r_[2 * P[:1] - P[1:2], P, 2 * P[-1:] - P[-2:-1]]
    out = []
    for i in range(1, len(P) - 2):
        p0, p1, p2, p3 = P[i - 1:i + 3]
        def tj(ti, a, b): return ti + np.linalg.norm(b - a) ** alpha + 1e-9
        t0 = 0; t1 = tj(t0, p0, p1); t2 = tj(t1, p1, p2); t3 = tj(t2, p2, p3)
        t = np.linspace(t1, t2, n, endpoint=False)[:, None]
        A1 = (t1 - t) / (t1 - t0) * p0 + (t - t0) / (t1 - t0) * p1
        A2 = (t2 - t) / (t2 - t1) * p1 + (t - t1) / (t2 - t1) * p2
        A3 = (t3 - t) / (t3 - t2) * p2 + (t - t2) / (t3 - t2) * p3
        B1 = (t2 - t) / (t2 - t0) * A1 + (t - t0) / (t2 - t0) * A2
        B2 = (t3 - t) / (t3 - t1) * A2 + (t - t1) / (t3 - t1) * A3
        out.append((t2 - t) / (t2 - t1) * B1 + (t - t1) / (t2 - t1) * B2)
    if not closed: out.append(P[-2:-1])
    return np.vstack(out)

def smoothstep(x):
    x = np.clip(x, 0, 1); return x * x * (3 - 2 * x)

# ---------------- strands ---------------------------------------------------
class Strand:
    def __init__(self, P, width, closed=False, n=2400, name=''):
        self.closed = closed
        self.P = resample(P, n, closed)
        self.s, self.L = arclen(self.P, closed)
        u = self.s / self.L
        self.w = np.asarray(width(u) if callable(width) else np.full(len(self.P), width), float)
        self.name = name

def offset_poly(P, w, closed, lo=-1, hi=1):
    N, _ = normals(P, closed)
    A = P + N * (lo * w / 2)[:, None]; B = P + N * (hi * w / 2)[:, None]
    if closed:
        pa, pb = Polygon(A).buffer(0), Polygon(B).buffer(0)
        big, small = (pa, pb) if pa.area > pb.area else (pb, pa)
        return big.difference(small)
    return Polygon(np.r_[A, B[::-1]]).buffer(0)

def find_crossings(strands, chunk=60):
    """Return list of crossings: (point, (si, idx_i), (sj, idx_j))."""
    pieces = []
    for si, st in enumerate(strands):
        n = len(st.P)
        rng = list(range(0, n, chunk))
        for a in rng:
            b = min(a + chunk + 1, n + (1 if st.closed else 0))
            idx = np.arange(a, b) % n
            pieces.append((si, idx, LineString(st.P[idx])))
    out = []
    for i in range(len(pieces)):
        si, ii, li = pieces[i]
        for j in range(i + 1, len(pieces)):
            sj, ij, lj = pieces[j]
            if si == sj:
                n = len(strands[si].P)
                # skip adjacent chunks of the same strand
                gap = min(abs(ii[0] - ij[0]), n - abs(ii[0] - ij[0]))
                if gap <= chunk: continue
            if not li.envelope.intersects(lj.envelope): continue
            inter = li.intersection(lj)
            if inter.is_empty: continue
            for g in getattr(inter, 'geoms', [inter]):
                if g.geom_type != 'Point': continue
                ki = ii[int(np.argmin(np.linalg.norm(strands[si].P[ii] - [g.x, g.y], axis=1)))]
                kj = ij[int(np.argmin(np.linalg.norm(strands[sj].P[ij] - [g.x, g.y], axis=1)))]
                out.append((np.array([g.x, g.y]), (si, int(ki)), (sj, int(kj))))
    # dedupe (chunk overlaps)
    ded = []
    for c in out:
        if all(np.linalg.norm(c[0] - d[0]) > 0.5 for d in ded): ded.append(c)
    return ded

def assign_weave(strands, crossings, flip=False):
    """2-colour passages: consecutive passages on a strand alternate, the two passages of a crossing differ."""
    passages = []   # (strand, idx, crossing_id)
    for ci, (p, a, b) in enumerate(crossings):
        passages.append((a[0], a[1], ci)); passages.append((b[0], b[1], ci))
    n = len(passages)
    adj = [[] for _ in range(n)]
    for ci in range(len(crossings)):
        adj[2 * ci].append(2 * ci + 1); adj[2 * ci + 1].append(2 * ci)
    for si, st in enumerate(strands):
        idxs = sorted([k for k in range(n) if passages[k][0] == si], key=lambda k: passages[k][1])
        for a, b in zip(idxs, idxs[1:]): adj[a].append(b); adj[b].append(a)
        if st.closed and len(idxs) > 1: adj[idxs[-1]].append(idxs[0]); adj[idxs[0]].append(idxs[-1])
    col = [None] * n; ok = True
    for s0 in range(n):
        if col[s0] is not None: continue
        col[s0] = 0; stack = [s0]
        while stack:
            u = stack.pop()
            for v in adj[u]:
                if col[v] is None: col[v] = 1 - col[u]; stack.append(v)
                elif col[v] == col[u]: ok = False
    over = []  # per crossing: which passage (0/1) is over
    for ci in range(len(crossings)):
        c = col[2 * ci] ^ (1 if flip else 0)
        over.append(0 if c == 0 else 1)
    return over, ok

def _open_poly(P, w, lo=-1, hi=1):
    N, _ = normals(P, False)
    A = P + N * (lo * w / 2)[:, None]; B = P + N * (hi * w / 2)[:, None]
    return Polygon(np.r_[A, B[::-1]]).buffer(0)

def weave(strands, gap=2.4, groove=None, flip=False, round_r=0.6, overrides=None, min_part=4.0):
    """Build visible shapes, piece by piece.
    groove: dict(offsets=[f...], width=g, taper=D, clear=c) - groove centre offsets as
    fractions of the half-width; grooves taper to points approaching under-passages.
    Returns dict(per_strand=[shape], shadows=[(strand, shape)], crossings, over, ok)."""
    cr = find_crossings(strands)
    over, ok = assign_weave(strands, cr, flip)
    if overrides:
        for k, v in overrides.items(): over[k] = v
    # passages per strand
    pas = {si: [] for si in range(len(strands))}
    for ci, (p, a, b) in enumerate(cr):
        for k, q in enumerate((a, b)):
            pas[q[0]].append((q[1], ci, over[ci] == k))
    # groove taper factor per strand
    gfac = []
    for si, st in enumerate(strands):
        f = np.ones(len(st.P))
        if groove:
            D = groove.get('taper', 18.0); clr = groove.get('clear', 0.0)
            for idx, ci, is_over in pas[si]:
                if is_over: continue
                d = np.abs(st.s - st.s[idx])
                if st.closed: d = np.minimum(d, st.L - d)
                f = np.minimum(f, smoothstep((d - clr) / D) ** 0.8)
        gfac.append(f)
    pieces = []   # (strand, idx array, polygon)
    for si, st in enumerate(strands):
        n = len(st.P)
        cuts = sorted(i for i, _, _ in pas[si])
        if not cuts:
            bounds = [(0, n)] if not st.closed else None
            if st.closed:
                pieces.append((si, np.arange(n), None)); continue
        else:
            if st.closed:
                mids = [((cuts[k] + ((cuts[(k + 1) % len(cuts)] - cuts[k]) % n) / 2)) % n for k in range(len(cuts))]
                mids = sorted(int(m) for m in mids)
                bounds = [(mids[k], mids[(k + 1) % len(mids)] if k + 1 < len(mids) else mids[0] + n) for k in range(len(mids))]
            else:
                mids = [0] + [int((cuts[k] + cuts[k + 1]) / 2) for k in range(len(cuts) - 1)] + [n]
                bounds = [(mids[k], mids[k + 1]) for k in range(len(mids) - 1)]
        for lo, hi in bounds:
            ids = np.arange(lo - 3, hi + 4)
            ids = ids % n if st.closed else ids[(ids >= 0) & (ids < n)]
            pieces.append((si, ids, None))
    built = []
    for si, ids, _ in pieces:
        st = strands[si]
        if len(ids) == len(st.P) and st.closed:
            poly = offset_poly(st.P, st.w, True)
            gsrc = (st.P, st.w, gfac[si], True)
        else:
            poly = _open_poly(st.P[ids], st.w[ids])
            gsrc = (st.P[ids], st.w[ids], gfac[si][ids], False)
        if groove:
            P, w, f, cl = gsrc
            wmax = st.w.max()
            gw = groove['width'] * f * np.clip(w / wmax, 0, 1) ** groove.get('wpow', 1.0)
            Nn, _ = normals(P, cl)
            gs = []
            for o in groove['offsets']:
                C = P + Nn * (o * w / 2)[:, None]
                gs.append(offset_poly(C, gw, True) if cl else _open_poly(C, gw))
            poly = poly.difference(unary_union(gs))
        built.append([si, ids, poly])
    shadows = []
    for ci, (p, a, b) in enumerate(cr):
        o_pas, u_pas = (a, b) if over[ci] == 0 else (b, a)
        so, su = o_pas[0], u_pas[0]
        rad = max(strands[so].w[o_pas[1]], strands[su].w[u_pas[1]]) * 2.5
        disk = Point(p).buffer(rad)
        over_local = local_piece(strands[so], o_pas[1], disk)
        cut = over_local.buffer(gap, quad_segs=24).intersection(disk)
        for item in built:
            si, ids, poly = item
            if si == su and u_pas[1] in set(ids.tolist()):
                item[2] = poly.difference(cut)
        shadows.append((su, over_local.buffer(gap * 2.5, quad_segs=24).difference(over_local.buffer(gap * 0.6)).intersection(disk)))
    per = []
    for si in range(len(strands)):
        u = unary_union([poly for s_, ids, poly in built if s_ == si])
        if round_r: u = u.buffer(-round_r, quad_segs=12).buffer(round_r, quad_segs=12)
        parts = [g for g in getattr(u, 'geoms', [u]) if g.area > min_part]
        per.append(unary_union(parts) if parts else u)
    return dict(per_strand=per, shadows=shadows, crossings=cr, over=over, ok=ok)

def local_piece(st, idx, region, span=None):
    """Ribbon polygon of the strand near index idx (enough to cover `region`)."""
    n = len(st.P)
    if span is None:
        r = math.sqrt(region.area / math.pi) * 1.6
        ds = st.L / n
        span = int(r / ds) + 2
    ids = np.arange(idx - span, idx + span + 1)
    if st.closed: ids = ids % n
    else: ids = ids[(ids >= 0) & (ids < n)]
    P = st.P[ids]; w = st.w[ids]
    N, _ = normals(P, False)
    return Polygon(np.r_[P + N * (w / 2)[:, None], (P - N * (w / 2)[:, None])[::-1]]).buffer(0)

# ---------------- leaves ----------------------------------------------------
def leaf(base, tip, width, bend=0.0, cup=0.0, n=300, shape=0.85, tipfrac=0.5):
    """Pointed leaf from base to tip. width = max width. bend = sideways bow of the midline
    (fraction of length). cup = asymmetry (one side fuller). Returns (polygon, midline)."""
    base = np.asarray(base, float); tip = np.asarray(tip, float)
    v = tip - base; L = np.linalg.norm(v); t_ = v / L; nrm = np.array([-t_[1], t_[0]])
    u = np.linspace(0, 1, n)
    mid = base + np.outer(u, v) + np.outer(np.sin(np.pi * u) * bend * L, nrm)
    # half-width profile: pointed both ends, fullest at tipfrac-ish
    a = np.where(u < tipfrac, u / tipfrac, (1 - u) / (1 - tipfrac))
    hw = width / 2 * np.sin(np.clip(a, 0, 1) * np.pi / 2) ** shape
    N, _ = normals(mid, False)
    left = mid + N * (hw * (1 + cup))[:, None]
    right = mid - N * (hw * (1 - cup))[:, None]
    return Polygon(np.r_[left, right[::-1]]).buffer(0), mid, hw

def taper_strip(mid, w0, start=0.05, end=0.85, pow_=1.0):
    """A thin strip along `mid` that swells and tapers to points at both ends (a leaf rib / groove)."""
    n = len(mid); u = np.linspace(0, 1, n)
    a = np.clip((u - start) / (end - start), 0, 1)
    w = w0 * np.sin(a * np.pi) ** pow_
    N, _ = normals(mid, False)
    return Polygon(np.r_[mid + N * (w / 2)[:, None], (mid - N * (w / 2)[:, None])[::-1]]).buffer(0)

# ---------------- svg -------------------------------------------------------
def path_d(geom, tol=0.02):
    if geom is None or geom.is_empty: return ''
    geom = geom.simplify(tol, preserve_topology=True)
    out = []
    for p in getattr(geom, 'geoms', [geom]):
        if p.geom_type != 'Polygon': continue
        for ring in [p.exterior] + list(p.interiors):
            c = list(ring.coords)[:-1]
            if len(c) < 3: continue
            out.append('M' + 'L'.join(f'{x:.2f} {y:.2f}' for x, y in c) + 'Z')
    return ''.join(out)

def fit(geoms, half=92.0):
    """Uniformly scale & centre a list of shapely geometries into +-half."""
    allg = unary_union([g for g in geoms if g is not None and not g.is_empty])
    x0, y0, x1, y1 = allg.bounds
    s = half / max((x1 - x0) / 2, (y1 - y0) / 2)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return [affinity.scale(affinity.translate(g, -cx, -cy), s, s, origin=(0, 0)) if g is not None else None for g in geoms], (cx, cy, s)
