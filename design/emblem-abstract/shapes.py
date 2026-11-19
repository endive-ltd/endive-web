"""Round 10: abstract, original shapes. No leaves. One colour, even-weight bands,
real over/under where bands cross (engine from emblem-blank)."""
import sys, os, math
import numpy as np
from shapely.geometry import Point, Polygon, box, LineString
from shapely.ops import unary_union
from shapely import affinity
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'emblem-blank'))
from engine import Strand, weave, catmull
Q = 256

def circle_pts(cx, cy, r, n=1600, a0=0.0):
    t = a0 + np.linspace(0, 2 * np.pi, n, endpoint=False)
    return np.c_[cx + r * np.cos(t), cy + r * np.sin(t)]

def two_rings():
    """Two heavy rings, linked: one over, one under."""
    w = 22
    A = Strand(circle_pts(-24, 0, 54), w, closed=True); B = Strand(circle_pts(24, 0, 54), w, closed=True)
    res = weave([A, B], gap=6, round_r=0)
    return affinity.rotate(unary_union(res['per_strand']), -35, origin=(0, 0))

def split_ring():
    """A ring cut in half, the halves sliding past each other: a fair split."""
    ring = Point(0, 0).buffer(90, quad_segs=Q).difference(Point(0, 0).buffer(50, quad_segs=Q))
    g = 8
    top = ring.intersection(box(-200, -200, 200, -g / 2)); bot = ring.intersection(box(-200, g / 2, 200, 200))
    return unary_union([affinity.translate(top, -16, 0), affinity.translate(bot, 16, 0)])

def trefoil():
    """One continuous band tied as a trefoil knot, bold and even."""
    t = np.linspace(0, 2 * np.pi, 3000, endpoint=False)
    x = np.sin(t) + 2 * np.sin(2 * t); y = np.cos(t) - 2 * np.cos(2 * t)
    st = Strand(np.c_[x, y] * 30, 20, closed=True)
    res = weave([st], gap=6, round_r=0)
    return affinity.rotate(res['per_strand'][0], 180, origin=(0, 0))

def linked_cs():
    """Two open C-shapes hooked through each other: two parties, one connection."""
    w = 24
    def arc(cx, a0, a1):
        t = np.linspace(math.radians(a0), math.radians(a1), 1200)
        return np.c_[cx + 52 * np.cos(t), 52 * np.sin(t)]
    A = Strand(arc(-26, 35, 325), w); B = Strand(arc(26, 215, 505), w)
    res = weave([A, B], gap=6, round_r=0)
    shp = unary_union(res['per_strand'])
    return affinity.rotate(shp, -20, origin=(0, 0))

def folded_square():
    """A wide band runs round a square and overlaps itself at one corner, like a folded ribbon."""
    w = 26
    P = np.array([(-60, 70), (-60, -40), (-60, -60), (-40, -60), (60, -60), (60, 60), (-80, 60)], float)
    # rounded square path with overlapping ends
    pts = []
    def seg(a, b, n=200):
        a, b = np.array(a, float), np.array(b, float)
        return [a + (b - a) * t for t in np.linspace(0, 1, n, endpoint=False)]
    def corner(c, r, a0, a1, n=120):
        return [np.array(c) + r * np.array([math.cos(math.radians(a)), math.sin(math.radians(a))]) for a in np.linspace(a0, a1, n, endpoint=False)]
    r = 30
    pts += seg((-62, 92), (-62, -32))
    pts += corner((-32, -32), 30, 180, 270)
    pts += seg((-32, -62), (32, -62))
    pts += corner((32, -32), 30, 270, 360)
    pts += seg((62, -32), (62, 32))
    pts += corner((32, 32), 30, 0, 90)
    pts += seg((32, 62), (-92, 62))
    st = Strand(np.array(pts), w)
    res = weave([st], gap=6, round_r=0)
    sh = res['per_strand'][0].intersection(box(-200, -200, 200, 200))
    return sh

