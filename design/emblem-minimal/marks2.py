"""Round 9b: more ownable geometry for a tech mark."""
import math
import numpy as np
from shapely.geometry import Point, Polygon, box, LineString
from shapely.ops import unary_union
from shapely import affinity
from marks import C, vesica, fit, path_d, Q

def lens_v(w, h):
    """Vertical lens (leaf) of width w and height h, centred at origin, from two circles."""
    # circle radius R through (0,+-h/2) and (+-w/2,0): centres at (-+(R-w/2),0)
    a = w / 2; b = h / 2
    R = (a * a + b * b) / (2 * a); d = R - a
    return C(-d, 0, R).intersection(C(d, 0, R)), [(-d, 0, R), (d, 0, R)]

def kernel():
    """A disc with a leaf inside it, separated by a hairline: light grown in the dark."""
    disc = C(0, 0, 90)
    lf, cons = lens_v(66, 150)
    lf = affinity.rotate(lf, 32, origin=(0, 0))
    g = 7
    return unary_union([disc.difference(lf.buffer(g)), lf]), [(0, 0, 90)] + cons

def kernel_open():
    """Same, but the leaf breaks out of the disc at the top: growth."""
    disc = C(0, 14, 78)
    lf, cons = lens_v(64, 176)
    lf = affinity.translate(affinity.rotate(lf, 28, origin=(0, 0)), 4, -10)
    g = 7
    return unary_union([disc.difference(lf.buffer(g)), lf]), cons

def layers():
    """Three nested pointed arches: an endive's layered head, and a stack."""
    shapes = []
    w = 17; g = 7
    outer, _ = lens_v(150, 250)
    outer = outer.intersection(box(-200, -200, 200, 40))
    out = []
    cur = outer
    for k in range(3):
        inner = cur.buffer(-w)
        ring = cur.difference(inner)
        out.append(ring)
        cur = inner.buffer(-g)
    out.append(cur)
    shp = unary_union(out).intersection(box(-200, -200, 200, 40))
    return shp, []

def xor_sprout():
    """Two leaves from one point; where they overlap the colour flips (XOR)."""
    lf, _ = lens_v(70, 180)
    lf = affinity.translate(lf, 0, -90)       # base at origin
    A = affinity.rotate(lf, -24, origin=(0, 0)); B = affinity.rotate(lf, 24, origin=(0, 0))
    return A.symmetric_difference(B), []

def quarter_bud():
    """Built from one module: the quarter-leaf (square with two opposite round corners)."""
    s = 80
    def qleaf(x, y, flip):
        sq = box(x, y, x + s, y + s)
        if not flip:
            c1 = C(x + s, y + s, s); c2 = C(x, y, s)
        else:
            c1 = C(x, y + s, s); c2 = C(x + s, y, s)
        return sq.intersection(c1).intersection(c2)
    g = 8
    L = qleaf(-s - g / 2, -s, False); R = qleaf(g / 2, -s, True)
    bottom = C(0, 0, s + g / 2).intersection(box(-200, g / 2, 200, 200)).difference(C(0, 0, s - 16 + g / 2))
    bottom = C(0, g / 2, s + g / 2).intersection(box(-200, g / 2, 200, 200))
    return unary_union([L, R, bottom]), []

def split_leaf():
    """One leaf, cut in two equal halves along its rib, the halves slightly offset."""
    lf, cons = lens_v(96, 190)
    g = 8
    Lh = lf.intersection(box(-200, -200, -g / 2, 200)); Rh = lf.intersection(box(g / 2, -200, 200, 200))
    Rh = affinity.translate(Rh, 0, -16)
    return affinity.rotate(unary_union([Lh, Rh]), 35, origin=(0, 0)), cons

def spear():
    """The endive head: a tall leaf, wrapped by two leaves cut from the same silhouette."""
    outer, _ = lens_v(120, 200)
    inner, _ = lens_v(54, 200)
    inner = affinity.translate(inner, 0, -6)
    g = 7
    sides = outer.difference(inner.buffer(g))
    sides = sides.difference(box(-g / 2, 0, g / 2, 200))
    shp = unary_union([sides, inner.intersection(outer)]).intersection(box(-200, -200, 200, 78))
    return shp, []

MARKS = [('kernel', 'Kernel', kernel), ('kernel2', 'Kernel, breaking out', kernel_open), ('layers', 'Layers', layers),
         ('xor', 'Overlap Sprout', xor_sprout), ('quarter', 'Quarter Bud', quarter_bud), ('split', 'Split Leaf', split_leaf),
         ('spear', 'Spear', spear)]

