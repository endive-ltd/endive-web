"""Concept geometry for 'Endive Emblem: Blank Page'. Each concept returns a list of
(role, shapely geometry) layers in its own units; render.py fits and colours them."""
import math
import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from shapely import affinity
from engine import *

def circle3(a, b, c):
    ax, ay = a; bx, by = b; cx, cy = c
    d = 2 * (ax * (by - cy) + bx * (cy - ay) + cx * (ay - by))
    ux = ((ax*ax+ay*ay)*(by-cy)+(bx*bx+by*by)*(cy-ay)+(cx*cx+cy*cy)*(ay-by))/d
    uy = ((ax*ax+ay*ay)*(cx-bx)+(bx*bx+by*by)*(ax-cx)+(cx*cx+cy*cy)*(bx-ax))/d
    return np.array([ux, uy]), math.hypot(ax-ux, ay-uy)

def arc_through(a, m, b, n=1200):
    c, r = circle3(a, m, b)
    t0 = math.atan2(a[1]-c[1], a[0]-c[0]); tm = math.atan2(m[1]-c[1], m[0]-c[0]); t1 = math.atan2(b[1]-c[1], b[0]-c[0])
    def norm(x): return x % (2*math.pi)
    # choose direction from t0 to t1 that passes tm
    d1 = norm(t1 - t0); dm = norm(tm - t0)
    sweep = d1 if dm < d1 else d1 - 2*math.pi
    t = t0 + np.linspace(0, 1, n) * sweep
    return np.c_[c[0] + r*np.cos(t), c[1] + r*np.sin(t)]

# 1 -------------------------------------------------------------------------
def leaf_trinity():
    R = 90.0
    T = [np.array([R*math.cos(math.radians(a)), R*math.sin(math.radians(a))]) for a in (-90, 30, 150)]
    strands = []
    for k in range(3):
        a, b, c = T[k], T[(k+1) % 3], T[(k+2) % 3]
        m = c / np.linalg.norm(c) * 40.0
        P = arc_through(a, m, b)[2:-2]
        strands.append(Strand(P, lambda u: 15.0 * (0.10 + 0.90 * np.sin(np.pi*u) ** 0.75), closed=False))
    res = weave(strands, gap=2.3, groove=dict(offsets=[0.0], width=1.7, taper=20, clear=2), round_r=0.5)
    layers = [('main', unary_union(res['per_strand']))]
    for sh in res['shadows']: layers.append(('shadow', sh[1]))
    return layers

# 2 -------------------------------------------------------------------------
def endive_spear():
    specs = [
        ((0, 94), (2, -96), 38, -0.02, 0.0),
        ((-3, 94), (-24, -70), 40, 0.05, 0.2),
        ((3, 94), (26, -58), 40, -0.05, -0.2),
        ((-5, 95), (-32, -30), 36, 0.06, 0.25),
        ((5, 95), (33, -20), 36, -0.06, -0.25),
    ]
    leaves = []
    for base, tip, w, bend, cup in specs:
        poly, mid, hw = leaf(base, tip, w, bend=bend, cup=cup, shape=0.7, tipfrac=0.38)
        leaves.append((poly, mid))
    layers = []
    for i, (poly, mid) in enumerate(leaves):
        vis = poly
        for j in range(i+1, len(leaves)):
            vis = vis.difference(leaves[j][0].buffer(2.4))
        rib = taper_strip(mid, 2.0, 0.10, 0.92, 0.9)
        layers.append((f'leaf{i}', vis.difference(rib)))
    return layers

# 3 -------------------------------------------------------------------------
def crescent_bloom(n=5):
    strands = []
    for k in range(n):
        th = 2*math.pi*k/n
        c = np.array([math.cos(th), math.sin(th)]) * 24
        t = np.linspace(th + math.radians(30), th + math.radians(195), 1600)
        P = np.c_[c[0] + 60*np.cos(t), c[1] + 60*np.sin(t)]
        strands.append(Strand(P, lambda u: 17 * np.sin(np.pi*u) ** 0.75 + 0.3, closed=False))
    res = weave(strands, gap=2.2, groove=dict(offsets=[0.0], width=1.5, taper=14, clear=1), round_r=0.4, min_part=12)
    layers = [('main', unary_union(res['per_strand']))]
    for sh in res['shadows']: layers.append(('shadow', sh[1]))
    return layers

