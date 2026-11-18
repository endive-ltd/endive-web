"""Endive E-D rings: parametric generator.

Two closed bands (a vertical "E" ring and a horizontal "D" ring) are built from
rounded-polygon centre lines, buffered to a band, optionally grooved (two thin
white lines, like reference N1), and woven: at every crossing one ring is cut
with a clean gap where it passes under the other. Over/under alternates along
the E ring, and the linking number is checked so the two rings really interlock.

Usage:  python3 generate.py OUT_DIR      (writes variants.json + one SVG per cut)
Needs:  pip install shapely numpy
"""
import json, math, sys, os
import numpy as np
from shapely.geometry import LineString, LinearRing, Point, Polygon, MultiPolygon
from shapely.ops import unary_union
from shapely import affinity

VB = 96.0          # half-extent the mark is fitted into (viewBox is -100..100)

# ---------- centre lines -------------------------------------------------
def rounded_poly(verts, n_arc=48):
    """verts: list of (x, y, r). Closed polygon with circular fillets."""
    pts = []
    N = len(verts)
    for i in range(N):
        px, py, _ = verts[i - 1]
        vx, vy, r = verts[i]
        nx, ny, _ = verts[(i + 1) % N]
        d1 = np.array([px - vx, py - vy], float); l1 = np.linalg.norm(d1); d1 /= l1
        d2 = np.array([nx - vx, ny - vy], float); l2 = np.linalg.norm(d2); d2 /= l2
        if r <= 0:
            pts.append((vx, vy)); continue
        th = math.acos(max(-1, min(1, float(d1 @ d2))))
        t = r / math.tan(th / 2)
        t = min(t, l1 / 2 - 1e-6 if verts[i - 1][2] > 0 else l1 - 1e-6,
                   l2 / 2 - 1e-6 if verts[(i + 1) % N][2] > 0 else l2 - 1e-6)
        r_eff = t * math.tan(th / 2)
        a = np.array([vx, vy]) + d1 * t
        b = np.array([vx, vy]) + d2 * t
        bis = d1 + d2; bis /= np.linalg.norm(bis)
        c = np.array([vx, vy]) + bis * (r_eff / math.sin(th / 2))
        a0 = math.atan2(a[1] - c[1], a[0] - c[0])
        a1 = math.atan2(b[1] - c[1], b[0] - c[0])
        da = (a1 - a0 + math.pi) % (2 * math.pi) - math.pi
        for k in range(n_arc + 1):
            ang = a0 + da * k / n_arc
            pts.append((c[0] + r_eff * math.cos(ang), c[1] + r_eff * math.sin(ang)))
    # dedupe
    out = [pts[0]]
    for p in pts[1:]:
        if math.hypot(p[0] - out[-1][0], p[1] - out[-1][1]) > 1e-4:
            out.append(p)
    return LinearRing(out)

def rect(x0, y0, x1, y1, rTL, rTR, rBR, rBL):
    return [(x0, y0, rTL), (x1, y0, rTR), (x1, y1, rBR), (x0, y1, rBL)]

def d_ring(x0, y0, x1, y1, r_left=6, bowl=1.0):
    """Horizontal D: flat left side, right end a bowl (bowl=1 -> full half-circle)."""
    h = y1 - y0
    rr = min(bowl * h / 2, h / 2 - 0.01)
    return rect(x0, y0, x1, y1, r_left, rr, rr, r_left)

def e_stepped(x0, y0, x1, y1, step_x, arm_h, r_out=5, r_in=4, r_left=4):
    """Vertical E: right wall recessed to step_x between the arms (arms of height arm_h)."""
    return [(x0, y0, r_left), (x1, y0, r_out), (x1, y0 + arm_h, r_in), (step_x, y0 + arm_h, r_in),
            (step_x, y1 - arm_h, r_in), (x1, y1 - arm_h, r_in), (x1, y1, r_out), (x0, y1, r_left)]

def e_tongue(x0, y0, x1, y1, step_x, arm_h, tongue_x, tongue_h, r_out=5, r_in=4, r_left=4):
    """Vertical E with recessed wall AND a short middle tongue poking right."""
    ym = (y0 + y1) / 2
    return [(x0, y0, r_left), (x1, y0, r_out), (x1, y0 + arm_h, r_in), (step_x, y0 + arm_h, r_in),
            (step_x, ym - tongue_h / 2, r_in), (tongue_x, ym - tongue_h / 2, r_in),
            (tongue_x, ym + tongue_h / 2, r_in), (step_x, ym + tongue_h / 2, r_in),
            (step_x, y1 - arm_h, r_in), (x1, y1 - arm_h, r_in), (x1, y1, r_out), (x0, y1, r_left)]

