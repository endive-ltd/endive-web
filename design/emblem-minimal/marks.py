"""Endive minimal emblem concepts (round 9).

Every mark is one colour, built only from circles and straight cuts, so it is exact,
scales to a 16 px favicon and can be redrawn with a compass. Each function returns
(shape, construction) where construction is a list of circles (cx, cy, r) used.
"""
import math
import numpy as np
from shapely.geometry import Point, Polygon, box, LineString
from shapely.ops import unary_union
from shapely import affinity

Q = 512  # circle smoothness

def C(x, y, r):
    return Point(x, y).buffer(r, quad_segs=Q)

def vesica(R, d):
    """Lens = intersection of two circles radius R, centres (+-d, 0). Width 2(R-d), height 2*sqrt(R^2-d^2)."""
    return C(-d, 0, R).intersection(C(d, 0, R)), [(-d, 0, R), (d, 0, R)]

def band(geom_line, w):
    return geom_line.buffer(w / 2, cap_style=2, quad_segs=Q)

def leaf_split():
    """A leaf split cleanly in two: fair shares (Tab) and a leaf (Endive)."""
    L, cons = vesica(100, 62)
    L = affinity.rotate(L, 40, origin=(0, 0))
    cut = band(affinity.rotate(LineString([(0, -200), (0, 200)]), 40, origin=(0, 0)), 9)
    halves = L.difference(cut)
    parts = sorted(getattr(halves, 'geoms', [halves]), key=lambda p: p.centroid.x)
    a, b = parts[0], parts[-1]
    # slide one half along the axis so the split reads as a deliberate offset
    ax = np.array([math.sin(math.radians(40)), -math.cos(math.radians(40))])
    b = affinity.translate(b, *(ax * 14))
    cons = [(c[0] * math.cos(math.radians(40)), c[0] * math.sin(math.radians(40)), c[2]) for c in cons]
    return unary_union([a, b]), cons

def bud():
    """Endive head: a pointed drop (circle + two tangent arcs) with one inner leaf cut out by a hairline."""
    a, R = 58, 150
    x0 = R - a
    top = C(-x0, 0, R).intersection(C(x0, 0, R)).intersection(box(-300, -300, 300, 0))
    drop = unary_union([top, C(0, 0, a)])
    # inner leaf: a narrower lens from the same apex down to the centre
    apex = -math.sqrt(R * R - x0 * x0)
    R2 = 120; x2 = 94
    inner = C(-x2, -24, R2).intersection(C(x2, -24, R2))
    g = 7
    ring = inner.buffer(g).difference(inner)
    shape = drop.difference(ring.intersection(box(-300, -300, 300, 300)))
    # open the inner leaf's lower tip into the base so it grows from the heart
    return shape, [(-x0, 0, R), (x0, 0, R), (0, 0, a), (-x2, -24, R2), (x2, -24, R2)]

def crescent_seed():
    """Grown in the dark: a crescent cradling a leaf."""
    outer = C(0, 0, 92); cut = C(0, -30, 80)
    cres = outer.difference(cut)
    L, cons = vesica(78, 52)
    L = affinity.rotate(L, 90, origin=(0, 0))
    L = affinity.scale(L, 0.82, 1.0, origin=(0, 0))
    L = affinity.translate(L, 0, -38)
    shape = unary_union([cres.difference(L.buffer(8)), L])
    return shape, [(0, 0, 92), (0, -30, 80)]

def leaf_link():
    """Two leaves linked like rings: connection, heir to the N1 knot."""
    def lens_ring(rot, dx):
        Lo, _ = vesica(100, 58); Li, _ = vesica(100 - 22, 58)
        ring = Lo.difference(Li)
        ring = affinity.rotate(ring, rot, origin=(0, 0))
        return affinity.translate(ring, dx, 0)
    A = lens_ring(90 + 0, -36); B = lens_ring(90, 36)
    A = affinity.rotate(A, 0); 
    gap = 7
    X = A.intersection(B)
    comps = sorted(getattr(X, 'geoms', [X]), key=lambda p: p.centroid.y)
    top, bot = comps[0], comps[-1]
    # A over at top, B over at bottom
    Bv = B.difference(A.buffer(gap).intersection(top.buffer(30)))
    Av = A.difference(B.buffer(gap).intersection(bot.buffer(30)))
    return affinity.rotate(unary_union([Av, Bv]), -30, origin=(0, 0)), []