# 4 -------------------------------------------------------------------------
def twin_leaf_ribbon():
    TR = np.array([96.0, 0.0]); TL = -TR; O = np.array([0.0, 0.0])
    ur = arc_through(O, np.array([50.0, -36.0]), TR)
    lr = arc_through(TR, np.array([50.0, 36.0]), O)
    ul = arc_through(O, np.array([-50.0, -36.0]), TL)
    ll = arc_through(TL, np.array([-50.0, 36.0]), O)
    s1 = np.r_[ll[1:-1], ur[1:-1]]
    s2 = np.r_[lr[1:-1], ul[1:-1]]
    prof = lambda u: 19 * (0.10 + 0.90 * np.sin(np.pi*u) ** 0.8)
    A = Strand(s1, prof); B = Strand(s2, prof)
    res = weave([A, B], gap=2.6, groove=dict(offsets=[-0.4, 0.4], width=1.1, taper=18, clear=2), round_r=0.5)
    layers = [('ribbon', unary_union(res['per_strand']))]
    for sh in res['shadows']: layers.append(('shadow', sh[1]))
    return [(r, affinity.rotate(g, -24, origin=(0, 0))) for r, g in layers]

# 5 -------------------------------------------------------------------------
def sprout_from_dark():
    # a dark crescent "cellar" cradling one pale leaf of light
    ground = Point(0, 18).buffer(80, quad_segs=128).difference(Point(0, -6).buffer(78, quad_segs=128))
    ground = ground.intersection(box(-100, -10, 100, 120))
    lf, mid, _ = leaf((-2, 84), (6, -96), 62, bend=-0.10, cup=0.18, shape=0.62, tipfrac=0.40)
    rib = taper_strip(mid, 2.8, 0.06, 0.93, 0.9)
    ground = ground.difference(lf.buffer(3.4))
    return [('glow', Point(4, -20).buffer(98, quad_segs=64)), ('ground', ground), ('sprout', lf.difference(rib))]

# 6 -------------------------------------------------------------------------
def glass_rosette(n=6):
    leaves = []
    for k in range(n):
        th = 360 * k / n
        poly, mid, hw = leaf((0, 0), (0, -96), 46, bend=0.10, shape=0.8, tipfrac=0.5)
        leaves.append(affinity.rotate(poly, th, origin=(0, 0)))
    # overlap counts
    regions = {}
    from itertools import combinations
    cover = [unary_union(leaves)]
    lv = []
    for c in range(1, 4):
        acc = []
        for combo in combinations(range(n), c):
            g = leaves[combo[0]]
            for i in combo[1:]: g = g.intersection(leaves[i])
            if not g.is_empty: acc.append(g)
        lv.append(unary_union(acc) if acc else None)
    t1 = lv[0].difference(lv[1]); t2 = lv[1].difference(lv[2]) if lv[2] else lv[1]; t3 = lv[2]
    return [('tone1', t1), ('tone2', t2), ('tone3', t3)]

# 7 -------------------------------------------------------------------------
def brush_leaf():
    P = catmull([(-66, 94), (-38, 66), (-6, 34), (26, -2), (50, -40), (56, -74), (50, -97),
                 (30, -84), (-12, -54), (-30, -18), (-26, 14), (-6, 30), (30, 34), (74, 22)], closed=False, n=80)
    st = Strand(P, None, closed=False)
    _, T = normals(st.P, False)
    ang = np.arctan2(T[:, 1], T[:, 0])
    nib = math.radians(-50)
    u = st.s / st.L
    ends = np.clip(np.minimum(u / 0.10, (1 - u) / 0.14), 0, 1) ** 0.8
    tip_i = int(np.argmin(st.P[:, 1]))
    dtip = np.abs(st.s - st.s[tip_i])
    st.w = (2.2 + 19.0 * np.abs(np.sin(ang - nib)) ** 1.2) * (0.10 + 0.90 * ends) * (0.12 + 0.88 * smoothstep(dtip / 26))
    res = weave([st], gap=2.8, groove=None, round_r=0.4)
    layers = [('ink', res['per_strand'][0])]
    for sh in res['shadows']: layers.append(('shadow', sh[1]))
    return layers, st

