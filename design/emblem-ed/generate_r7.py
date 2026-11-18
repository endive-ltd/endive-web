"""Endive E-D rings, round 7 ("refined"): smooth superellipse rings.

Each ring's centre line is a superellipse whose exponent changes smoothly from
the left half to the right half (n_left -> n_right), so one side can be a
softly squared spine (E) and the other a round bowl (D) with no corners and no
tangent or curvature breaks. The band is drawn by offsetting the centre line
with a width that eases slightly thinner where it crosses the other ring.
Grooves are true parallel strips. Under-crossings are cut with an even gap and
their cut ends are softly rounded. Over/under alternates along the E ring; the
linking number is checked so the rings genuinely interlock.

Usage:  python3 generate_r7.py OUT_DIR       (variants.json, per-cut SVGs, picks/)
Needs:  pip install shapely numpy
"""
import json, math, os, sys
import numpy as np
from shapely.geometry import Polygon, LinearRing, Point
from shapely.ops import unary_union
from shapely import affinity

FLAT_HALF, ROUND_HALF = 94.0, 96.0   # flat extents fit 94, round extents may overshoot to 96

# ---------- centre line ---------------------------------------------------
def ring_cl(x0, y0, x1, y1, rL, nL, rR, nR, N=1800):
    """Rounded rectangle centre line whose corners are superellipse quarters.
    Left corners: radius rL, exponent nL; right corners: radius rR, exponent nR.
    With n > 2 the corner meets the straight sides with zero curvature (G2, no kink);
    rR equal to half the height gives a full round D bowl."""
    pts = []
    def corner(cx, cy, r, n, a0):
        for t in np.linspace(0, np.pi / 2, 400):
            th = a0 + t
            c, s_ = np.cos(th), np.sin(th)
            pts.append((cx + r * np.sign(c) * abs(c) ** (2 / n), cy + r * np.sign(s_) * abs(s_) ** (2 / n)))
    # y down; go clockwise on screen: top-left -> top-right -> bottom-right -> bottom-left
    corner(x1 - rR, y0 + rR, rR, nR, -np.pi / 2)        # top-right
    corner(x1 - rR, y1 - rR, rR, nR, 0)                 # bottom-right
    corner(x0 + rL, y1 - rL, rL, nL, np.pi / 2)         # bottom-left
    corner(x0 + rL, y0 + rL, rL, nL, np.pi)             # top-left
    P = np.array(pts)
    keep = np.r_[True, np.hypot(*np.diff(P, axis=0).T) > 1e-9]; P = P[keep]
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(np.r_[P, P[:1]], axis=0).T))]
    u = np.linspace(0, d[-1], N, endpoint=False)
    Pc = np.r_[P, P[:1]]
    return np.c_[np.interp(u, d, Pc[:, 0]), np.interp(u, d, Pc[:, 1])]

def ring_se(cx, cy, a, b, nL, nR, k=2.2, N=1800):
    """Whole-ring superellipse centre line; the exponent blends smoothly from nL on
    the left half to nR on the right half, so one side can be a calmer, squarer
    spine (E) and the other a rounder bowl (D) with no joins at all."""
    t = np.linspace(0, 2 * np.pi, 24000, endpoint=False)
    c, s_ = np.cos(t), np.sin(t)
    n = nL + (nR - nL) * (0.5 + 0.5 * np.tanh(k * c))
    P = np.c_[a * np.sign(c) * np.abs(c) ** (2 / n), b * np.sign(s_) * np.abs(s_) ** (2 / n)]
    d = np.r_[0, np.cumsum(np.hypot(*np.diff(np.r_[P, P[:1]], axis=0).T))]
    u = np.linspace(0, d[-1], N, endpoint=False)
    Pc = np.r_[P, P[:1]]
    return np.c_[np.interp(u, d, Pc[:, 0]) + cx, np.interp(u, d, Pc[:, 1]) + cy]