def two_leaves():
    """Two leaves meeting at the stem: a sprout that is also a heart (Soft Spot)."""
    L, _ = vesica(100, 66)
    L = affinity.rotate(L, 90, origin=(0, 0))          # vertical lens, tips at +-74.8
    h = math.sqrt(100**2 - 66**2)
    L = affinity.translate(L, 0, -h)                     # bottom tip at origin
    A = affinity.rotate(L, -34, origin=(0, 0)); B = affinity.rotate(L, 34, origin=(0, 0))
    gap = 8
    shape = unary_union([A.difference(B.buffer(gap)), B.intersection(box(-300, -300, 300, 300)).difference(A.buffer(0))])
    shape = unary_union([A, B.difference(A.buffer(gap))])
    return shape, []

def golden_leaf():
    """An asymmetric leaf from two arcs whose radii are in the golden ratio, with a rib cut."""
    phi = (1 + 5 ** 0.5) / 2
    R1 = 120; R2 = R1 / phi * 1.35
    # both circles pass through the base (0,90) and the tip (0,-90)
    def through(r, side):
        h = math.sqrt(r * r - 90 * 90); return (side * h, 0, r)
    c1 = through(R1, 1); c2 = through(R2, -1)
    L = C(c1[0], c1[1], c1[2]).intersection(C(c2[0], c2[1], c2[2]))
    # rib: arc of a large circle from base to near tip, as a hairline
    rc = (150, 0, math.hypot(150, 90))
    rib_circle = C(*rc[:2], rc[2])
    rib = rib_circle.buffer(3.6).difference(rib_circle.buffer(-3.6)).intersection(box(-200, -66, 200, 92))
    shape = affinity.rotate(L.difference(rib), 30, origin=(0, 0))
    return shape, [c1, c2, rc]

def nested_leaves():
    """Leaf inside a leaf: the endive's layered heart in two strokes."""
    Lo, _ = vesica(100, 60); Li, _ = vesica(100, 60)
    Lo = affinity.rotate(Lo, 90, origin=(0, 0)); h = math.sqrt(100**2 - 60**2)
    outer_ring = Lo.difference(Lo.buffer(-16))
    inner = affinity.scale(Lo, 0.46, 0.62, origin=(0, h))
    shape = unary_union([outer_ring, inner])
    return affinity.rotate(shape, 0, origin=(0, 0)), []

def loop_leaf():
    """A single monoline loop that draws a leaf and crosses itself at the stem."""
    # leaf outline from two arcs, opened at the base into a crossing stem
    R, d = 100, 62
    t = np.linspace(0, 1, 800)
    h = math.sqrt(R * R - d * d)
    # right arc from base to tip: circle centre (-d, 0)
    a0 = math.atan2(h, d); a1 = math.atan2(-h, d)
    right = np.c_[-d + R * np.cos(a0 + (a1 - a0) * t), R * np.sin(a0 + (a1 - a0) * t)]
    left = np.c_[d + R * np.cos(math.pi - a1 + (a1 - a0) * t * 0 + (-(math.pi - a1) + (math.pi - a0)) * t), R * np.sin(math.pi - a1 + ((math.pi - a0) - (math.pi - a1)) * t)]
    stem_in = np.c_[np.linspace(34, 0, 60), np.linspace(h + 34, h, 60)]
    stem_out = np.c_[np.linspace(0, -30, 60), np.linspace(h, h + 30, 60)]
    w = 15
    A = LineString(np.r_[stem_in, right]).buffer(w / 2, cap_style=1, join_style=1, quad_segs=64)
    B = LineString(np.r_[left, stem_out]).buffer(w / 2, cap_style=1, join_style=1, quad_segs=64)
    # weave at the base: B passes under A
    cross = Point(0, h).buffer(30)
    B = B.difference(A.buffer(6).intersection(cross))
    return affinity.rotate(unary_union([A, B]), 32, origin=(0, 0)), []

MARKS = [
    ('split', 'Split Leaf', leaf_split), ('bud', 'Bud', bud), ('seed', 'Seed', crescent_seed),
    ('link', 'Leaf Link', leaf_link), ('sprout', 'Two Leaves', two_leaves), ('golden', 'Golden Leaf', golden_leaf),
    ('nested', 'Nested Leaf', nested_leaves), ('loop', 'Loop Leaf', loop_leaf),
]

def fit(shape, half=86.0):
    x0, y0, x1, y1 = shape.bounds
    s = half / max((x1 - x0) / 2, (y1 - y0) / 2)
    cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    return affinity.scale(affinity.translate(shape, -cx, -cy), s, s, origin=(0, 0)), (cx, cy, s)

def path_d(geom, tol=0.03):
    geom = geom.simplify(tol, preserve_topology=True)
    out = []
    for p in getattr(geom, 'geoms', [geom]):
        for ring in [p.exterior] + list(p.interiors):
            c = list(ring.coords)[:-1]
            out.append('M' + 'L'.join(f'{x:.2f} {y:.2f}' for x, y in c) + 'Z')
    return ''.join(out)