def superellipse(cx, cy, a, n=5, N=2000):
    t = np.linspace(0, 2 * np.pi, N, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    return Polygon(np.c_[cx + a * np.sign(c) * np.abs(c) ** (2 / n), cy + a * np.sign(s) * np.abs(s) ** (2 / n)])

def tile_leaf():
    """An app-tile squircle with one corner drawn out to a leaf tip."""
    a = 80
    sq = superellipse(0, 0, a, n=4.2)
    # leaf tip: the top-right quadrant becomes the lens corner formed by two circle arcs through the tip
    tip = (a * 1.12, -a * 1.12)
    # replace top-right quadrant by intersection of two big circles meeting at the tip
    R = 150
    c1 = C(tip[0] - R, tip[1] + 0, R)  # placeholder adjusted below
    # arcs tangent-ish to the squircle's top and right sides, meeting at the tip
    top_arc = C(tip[0] - R * 0.95, tip[1] + R * 0.32, R)
    right_arc = C(tip[0] - R * 0.32, tip[1] + R * 0.95, R)
    quad = box(0, -200, 200, 0)
    corner = top_arc.intersection(right_arc).intersection(quad)
    shp = unary_union([sq.difference(quad), corner, sq.intersection(quad).intersection(top_arc).intersection(right_arc)])
    shp = unary_union([sq.difference(quad), corner]).buffer(0)
    return shp, []

def tile_leaf_rib():
    shp, _ = tile_leaf()
    rib = LineString([(-30, 30), (86, -86)]).buffer(3.6, cap_style=2)
    taper = Polygon([(-34, 34), (90, -90), (-30, 40)])
    return shp.difference(rib), []

def wrap():
    """One leaf silhouette; a single arc cut shows a second leaf wrapped around the first."""
    lf, _ = lens_v(104, 196)
    R = 190
    # circle through the top tip (0,-98) and a point low on the left edge
    cx, cy = 150, 60
    r = math.hypot(cx - 0, cy + 98)
    arc = C(cx, cy, r)
    band_ = arc.buffer(4).difference(arc.buffer(-4))
    shp = lf.difference(band_)
    return affinity.rotate(shp, 22, origin=(0, 0)), []

def triad():
    """Three leaves from one point, overlaps flipped: a sprout, a crown of leaves."""
    lf, _ = lens_v(62, 176)
    lf = affinity.translate(lf, 0, -88)
    A = lf; B = affinity.rotate(lf, -38, origin=(0, 0)); Cc = affinity.rotate(lf, 38, origin=(0, 0))
    x = A.symmetric_difference(B).symmetric_difference(Cc)
    return x, []

MARKS += [('tile', 'Tile Leaf', tile_leaf), ('tilerib', 'Tile Leaf with rib', tile_leaf_rib), ('wrap', 'Wrap', wrap), ('triad', 'Triad', triad)]

def tile_leaf2():
    """App-tile shape with three soft corners and one sharp leaf tip; a tapering rib cut."""
    a, r = 84, 40
    body = box(-a + r, -a + r, a - r, a - r).buffer(r, quad_segs=Q)
    tip = box(0, -a, a, 0)
    shp = unary_union([body, tip])
    # outer corners on the two sides of the tip: soften the sharp corner by drawing the tip as a lens
    lensR = 2.2 * a
    lens = C(a - lensR, -a + lensR * 0.0 + 0, lensR)
    rib = Polygon([(a, -a), (-6, 12), (6, -6)]).buffer(0)
    rib = Polygon([(a + 2, -a - 2), (-10, 22), (-2, 2), (22, -10)]).buffer(0)
    # thin tapering wedge from the tip toward the centre
    v = np.array([-1, 1]) / math.sqrt(2); n = np.array([1, 1]) / math.sqrt(2)
    p0 = np.array([a, -a]); L = 118
    pts = [p0 + v * L * t + n * (4.2 * math.sin(math.pi * t) ** 0.8) for t in np.linspace(0, 1, 60)]
    pts += [p0 + v * L * t - n * (4.2 * math.sin(math.pi * t) ** 0.8) for t in np.linspace(1, 0, 60)]
    rib = Polygon(pts).buffer(0)
    return shp.difference(rib), []

def tile_leaf_plain():
    a, r = 84, 40
    body = box(-a + r, -a + r, a - r, a - r).buffer(r, quad_segs=Q)
    shp = unary_union([body, box(0, -a, a, 0)])
    return shp, []

def layered():
    """Two leaves, one in front of the other: the endive's layers in a single silhouette."""
    lf, _ = lens_v(92, 196)
    base = (0, 98)
    front = lf
    back = affinity.rotate(lf, -17, origin=base)
    g = 7
    shp = unary_union([front, back.difference(front.buffer(g))])
    return affinity.rotate(shp, 14, origin=(0, 0)), []

MARKS += [('tile2', 'Tile Leaf', tile_leaf2), ('tile3', 'Tile Leaf plain', tile_leaf_plain), ('layered', 'Layered', layered)]