# 8 -------------------------------------------------------------------------
def heart_of_leaves():
    def lens_arcs(base, tip, bulge):
        base = np.asarray(base, float); tip = np.asarray(tip, float)
        mid = (base + tip) / 2; v = tip - base; nrm = np.array([-v[1], v[0]]) / np.linalg.norm(v)
        a1 = arc_through(base, mid + nrm * bulge, tip)[2:-2]
        a2 = arc_through(tip, mid - nrm * bulge, base)[2:-2]
        return a1, a2
    prof = lambda u: 17 * (0.10 + 0.90 * np.sin(np.pi*u) ** 0.8)
    strands = []
    for base, tip in (((-96, 30), (40, -40)), ((96, -30), (-40, 40))):
        for arc in lens_arcs(base, tip, 30):
            strands.append(Strand(arc, prof))
    res = weave(strands, gap=2.4, groove=dict(offsets=[0.0], width=1.6, taper=16, clear=2), round_r=0.5)
    layers = [('main', unary_union(res['per_strand'][:2])), ('alt', unary_union(res['per_strand'][2:]))]
    for sh in res['shadows']: layers.append(('shadow', sh[1]))
    return [(r, affinity.rotate(g, -18, origin=(0, 0))) for r, g in layers]

# 9 -------------------------------------------------------------------------
def pentafoil():
    phi = np.linspace(0, 2*np.pi, 6000, endpoint=False)
    r = 64 + 22*np.cos(5*phi)
    P = np.c_[r*np.cos(2*phi), r*np.sin(2*phi)]
    st = Strand(P, 13, closed=True, n=3000)
    res = weave([st], gap=2.3, groove=dict(offsets=[-0.42, 0.42], width=1.1, taper=16, clear=1), round_r=0.5)
    layers = [('main', res['per_strand'][0])]
    for sh in res['shadows']: layers.append(('shadow', sh[1]))
    return [(r_, affinity.rotate(g, -90, origin=(0, 0))) for r_, g in layers]

# 10 ------------------------------------------------------------------------
def golden_head(N=55):
    ga = math.radians(137.50776)
    leaves = []
    for i in range(N):
        f = (i + 1) / N
        r_in = 4 + 44 * math.sqrt(f)
        L = 18 + 66 * f ** 0.85
        W = 9 + 19 * f ** 0.8
        th = i * ga
        d = np.array([math.cos(th), math.sin(th)])
        base = d * (r_in - L * 0.5); tip = d * (r_in + L * 0.5)
        poly, mid, hw = leaf(base, tip, W, bend=0.06, shape=0.75, tipfrac=0.42)
        leaves.append((f, poly))
    order = sorted(leaves, key=lambda t: -t[0])
    vis_all = []
    for k, (f, poly) in enumerate(order):
        vis = poly
        for f2, p2 in order[k+1:]:
            vis = vis.difference(p2.buffer(1.3))
        if not vis.is_empty: vis_all.append(vis)
    return [('head', unary_union(vis_all))]

# 11 ------------------------------------------------------------------------
def braided_spear():
    y = np.linspace(96, -98, 1800)
    v = (96 - y) / 194
    amp = 30 * np.sin(np.pi * np.clip(v, 0, 1) ** 0.72) ** 1.1
    strands = []
    for i in range(3):
        x = amp * np.sin(2*np.pi * 1.75 * v + 2*np.pi*i/3)
        strands.append(Strand(np.c_[x, y], lambda u: 16 * (0.08 + 0.92 * np.sin(np.pi * np.clip(u, 0, 1) ** 0.8) ** 0.6), closed=False))
    res = weave(strands, gap=2.3, groove=dict(offsets=[0.0], width=1.5, taper=12, clear=1), round_r=0.4, min_part=8)
    return [(f'strand{i}', g) for i, g in enumerate(res['per_strand'])]


# 12 ------------------------------------------------------------------------
def folded_leaf():
    """One leaf folded along its rib: a pale half and a shaded half, like paper."""
    base = np.array([-10.0, 92.0]); tip = np.array([22.0, -96.0])
    u = np.linspace(0, 1, 500)
    v = tip - base; L = np.linalg.norm(v); t_ = v / L; nrm = np.array([-t_[1], t_[0]])
    mid = base + np.outer(u, v) + np.outer(np.sin(np.pi*u) * 0.10 * L, nrm)
    a = np.where(u < 0.42, u / 0.42, (1 - u) / 0.58)
    prof = np.sin(np.clip(a, 0, 1) * np.pi / 2) ** 0.62
    N, _ = normals(mid, False)
    left = mid + N * (34 * prof)[:, None]
    right = mid - N * (22 * prof)[:, None]
    lh = Polygon(np.r_[left, mid[::-1]]).buffer(0)
    rh = Polygon(np.r_[mid, right[::-1]]).buffer(0)
    crease = taper_strip(mid, 2.2, 0.03, 0.97, 0.7)
    stem = taper_strip(bezier([(-10, 92), (-14, 98), (-20, 104), (-28, 108)], 80), 4, -0.3, 1.0, 0.6)
    return [('fold_a', lh.difference(crease)), ('fold_b', rh.difference(crease)), ('fold_b', stem)]
