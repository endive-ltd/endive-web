"""Endive minimal emblems, final set (round 9). One colour, circles and straight cuts only.
Usage: python3 final.py OUT_DIR  -> marks.json + svg/endive-mark-<id>.svg (+ -white)"""
import sys, os, json, math
import numpy as np
from shapely.geometry import Point, Polygon, box
from shapely.ops import unary_union
from shapely import affinity
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from marks import C, path_d, Q

G = 7.0   # the one hairline gap used everywhere

def lens_v(w, h):
    a, b = w / 2, h / 2
    R = (a * a + b * b) / (2 * a); d = R - a
    return C(-d, 0, R).intersection(C(d, 0, R)), [(-d, 0, R), (d, 0, R)]

def rot_cons(cons, ang, origin=(0, 0), dx=0, dy=0):
    t = math.radians(ang); ox, oy = origin; out = []
    for x, y, r in cons:
        x0, y0 = x - ox, y - oy
        out.append((ox + x0 * math.cos(t) - y0 * math.sin(t) + dx, oy + x0 * math.sin(t) + y0 * math.cos(t) + dy, r))
    return out

def kernel():
    disc = C(0, 0, 90)
    lf, cons = lens_v(64, 150)
    lf = affinity.rotate(lf, 32, origin=(0, 0)); cons = rot_cons(cons, 32)
    return unary_union([disc.difference(lf.buffer(G)), lf]), [(0, 0, 90)] + cons

def breakout():
    disc = C(0, 14, 78)
    lf, cons = lens_v(64, 176)
    lf = affinity.translate(affinity.rotate(lf, 28, origin=(0, 0)), 4, -10); cons = rot_cons(cons, 28, dx=4, dy=-10)
    return unary_union([disc.difference(lf.buffer(G)), lf]), [(0, 14, 78)] + cons

def twin():
    lf, cons = lens_v(70, 180)
    lf = affinity.translate(lf, 0, -90); cons = [(x, y - 90, r) for x, y, r in cons]
    A = affinity.rotate(lf, -24, origin=(0, 0)); B = affinity.rotate(lf, 24, origin=(0, 0))
    return A.symmetric_difference(B), rot_cons(cons, -24) + rot_cons(cons, 24)

def tile():
    a, r = 84, 40
    body = box(-a + r, -a + r, a - r, a - r).buffer(r, quad_segs=Q)
    shp = unary_union([body, box(0, -a, a, 0)])
    v = np.array([-1, 1]) / math.sqrt(2); n = np.array([1, 1]) / math.sqrt(2)
    p0 = np.array([a, -a]); L = 118
    pts = [p0 + v * L * t + n * (4.2 * math.sin(math.pi * t) ** 0.8) for t in np.linspace(0, 1, 80)]
    pts += [p0 + v * L * t - n * (4.2 * math.sin(math.pi * t) ** 0.8) for t in np.linspace(1, 0, 80)]
    return shp.difference(Polygon(pts).buffer(0)), [(-a + r, -a + r, r), (a - r, a - r, r), (-a + r, a - r, r)]

def layered():
    lf, cons = lens_v(92, 196)
    base = (0, 98)
    back = affinity.rotate(lf, -24, origin=base)
    shp = unary_union([lf, back.difference(lf.buffer(G))])
    return affinity.rotate(shp, 14, origin=(0, 0)), rot_cons(cons, 14) + rot_cons(rot_cons(cons, -24, origin=base), 14)

MARKS = [('twin', twin), ('kernel', kernel), ('tile', tile), ('breakout', breakout), ('layered', layered)]

def fit(shape, cons, half):
    x0, y0, x1, y1 = shape.bounds
    s = half / max((x1 - x0) / 2, (y1 - y0) / 2); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    shp = affinity.scale(affinity.translate(shape, -cx, -cy), s, s, origin=(0, 0))
    return shp, [((x - cx) * s, (y - cy) * s, r * s) for x, y, r in cons]

# optical sizes: round and square silhouettes look bigger than pointed ones
HALF = {'twin': 88, 'kernel': 82, 'tile': 80, 'breakout': 86, 'layered': 88}

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'build'
    os.makedirs(os.path.join(out, 'svg'), exist_ok=True)
    data = {}
    for cid, fn in MARKS:
        shp, cons = fit(*fn(), HALF[cid])
        d = path_d(shp, 0.02)
        data[cid] = dict(d=d, cons=[[round(v, 2) for v in c] for c in cons])
        for col, suf in (('#26734A', ''), ('#FFFFFF', '-white'), ('#101814', '-black'), ('#7DCAA1', '-mint')):
            open(os.path.join(out, 'svg', f'endive-mark-{cid}{suf}.svg'), 'w').write(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-100 -100 200 200"><path fill="{col}" fill-rule="evenodd" d="{d}"/></svg>\n')
        print(cid, len(d) // 1024, 'KB', file=sys.stderr)
    json.dump(data, open(os.path.join(out, 'marks.json'), 'w'))
