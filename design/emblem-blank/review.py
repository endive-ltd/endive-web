import sys, json, time
sys.path.insert(0, '/home/user/endive-web/design/emblem-blank')
import concepts as C
from render import symbol, fit_layers
ids = sys.argv[2:] or None
todo = [('trinity', C.leaf_trinity, 0), ('spear', C.endive_spear, 0), ('bloom', C.crescent_bloom, 0), ('twin', C.twin_leaf_ribbon, 0),
        ('sprout', C.sprout_from_dark, 0), ('brush', lambda: C.brush_leaf()[0], 0), ('heart', C.heart_of_leaves, 0),
        ('pentafoil', C.pentafoil, 0), ('folded', C.folded_leaf, 0), ('head', C.golden_head, 0), ('braid', C.braided_spear, 0)]
syms = []; cells = []
for cid, fn, rot in todo:
    if ids and cid not in ids: continue
    t = time.time(); L = fit_layers(fn(), rot=rot); dt = time.time() - t
    for g in ('dark', 'light'):
        syms.append(symbol(f'{cid}-{g}', L, g))
        bg = '#0E1712' if g == 'dark' else '#F4F7F4'
        cells.append(f'<div style="position:relative;background:{bg};width:560px;height:560px"><b style="position:absolute;left:10px;top:8px;color:#888;font:14px sans-serif">{cid}</b><svg width="560" height="560" viewBox="-110 -110 220 220"><use href="#{cid}-{g}" x="-100" y="-100" width="200" height="200"/></svg></div>')
    print(cid, round(dt, 2), file=sys.stderr)
open(sys.argv[1], 'w').write('<html><body style="margin:0;display:flex;flex-wrap:wrap;width:1120px"><svg width="0" height="0" style="position:absolute"><defs>' + ''.join(syms) + '</defs></svg>' + ''.join(cells) + '</body></html>')