def make_ring(p):
    return ring_se(*p) if len(p) == 6 else ring_cl(*p)

def bow(P, beta):
    """Gently bow the ring's long sides outward (max `beta` of the half-width at the
    middle, easing to zero at the ends), so long sides have tension instead of
    being ruler-straight."""
    if not beta: return P
    c = (P.max(0) + P.min(0)) / 2; h = (P.max(0) - P.min(0)) / 2
    Q = P - c
    if h[1] >= h[0]:   # upright ring: bow x
        Q[:, 0] *= 1 + beta * np.cos(np.clip(Q[:, 1] / h[1], -1, 1) * np.pi / 2) ** 2
    else:              # flat ring: bow y
        Q[:, 1] *= 1 + beta * np.cos(np.clip(Q[:, 0] / h[0], -1, 1) * np.pi / 2) ** 2
    return Q + c

def normals(P):
    T = np.roll(P, -1, 0) - np.roll(P, 1, 0)
    T /= np.linalg.norm(T, axis=1)[:, None]
    return np.c_[T[:, 1], -T[:, 0]], T

def min_radius(P):
    _, T = normals(P)
    ds = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
    dT = np.linalg.norm(np.roll(T, -1, 0) - T, axis=1)
    return float(np.min(ds / np.maximum(dT, 1e-12)))

# ---------- bands ---------------------------------------------------------
def strip(P, w, u1, u2):
    Nn, _ = normals(P)
    A = Polygon(P + Nn * (u1 * w / 2)[:, None]).buffer(0)
    B = Polygon(P + Nn * (u2 * w / 2)[:, None]).buffer(0)
    big, small = (A, B) if A.area > B.area else (B, A)
    return big.difference(small)

def width_profile(P, w0, cross_pts, thin=0.06, sigma=2.6):
    """Band width along the ring: eases thinner (by `thin`) around each crossing."""
    if not cross_pts or thin == 0:
        return np.full(len(P), w0)
    ds = np.linalg.norm(np.roll(P, -1, 0) - P, axis=1)
    s = np.r_[0, np.cumsum(ds)[:-1]]; L = ds.sum()
    f = np.ones(len(P))
    for q in cross_pts:
        i = int(np.argmin(np.linalg.norm(P - q, axis=1)))
        dd = np.abs(s - s[i]); dd = np.minimum(dd, L - dd)
        f -= thin * np.exp(-(dd / (sigma * w0)) ** 2 * 0.5)
    return w0 * f

def crossings(PE, PD):
    a = LinearRing(PE); b = LinearRing(PD)
    inter = a.intersection(b)
    pts = [g for g in getattr(inter, 'geoms', [inter]) if g.geom_type == 'Point']
    pts.sort(key=lambda p: a.project(p))
    return pts, a, b

def tangent(ring, p, eps=0.1):
    s = ring.project(p); L = ring.length
    q0 = ring.interpolate((s - eps) % L); q1 = ring.interpolate((s + eps) % L)
    v = np.array([q1.x - q0.x, q1.y - q0.y]); return v / np.linalg.norm(v)

# ---------- one cut -------------------------------------------------------
CUTS = {
    'grooved': dict(w=18.0, gap=2.2, grooves=(0.25, 0.39), round=0.6),
    'solid':   dict(w=22.0, gap=2.7, grooves=None, round=1.3),
}

