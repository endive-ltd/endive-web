"""Round 10 final: four abstract one-colour marks. Usage: python3 final.py OUT_DIR"""
import sys, os, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'emblem-minimal'))
from shapes import split_ring_v2, two_tiles, two_rings_v2, trefoil
from marks import path_d
from shapely import affinity

MARKS = [('split', split_ring_v2, 86), ('tiles', two_tiles, 82), ('rings', two_rings_v2, 86), ('trefoil', trefoil, 88)]

def rot(x, y, deg):
    t = math.radians(deg); return x * math.cos(t) - y * math.sin(t), x * math.sin(t) + y * math.cos(t)

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'build'
    os.makedirs(os.path.join(out, 'svg'), exist_ok=True)
    data = {}
    for cid, fn, half in MARKS:
        shp = fn()
        x0, y0, x1, y1 = shp.bounds
        s = half / max((x1 - x0) / 2, (y1 - y0) / 2); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        shp = affinity.scale(affinity.translate(shp, -cx, -cy), s, s, origin=(0, 0))
        cons = []
        if cid == 'split':
            for dx in (-22, 22):
                px, py = rot(dx, 0, -20)
                for r in (90, 46): cons.append([round((px - cx) * s, 2), round((py - cy) * s, 2), round(r * s, 2)])
        d = path_d(shp, 0.02)
        data[cid] = dict(d=d, cons=cons)
        for col, suf in (('#26734A', ''), ('#FFFFFF', '-white'), ('#101814', '-black'), ('#7DCAA1', '-mint')):
            open(os.path.join(out, 'svg', f'endive-mark-{cid}{suf}.svg'), 'w').write(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-100 -100 200 200"><path fill="{col}" fill-rule="evenodd" d="{d}"/></svg>\n')
    json.dump(data, open(os.path.join(out, 'marks.json'), 'w'))
