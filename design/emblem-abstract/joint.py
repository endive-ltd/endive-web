"""Round 11: 'The Joint'. A shape split by a cut that carries a dovetail key, so the two
parts are locked together: a fix, and two sides joined. One colour, one gap width."""
import sys, os, math
import numpy as np
from shapely.geometry import Point, Polygon, box, LineString
from shapely.ops import unary_union
from shapely import affinity
Q = 256
G = 8.0

def C(x, y, r): return Point(x, y).buffer(r, quad_segs=Q)
def squircle(a, n=4.4, N=2400):
    t = np.linspace(0, 2 * np.pi, N, endpoint=False); c, s = np.cos(t), np.sin(t)
    return Polygon(np.c_[a * np.sign(c) * np.abs(c) ** (2 / n), a * np.sign(s) * np.abs(s) ** (2 / n)])

def cut_path(keys, H=140, neck=26, flare=46, depth=34, r=4):
    """Vertical cut line x=0 with dovetail keys. keys: list of (y_centre, direction +1 right / -1 left).
    Returns the left region (a polygon) bounded by the cut; corners lightly rounded."""
    pts = [(-300, -H * 2), (0, -H * 2)]
    for yc, d in sorted(keys):
        pts += [(0, yc - neck / 2), (d * depth, yc - flare / 2), (d * depth, yc + flare / 2), (0, yc + neck / 2)]
    pts += [(0, H * 2), (-300, H * 2)]
    left = Polygon(pts).buffer(0)
    return left.buffer(r, join_style=1).buffer(-2 * r, join_style=1).buffer(r, join_style=1)

def joint(base, keys, rot=0, **kw):
    left = cut_path(keys, **kw)
    gapband = left.buffer(G / 2, join_style=1).difference(left.buffer(-G / 2, join_style=1))
    shp = base.difference(gapband)
    return affinity.rotate(shp, rot, origin=(0, 0))

def disc_one():   return joint(C(0, 0, 90), [(0, 1)], rot=-28)
def disc_two():   return joint(C(0, 0, 90), [(-30, 1), (30, -1)], rot=-28, neck=22, flare=38, depth=30)
def tile_one():   return joint(squircle(86), [(0, 1)], rot=0)
def tile_two():   return joint(squircle(86), [(-32, 1), (32, -1)], rot=0, neck=22, flare=38, depth=30)
def disc_offset():return joint(C(0, 0, 90), [(14, 1)], rot=-28, neck=30, flare=54, depth=40)
def pill():
    base = Point(0, 0).buffer(56, quad_segs=Q)
    base = unary_union([base, affinity.translate(base, 0, 60), box(-56, 0, 56, 60)])
    base = affinity.translate(base, 0, -30)
    return joint(affinity.rotate(base, 90, origin=(0, 0)), [(0, 1)], rot=-28)

JOINTS = [('disc1', 'Joint, one key', disc_one), ('disc2', 'Joint, two keys', disc_two), ('tile1', 'Tile joint', tile_one),
          ('tile2', 'Tile joint, two keys', tile_two), ('discoff', 'Joint, offset key', disc_offset), ('pill', 'Pill joint', pill)]

def disc_v():  return joint(C(0, 0, 90), [(0, 1)], rot=0, neck=20, flare=58, depth=40, r=3)
def tile_v():  return joint(squircle(84), [(0, 1)], rot=0, neck=20, flare=58, depth=40, r=3)
def pill_v():
    base = unary_union([C(0, -34, 56), C(0, 34, 56), box(-56, -34, 56, 34)])
    return joint(affinity.rotate(base, 90, origin=(0, 0)), [(0, 1)], rot=0, neck=20, flare=58, depth=40, r=3)
def disc_shift():
    """The right half sits a step lower: the two parts slid into place."""
    left = cut_path([(0, 1)], neck=20, flare=58, depth=40, r=3)
    band = left.buffer(G / 2, join_style=1).difference(left.buffer(-G / 2, join_style=1))
    d = C(0, 0, 90).difference(band)
    parts = sorted(getattr(d, 'geoms', [d]), key=lambda p: p.centroid.x)
    return unary_union([parts[0], affinity.translate(parts[1], 0, 14)])
def tile_wide():
    base = Polygon(squircle(84).exterior.coords)
    base = affinity.scale(base, 1.18, 0.9)
    return joint(base, [(0, 1)], rot=0, neck=20, flare=58, depth=40, r=3)
JOINTS[:] = [('discv', 'Joint disc', disc_v), ('tilev', 'Joint tile', tile_v), ('pillv', 'Joint pill', pill_v),
             ('shift', 'Joint disc, shifted', disc_shift), ('wide', 'Joint tile, wide', tile_wide)]