def build(spec, cut):
    C = CUTS[cut]
    PE = bow(make_ring(spec['E']), spec.get('bow', 0)); PD = bow(make_ring(spec['D']), spec.get('bow', 0))
    # fit: flat (vertical) extent -> 94, round (horizontal) extent may reach 96
    allP = np.r_[PE, PD]
    wmax = C['w'] / 2
    x0, y0 = allP.min(0) - wmax; x1, y1 = allP.max(0) + wmax
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    hx, hy = (x1 - x0) / 2, (y1 - y0) / 2
    s = min((FLAT_HALF - wmax) / (hy - wmax), (ROUND_HALF - wmax) / (hx - wmax))
    PE = (PE - [cx, cy]) * s; PD = (PD - [cx, cy]) * s
    pts, rE, rD = crossings(PE, PD)
    qs = [np.array([p.x, p.y]) for p in pts]
    thin = spec.get('thin', 0.06)
    wE = width_profile(PE, C['w'] * spec.get('kE', 1.0), qs, thin)
    wD = width_profile(PD, C['w'] * spec.get('kD', 1.0), qs, thin)
    FE = strip(PE, wE, -1, 1); FD = strip(PD, wD, -1, 1)
    def vis(P, w, F):
        if not C['grooves']: return F
        g1, g2 = C['grooves']
        return unary_union([strip(P, w, -1, -g2), strip(P, w, -g1, g1), strip(P, w, g2, 1)])
    Ev = vis(PE, wE, FE); Dv = vis(PD, wD, FD)
    start = spec.get('start', 'E')
    over = ['E' if ((i % 2 == 0) == (start == 'E')) else 'D' for i in range(len(pts))]
    lk = 0
    for p, o in zip(pts, over):
        tE = tangent(rE, p); tD = tangent(rD, p)
        to, tu = (tE, tD) if o == 'E' else (tD, tE)
        lk += np.sign(to[0] * tu[1] - to[1] * tu[0])
    xE = FD.buffer(C['gap'], quad_segs=32).intersection(FE)
    xD = FE.buffer(C['gap'], quad_segs=32).intersection(FD)
    cutE = cutD = False
    for p, o in zip(pts, over):
        src, tgt = (xD, 'D') if o == 'E' else (xE, 'E')
        for comp in getattr(src, 'geoms', [src]):
            if comp.distance(p) < 1e-6:
                if tgt == 'D': Dv = Dv.difference(comp.buffer(0.01)); cutD = True
                else: Ev = Ev.difference(comp.buffer(0.01)); cutE = True
    r = C['round']
    if cutD: Dv = Dv.buffer(-r, quad_segs=16).buffer(r, quad_segs=16)
    if cutE: Ev = Ev.buffer(-r, quad_segs=16).buffer(r, quad_segs=16)
    shape = unary_union([Ev, Dv])
    # optical centring: nudge x halfway from bbox centre towards the area centroid
    bx = (shape.bounds[0] + shape.bounds[2]) / 2
    dx = -(0.6 * bx + 0.4 * shape.centroid.x)
    dx = max(min(dx, 98 - shape.bounds[2]), -98 - shape.bounds[0])   # never clip the box
    shape = affinity.translate(shape, dx, -(shape.bounds[1] + shape.bounds[3]) / 2)
    polys = list(getattr(shape, 'geoms', [shape]))
    info = dict(crossings=len(pts), link=float(lk / 2), parts=len(polys),
                tiny=[round(p.area, 2) for p in polys if p.area < 8],
                minR=round(min(min_radius(PE), min_radius(PD)), 1),
                bounds=[round(v, 1) for v in shape.bounds])
    return shape, info

def to_path(geom, tol=0.015):
    geom = geom.simplify(tol, preserve_topology=True)
    out = []
    for p in getattr(geom, 'geoms', [geom]):
        for ring in [p.exterior] + list(p.interiors):
            c = list(ring.coords)[:-1]
            out.append('M' + 'L'.join(f'{x:.2f} {y:.2f}' for x, y in c) + 'Z')
    return ''.join(out)

# ---------- variants: E=(cx, cy, a, b, nLeft, nRight), D likewise ---------
PHI = (1 + 5 ** 0.5) / 2
V = []
def add(id, name, family, note, E, D, **kw):
    V.append(dict(id=id, name=name, family=family, note=note, E=E, D=D, **kw))