# ---------- weaving ------------------------------------------------------
def tangent_at(ring, pt, eps=0.05):
    s = ring.project(pt); L = ring.length
    a = ring.interpolate((s - eps) % L); b = ring.interpolate((s + eps) % L)
    v = np.array([b.x - a.x, b.y - a.y]); return v / np.linalg.norm(v)

def crossings(A, B):
    inter = A.intersection(B)
    pts = [g for g in getattr(inter, 'geoms', [inter]) if g.geom_type == 'Point']
    pts.sort(key=lambda p: A.project(p))
    return pts

def build(E_cl, D_cl, wE, wD, gap, grooved, groove_w, groove_inset, start_over='E', fit=True):
    # fit both centre lines into the box (band half-width included), centred on bbox
    if fit:
        both = unary_union([Polygon(E_cl).buffer(wE / 2), Polygon(D_cl).buffer(wD / 2)])
        x0, y0, x1, y1 = both.bounds
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        # scale centre lines so that outer bounds fit +-VB (approx; band widths stay fixed)
        half = max(x1 - x0, y1 - y0) / 2
        wmax = max(wE, wD) / 2
        s = (VB - wmax) / (half - wmax)
        E_cl = affinity.scale(affinity.translate(E_cl, -cx, -cy), s, s, origin=(0, 0))
        D_cl = affinity.scale(affinity.translate(D_cl, -cx, -cy), s, s, origin=(0, 0))
    FE = E_cl.buffer(wE / 2, quad_segs=24)
    FD = D_cl.buffer(wD / 2, quad_segs=24)
    pts = crossings(E_cl, D_cl)
    over = []
    for i, p in enumerate(pts):
        e_over = (i % 2 == 0) == (start_over == 'E')
        over.append('E' if e_over else 'D')
    # linking number check
    lk = 0
    for p, o in zip(pts, over):
        tE = tangent_at(E_cl, p); tD = tangent_at(D_cl, p)
        to, tu = (tE, tD) if o == 'E' else (tD, tE)
        lk += np.sign(to[0] * tu[1] - to[1] * tu[0])
    lk /= 2

    def band(cl, w, F):
        g = F
        if grooved:
            off = w / 2 - groove_inset
            grooves = cl.buffer(off + groove_w / 2, quad_segs=24).difference(cl.buffer(off - groove_w / 2, quad_segs=24))
            g = g.difference(grooves)
        return g
    Ev = band(E_cl, wE, FE); Dv = band(D_cl, wD, FD)
    FEg = FE.buffer(gap, quad_segs=24); FDg = FD.buffer(gap, quad_segs=24)
    xE = FDg.intersection(FE); xD = FEg.intersection(FD)
    for p, o in zip(pts, over):
        if o == 'E':   # D passes under E here: cut D
            comps = [c for c in getattr(xD, 'geoms', [xD]) if c.distance(p) < 1e-6]
            for c in comps: Dv = Dv.difference(c.buffer(0.01))
        else:
            comps = [c for c in getattr(xE, 'geoms', [xE]) if c.distance(p) < 1e-6]
            for c in comps: Ev = Ev.difference(c.buffer(0.01))
    shape = unary_union([Ev, Dv])
    # sliver report: parts thinner than ~0.9 units, or tiny islands
    opened = shape.buffer(-0.45).buffer(0.45)
    sliver = shape.difference(opened).area
    polys = list(getattr(shape, 'geoms', [shape]))
    tiny = [round(p.area, 2) for p in polys if p.area < 6]
    return shape, dict(crossings=len(pts), over=over, link=float(lk), sliver_area=round(sliver, 2), tiny=tiny,
                       bounds=[round(v, 1) for v in shape.bounds])

def to_path(geom, tol=0.02):
    geom = geom.simplify(tol, preserve_topology=True)
    out = []
    for p in getattr(geom, 'geoms', [geom]):
        for ring in [p.exterior] + list(p.interiors):
            c = list(ring.coords)[:-1]
            out.append('M' + 'L'.join(f'{x:.2f} {y:.2f}' for x, y in c) + 'Z')
    return ''.join(out)

# ---------- cuts ---------------------------------------------------------
GROOVED = dict(w=14.0, gap=2.2, groove_w=1.5, groove_inset=3.9)
SOLID = dict(w=21.0, gap=2.6)

