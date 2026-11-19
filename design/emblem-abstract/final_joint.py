"""Round 11 final: 'The Joint' family. Usage: python3 final_joint.py OUT_DIR"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'emblem-minimal'))
from joint import disc_v, tile_v, pill_v, disc_shift
from marks import path_d
from shapely import affinity

MARKS = [('joint', disc_v, 86), ('jtile', tile_v, 80), ('jpill', pill_v, 88), ('jshift', disc_shift, 86)]
# centre line of the cut (pre-fit units): x = 0 with one dovetail
CUT = [(0, -200), (0, -10), (40, -29), (40, 29), (0, 10), (0, 200)]

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'build'
    os.makedirs(os.path.join(out, 'svg'), exist_ok=True)
    data = {}
    for cid, fn, half in MARKS:
        shp = fn()
        x0, y0, x1, y1 = shp.bounds
        s = half / max((x1 - x0) / 2, (y1 - y0) / 2); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        shp = affinity.scale(affinity.translate(shp, -cx, -cy), s, s, origin=(0, 0))
        d = path_d(shp, 0.02)
        cut = ' '.join(f'{(x - cx) * s:.2f},{max(-100, min(100, (y - cy) * s)):.2f}' for x, y in CUT)
        data[cid] = dict(d=d, cut=cut)
        for col, suf in (('#26734A', ''), ('#FFFFFF', '-white'), ('#101814', '-black'), ('#7DCAA1', '-mint')):
            open(os.path.join(out, 'svg', f'endive-mark-{cid}{suf}.svg'), 'w').write(
                f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-100 -100 200 200"><path fill="{col}" fill-rule="evenodd" d="{d}"/></svg>\n')
    json.dump(data, open(os.path.join(out, 'marks.json'), 'w'))