# ring = (x0, y0, x1, y1, rLeft, nLeft, rRight, nRight); pre-fit units, y down
# Superellipse rings: (cx, cy, a, b, n_left, n_right), pre-fit units, y down.
add('S1', 'N1, barely touched', 'Cross',
    'N1 almost exactly. The upright ring’s left side is a touch straighter and the flat ring’s right end a touch rounder. The safe choice.',
    (0, 0, 40, 94, 3.0, 2.7), (0, 0, 94, 40, 3.0, 2.55))
add('S2', 'Soft E, round D', 'Cross',
    'N1’s cross, but the upright ring has a calm, straighter back with softly squared corners (E), and the flat ring swells into a round bowl on the right (D).',
    (-4, 0, 40, 94, 3.8, 2.7), (4, 0, 94, 40, 3.8, 2.5))
add('S3', 'Golden cross', 'Cross',
    'S2 drawn to the golden ratio: each ring is 2.6× as long as it is wide (φ²) and the D slides right by a golden step. Airier holes.',
    (-10, 0, 36, 94, 3.8, 2.7), (10, 0, 94, 36, 3.8, 2.5))
add('S4', 'Calligraphic cross', 'Cross',
    'S2 with a gentle thick-and-thin: the band slims slightly where it dives under, like a pen stroke. The most hand-crafted feel.',
    (-4, 0, 40, 94, 3.8, 2.7), (4, 0, 94, 40, 3.8, 2.5), thin=0.13)
add('S5', 'Chain link, sleek', 'Chain link',
    'The D hooks through the E like two links, all soft curves: a calm E with a straighter back, a round D bowl. Reads E then D with no steps or arms.',
    (-36, 0, 56, 94, 4.2, 3.0), (34, 0, 64, 42, 3.8, 2.5))
add('S6', 'Chain link, middle bar', 'Chain link',
    'A slimmer D runs through the middle of the E, so it reads as the E’s middle bar before rounding off into the D.',
    (-34, 0, 52, 94, 4.2, 3.0), (36, 0, 70, 32, 3.8, 2.5))
add('S7', 'Chain link, golden', 'Chain link',
    'S5 on the golden ratio: the E is 1 : 1.618 and the D’s height is the E’s width ÷ 1.618. The calmest of the chain links.',
    (-32, 0, 94 / PHI, 94, 4.0, 3.0), (30, 0, 94 / PHI * 1.1, 94 / PHI ** 2 + 2, 3.8, 2.5))

PICK_FILES = {'S2': 'endive-ed-r7-soft-cross', 'S5': 'endive-ed-r7-chain', 'S1': 'endive-ed-r7-n1-touch'}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'build_r7'
    only = set(sys.argv[2:])
    os.makedirs(os.path.join(out, 'picks'), exist_ok=True)
    data = []
    for v in V:
        if only and v['id'] not in only: continue
        rec = {k: v[k] for k in ('id', 'name', 'family', 'note')}; rec['info'] = {}
        for cut in CUTS:
            shape, info = build(v, cut)
            rec[cut] = to_path(shape); rec['info'][cut] = info
            with open(os.path.join(out, f"{v['id']}-{cut}.svg"), 'w') as f:
                f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-100 -100 200 200"><path fill="#26734A" fill-rule="evenodd" d="{rec[cut]}"/></svg>\n')
            if v['id'] in PICK_FILES:
                for col, suf in (('#26734A', ''), ('#7DCAA1', '-mint'), ('#FFFFFF', '-white'), ('#101814', '-black')):
                    with open(os.path.join(out, 'picks', f"{PICK_FILES[v['id']]}-{cut}{suf}.svg"), 'w') as f:
                        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-100 -100 200 200"><path fill="{col}" fill-rule="evenodd" d="{rec[cut]}"/></svg>\n')
        print(v['id'], rec['info'])
        data.append(rec)
    with open(os.path.join(out, 'variants.json'), 'w') as f:
        json.dump(data, f)
