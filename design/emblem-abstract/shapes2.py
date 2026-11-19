"""Round 11: less archetypal constructions. Each mark combines two or three specific moves,
so it does not collapse into a single stock symbol (ring, link, knot, arrow, pie)."""
import sys, os, math
import numpy as np
from shapely.geometry import Point, Polygon, box, LineString
from shapely.ops import unary_union
from shapely import affinity
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'emblem-blank'))
from engine import Strand, weave
Q = 256
PHI = (1 + 5 ** 0.5) / 2
def C(x, y, r): return Point(x, y).buffer(r, quad_segs=Q)
def squircle(cx, cy, a, n=4.5, N=2400):
    t = np.linspace(0, 2 * np.pi, N, endpoint=False); c, s = np.cos(t), np.sin(t)
    return Polygon(np.c_[cx + a * np.sign(c) * np.abs(c) ** (2 / n), cy + a * np.sign(s) * np.abs(s) ** (2 / n)])
G = 8

def lune_pair():
    """Two crescents of unequal weight, nested head-to-tail with one even gap."""
    big = C(0, 0, 90).difference(C(22, -14, 72))
    small = C(18, -10, 58).difference(C(-4, 6, 44))
    small = small.difference(big.buffer(G))
    return unary_union([big, small])

def stepped_arcs():
    """Three quarter-bands, each a golden step larger, climbing outward."""
    parts = []
    r = 26; w = 22; cx, cy = 0, 0
    a0 = 180
    for k in range(3):
        ring = C(cx, cy, r + w).difference(C(cx, cy, r))
        t = np.radians(np.linspace(a0, a0 + 90, 200))
        wedge = Polygon([(cx, cy)] + [(cx + 400 * math.cos(a), cy + 400 * math.sin(a)) for a in t])
        parts.append(ring.intersection(wedge))
        # next arc starts where this one ends, one gap further out
        a0 += 90
        r = (r + w) * PHI ** 0.5 + 0; w = w * 1.18
    shp = unary_union([p for p in parts])
    return shp

def hinge():
    """A tile cut by one arc; the thin outer piece swings open on a hinge."""
    tile = squircle(0, 0, 84)
    arc_c = C(-70, 70, 150)
    inner = tile.intersection(arc_c)
    lid = tile.difference(arc_c.buffer(G))
    lid = affinity.rotate(lid, -11, origin=(84, -84 + 160))
    pivot = (-84 + 4, -84 + 4)
    lid = affinity.rotate(tile.difference(arc_c.buffer(G)), -12, origin=(84 * 0.98, 70))
    return unary_union([inner, lid])

def pebbles():
    """Three touching circles in golden sizes, fused into one smooth body, then split by one hairline."""
    r1 = 40; r2 = r1 / PHI; r3 = r2 / PHI
    c1 = np.array([-18.0, 22.0]); c2 = c1 + np.array([math.cos(math.radians(-50)), math.sin(math.radians(-50))]) * (r1 + r2 - 6)
    c3 = c2 + np.array([math.cos(math.radians(-10)), math.sin(math.radians(-10))]) * (r2 + r3 - 4)
    body = unary_union([C(*c1, r1), C(*c2, r2), C(*c3, r3)])
    body = body.buffer(10, quad_segs=Q).buffer(-10, quad_segs=Q)
    return body

def twisted_pair():
    """Two bands that swap sides once, the way a twisted-pair cable carries a signal."""
    y = np.linspace(-92, 92, 1600)
    s = np.clip((y + 40) / 80, 0, 1); s = s * s * (3 - 2 * s)
    xa = -36 + 72 * s; xb = 36 - 72 * s
    A = Strand(np.c_[xa, y], 30); B = Strand(np.c_[xb, y], 30)
    res = weave([A, B], gap=G, round_r=0)
    shp = unary_union(res['per_strand'])
    # round the four ends
    shp = shp.buffer(-6, quad_segs=Q).buffer(6, quad_segs=Q)
    return affinity.rotate(shp, -18, origin=(0, 0))

def bridge():
    """A tile and a disc joined by a single narrow bridge: two parties, one connection."""
    t = squircle(-30, 22, 54)
    d = C(42, -34, 40)
    link = LineString([(-30, 22), (42, -34)]).buffer(8, cap_style=2)
    sh = unary_union([t, d, link])
    sh = sh.buffer(6, quad_segs=Q).buffer(-6, quad_segs=Q)
    return sh

def offset_frame():
    """A thick squircle frame whose window is a circle pushed off-centre until it nearly breaks through."""
    f = squircle(0, 0, 86).difference(C(18, -18, 46))
    notch = Polygon([(40, -40), (120, -120), (120, -60), (60, -20)])
    return f

SHAPES2 = [('lunes', 'Lune Pair', lune_pair), ('steps', 'Stepped Arcs', stepped_arcs), ('hinge', 'Hinge', hinge),
           ('pebbles', 'Pebbles', pebbles), ('pair', 'Twisted Pair', twisted_pair), ('bridge', 'Bridge', bridge), ('frame', 'Offset Window', offset_frame)]