def render(spec):
    """spec: dict with 'E' and 'D' -> functions(w) returning vertex lists, plus options."""
    res = {}
    for cut in ('grooved', 'solid'):
        P = GROOVED if cut == 'grooved' else SOLID
        kE = spec.get('wE', 1.0); kD = spec.get('wD', 1.0)
        wE = P['w'] * kE; wD = P['w'] * kD
        E_cl = rounded_poly(spec['E'](cut)); D_cl = rounded_poly(spec['D'](cut))
        shape, info = build(E_cl, D_cl, wE, wD, P['gap'], cut == 'grooved',
                            GROOVED['groove_w'] * min(kE, kD), GROOVED['groove_inset'] * min(kE, kD),
                            spec.get('start', 'E'))
        res[cut] = dict(d=to_path(shape), info=info)
    return res

# ---------- variants -----------------------------------------------------
# Coordinates: x right, y down. Sizes are pre-fit; build() scales to the box.
V = []
def add(id, name, family, note, E, D, **kw):
    V.append(dict(id=id, name=name, family=family, note=note, E=E, D=D, **kw))

# Family A: N1 layout (upright ring through flat ring, 4 crossings), shapes nudged.
add('A1', 'Gentle nod', 'Cross',
    'Closest to N1: the upright ring gets a flat left side and squarer left corners; the flat ring gets a flat left end and a fully round right end.',
    lambda c: rect(-30, -90, 30, 90, 7, 26, 26, 7),
    lambda c: d_ring(-90, -30, 90, 30, r_left=7, bowl=1.0))
add('A2', 'Square E, round D', 'Cross',
    'Same layout as N1, but the upright ring is almost square at every corner (more E) and the flat ring has one square end, one round end (D).',
    lambda c: rect(-32, -90, 32, 90, 7, 12, 12, 7),
    lambda c: d_ring(-90, -32, 90, 32, r_left=7, bowl=1.0))
add('A3', 'D slides right', 'Cross',
    'As A2, with the D slid to the right so its round end sticks out further. Reads E first, then D.',
    lambda c: rect(-50, -90, 12, 90, 6, 10, 10, 6),
    lambda c: d_ring(-82, -30, 96, 30, r_left=6, bowl=1.0))
add('A4', 'Flatter D curve', 'Cross',
    'As A3, but the D’s round end is a gentler curve rather than a full half-circle: calmer, closer to N1.',
    lambda c: rect(-50, -90, 12, 90, 6, 12, 12, 6),
    lambda c: d_ring(-82, -30, 96, 30, r_left=6, bowl=0.7))

# Family B: threaded (the D's flat end sits inside the E, like two chain links; 2 crossings).
add('B1', 'Chain link', 'Threaded',
    'The D hooks through the E like two links of a chain: square-ish E on the left, D bowl out to the right. Only two crossings, so very clean.',
    lambda c: rect(-90, -90, -14, 90, 6, 8, 8, 6),
    lambda c: d_ring(-62, -36, 92, 36, r_left=6, bowl=1.0))
add('B2', 'Chain link, E arms', 'Threaded',
    'As B1, but the E’s right side steps in, so its top and bottom reach out like the arms of an E and the D fills the middle.',
    lambda c: e_stepped(-90, -90, 24, 90, -16, 30, r_out=8, r_in=10, r_left=6),
    lambda c: d_ring(-60, -28, 92, 28, r_left=6, bowl=1.0))
add('B3', 'Chain link, compact', 'Threaded',
    'B2 made squarer: shorter D, less overhang, so the whole mark sits closer to a square.',
    lambda c: e_stepped(-90, -90, 14, 90, -20, 30, r_out=8, r_in=10, r_left=6),
    lambda c: d_ring(-62, -28, 70, 28, r_left=6, bowl=1.0))
add('B4', 'Chain link, soft', 'Threaded',
    'B2 with softer corners all round: friendlier and closer to N1’s rounded feel.',
    lambda c: e_stepped(-90, -90, 24, 90, -16, 30, r_out=16, r_in=8, r_left=16),
    lambda c: d_ring(-60, -28, 92, 28, r_left=14, bowl=1.0))
add('B5', 'Chain link, heavy E', 'Threaded',
    'B2 with the E band a little heavier than the D, so the E leads and the D follows.',
    lambda c: e_stepped(-90, -90, 24, 90, -16, 30, r_out=8, r_in=10, r_left=6),
    lambda c: d_ring(-60, -28, 92, 28, r_left=6, bowl=1.0), wE=1.15, wD=0.85)