def spiral():
    """A band that winds into itself on quarter circles in the golden ratio."""
    phi = (1 + 5 ** 0.5) / 2
    pts = []; c = np.array([0.0, 0.0]); r = 90; ang = 180
    centers = []
    x, y = 0.0, 0.0
    # golden spiral from quarter arcs: shrink radius by phi each quarter
    cur = np.array([-90.0, 0.0]); a = 180
    cen = np.array([0.0, 0.0])
    for k in range(5):
        t = np.radians(np.linspace(a, a + 90, 200, endpoint=False))
        pts.append(np.c_[cen[0] + r * np.cos(t), cen[1] + r * np.sin(t)])
        end = cen + r * np.array([math.cos(math.radians(a + 90)), math.sin(math.radians(a + 90))])
        r2 = r / phi
        d = np.array([math.cos(math.radians(a + 90)), math.sin(math.radians(a + 90))])
        cen = end - d * r2
        r = r2; a += 90
    P = np.vstack(pts)
    st = Strand(P, lambda u: 26 * (1 - 0.55 * u))
    res = weave([st], gap=6, round_r=0)
    return res['per_strand'][0]

SHAPES = [('rings', 'Two Rings', two_rings), ('split', 'Split Ring', split_ring), ('trefoil', 'Trefoil', trefoil),
          ('hooks', 'Hooked Cs', linked_cs), ('fold', 'Folded Square', folded_square), ('spiral', 'Golden Spiral', spiral)]

def two_rings_v2():
    w = 24
    A = Strand(circle_pts(-34, 0, 56), w, closed=True); B = Strand(circle_pts(34, 0, 56), w, closed=True)
    res = weave([A, B], gap=7, round_r=0)
    return affinity.rotate(unary_union(res['per_strand']), -30, origin=(0, 0))

def squircle_pts(cx, cy, a, n=4.0, N=2000):
    t = np.linspace(0, 2 * np.pi, N, endpoint=False)
    c, s = np.cos(t), np.sin(t)
    return np.c_[cx + a * np.sign(c) * np.abs(c) ** (2 / n), cy + a * np.sign(s) * np.abs(s) ** (2 / n)]

def two_tiles():
    """Two app-tile frames linked through each other."""
    w = 22
    A = Strand(squircle_pts(-26, -26, 52), w, closed=True); B = Strand(squircle_pts(26, 26, 52), w, closed=True)
    res = weave([A, B], gap=7, round_r=0)
    return unary_union(res['per_strand'])

def hooks_v2():
    """Two open rings, each hooked through the other's gap."""
    w = 24; r = 50
    def arc(cx, a0, a1):
        t = np.linspace(math.radians(a0), math.radians(a1), 1200)
        return np.c_[cx + r * np.cos(t), r * np.sin(t)]
    A = Strand(arc(-30, 60, 330), w); B = Strand(arc(30, 240, 510), w)
    res = weave([A, B], gap=7, round_r=0)
    return affinity.rotate(unary_union(res['per_strand']), -25, origin=(0, 0))

def pivot():
    """Two half-rings turning around one point: an S of balance, a turn of motion."""
    ro, ri = 52, 24
    def half(cx, top):
        ring = Point(cx, 0).buffer(ro, quad_segs=Q).difference(Point(cx, 0).buffer(ri, quad_segs=Q))
        return ring.intersection(box(-300, -300, 300, 0) if top else box(-300, 0, 300, 300))
    g = 7
    A = half(-ro + (ro - ri) / 2 - 0, True)
    A = half(-(ro + ri) / 2, True); B = half((ro + ri) / 2, False)
    A = affinity.translate(A, -g / 2, -g / 2); B = affinity.translate(B, g / 2, g / 2)
    return affinity.rotate(unary_union([A, B]), -30, origin=(0, 0))

def split_ring_v2():
    ring = Point(0, 0).buffer(90, quad_segs=Q).difference(Point(0, 0).buffer(46, quad_segs=Q))
    g = 9
    top = ring.intersection(box(-200, -200, 200, -g / 2)); bot = ring.intersection(box(-200, g / 2, 200, 200))
    return affinity.rotate(unary_union([affinity.translate(top, -22, 0), affinity.translate(bot, 22, 0)]), -20, origin=(0, 0))

SHAPES[:] = [('split', 'Split Ring', split_ring_v2), ('pivot', 'Pivot', pivot), ('tiles', 'Linked Tiles', two_tiles),
             ('rings', 'Two Rings', two_rings_v2), ('hooks', 'Hooked Rings', hooks_v2), ('trefoil', 'Trefoil', trefoil)]
