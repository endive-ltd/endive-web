"""Build every 'Blank Page' concept: symbols for the review page and standalone SVGs.
Usage: python3 generate.py OUT_DIR   (writes concepts.json + svg/<id>-<ground>.svg)"""
import sys, os, json, math
import numpy as np
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import concepts as C
from render import symbol, fit_layers
from engine import path_d

CONCEPTS = [
    ('trinity', C.leaf_trinity), ('head', C.golden_head), ('braid', C.braided_spear), ('bloom', C.crescent_bloom),
    ('sprout', C.sprout_from_dark), ('linked', C.heart_of_leaves), ('folded', C.folded_leaf), ('spear', C.endive_spear),
    ('brush', None), ('pentafoil', C.pentafoil),
]

def build(out):
    os.makedirs(os.path.join(out, 'svg'), exist_ok=True)
    data = {}
    for cid, fn in CONCEPTS:
        extra = {}
        if cid == 'brush':
            layers, st = C.brush_leaf()
            L = fit_layers(layers)
            cx, cy, s, _ = fit_layers.last
            P = (st.P - [cx, cy]) * s
            extra['centerline'] = 'M' + 'L'.join(f'{x:.1f} {y:.1f}' for x, y in P[::6])
        else:
            L = fit_layers(fn())
        rec = {}
        for g in ('light', 'dark'):
            sym = symbol(f'{cid}-{g}', L, g)
            rec[g] = sym
            svg = sym.replace(f'<symbol id="{cid}-{g}" viewBox="-100 -100 200 200">', '<svg xmlns="http://www.w3.org/2000/svg" viewBox="-100 -100 200 200">').replace('</symbol>', '</svg>')
            open(os.path.join(out, 'svg', f'endive-{cid}-{g}.svg'), 'w').write(svg + '\n')
        mono = symbol(f'{cid}-mono', L, 'light', mono='currentColor')
        rec['mono'] = mono
        rec.update(extra)
        data[cid] = rec
        print(cid, sum(len(v) for v in rec.values() if isinstance(v, str)) // 1024, 'KB', file=sys.stderr)
    json.dump(data, open(os.path.join(out, 'concepts.json'), 'w'))

if __name__ == '__main__':
    build(sys.argv[1] if len(sys.argv) > 1 else 'build')