add('B6', 'Chain link, tall D', 'Threaded',
    'B1 with a taller, rounder D: the D gets equal billing with the E.',
    lambda c: rect(-90, -90, -4, 90, 6, 8, 8, 6),
    lambda c: d_ring(-58, -46, 92, 46, r_left=6, bowl=1.0))
add('B7', 'Chain link, swapped weave', 'Threaded',
    'B2 with the over/under swapped, to compare which crossing should sit on top.',
    lambda c: e_stepped(-90, -90, 24, 90, -16, 30, r_out=8, r_in=10, r_left=6),
    lambda c: d_ring(-60, -28, 92, 28, r_left=6, bowl=1.0), start='D')

# Family C: literal E (the E ring has a short middle arm that pokes into the D).
def C_E(x1, step, tongue, arm=30, ro=6, ri=4, rl=5):
    return lambda c: e_tongue(-90, -90, x1, 90, step, arm, tongue, 4, r_out=ro, r_in=ri, r_left=rl)
add('C1', 'E with middle arm', 'Literal',
    'The E ring traces a real E: top arm, short middle arm, bottom arm. The middle arm pokes into the D’s hole.',
    C_E(24, -22, 10, ro=8, ri=5, rl=6), lambda c: d_ring(-66, -42, 92, 42, r_left=6, bowl=1.0))
add('C2', 'E with middle arm, compact', 'Literal',
    'C1 made squarer: the D overhangs less, so the mark sits closer to a square.',
    C_E(14, -26, 4), lambda c: d_ring(-64, -34, 70, 34, r_left=6, bowl=1.0))
add('C3', 'E with middle arm, soft', 'Literal',
    'C1 with rounder corners: the most friendly of the literal set.',
    C_E(24, -22, 12, ro=16, ri=6, rl=16), lambda c: d_ring(-62, -34, 92, 34, r_left=14, bowl=1.0))
add('C4', 'E with middle arm, through', 'Literal',
    'The literal E with the D running right through it (N1 layout, four crossings): the D’s flat end shows on the left.',
    lambda c: e_tongue(-50, -90, 44, 90, 6, 30, 30, 4, r_out=6, r_in=4, r_left=5),
    lambda c: d_ring(-84, -34, 92, 34, r_left=6, bowl=1.0))
add('C5', 'E with long middle arm', 'Literal',
    'C1 with a longer middle arm reaching well into the D, so the E reads even at a glance.',
    C_E(24, -22, 30), lambda c: d_ring(-62, -36, 96, 36, r_left=6, bowl=1.0))

if __name__ == '__main__':
    out = sys.argv[1] if len(sys.argv) > 1 else 'build'
    os.makedirs(out, exist_ok=True)
    only = set(sys.argv[2:])
    data = []
    for v in V:
        if only and v['id'] not in only: continue
        spec = {k: v[k] for k in ('E', 'D') }
        for k in ('wE', 'wD', 'start'):
            if k in v: spec[k] = v[k]
        r = render(spec)
        rec = {k: v[k] for k in ('id', 'name', 'family', 'note')}
        rec.update(grooved=r['grooved']['d'], solid=r['solid']['d'],
                   info={'grooved': r['grooved']['info'], 'solid': r['solid']['info']})
        data.append(rec)
        for cut in ('grooved', 'solid'):
            with open(os.path.join(out, f"{v['id']}-{cut}.svg"), 'w') as f:
                f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-100 -100 200 200">'
                        f'<path fill="#26734A" fill-rule="evenodd" d="{r[cut]["d"]}"/></svg>\n')
        print(v['id'], r['grooved']['info'], r['solid']['info'])
    PICKS = {'B2': 'endive-ed-chain-arms', 'A3': 'endive-ed-cross', 'B1': 'endive-ed-chain'}
    for rec in data:
        if rec['id'] in PICKS:
            for cut in ('grooved', 'solid'):
                for col, name in (('#26734A', ''), ('#7DCAA1', '-mint'), ('#FFFFFF', '-white'), ('#101814', '-black')):
                    os.makedirs(os.path.join(out, 'picks'), exist_ok=True)
                    with open(os.path.join(out, 'picks', f"{PICKS[rec['id']]}-{cut}{name}.svg"), 'w') as f:
                        f.write(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="-100 -100 200 200">'
                                f'<path fill="{col}" fill-rule="evenodd" d="{rec[cut]}"/></svg>\n')
    with open(os.path.join(out, 'variants.json'), 'w') as f:
        json.dump(data, f)
