"""Colour + SVG assembly for the blank-page concepts."""
import numpy as np
from shapely.ops import unary_union
from shapely import affinity
from engine import path_d

def lin(id, a, b, x1=-80, y1=-95, x2=80, y2=95):
    return (f'<linearGradient id="{id}" gradientUnits="userSpaceOnUse" x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}">'
            f'<stop offset="0" stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient>')

def rad(id, a, oa, b, ob, cx=0, cy=0, r=90):
    return (f'<radialGradient id="{id}" gradientUnits="userSpaceOnUse" cx="{cx}" cy="{cy}" r="{r}">'
            f'<stop offset="0" stop-color="{a}" stop-opacity="{oa}"/><stop offset="1" stop-color="{b}" stop-opacity="{ob}"/></radialGradient>')

# role -> (kind, args) per ground
PAL = {
 'light': {
   'main': ('lin', '#2F8F5C', '#13442B'), 'ink': ('lin', '#2F8F5C', '#13442B'), 'ribbon': ('lin', '#5DB385', '#13442B', -95, 0, 95, 0),
   'alt': ('lin', '#86D0A8', '#3E9A6B'), 'rib': ('lin', '#2F8F5C', '#13442B'),
   'leaf0': ('lin', '#CFEBD7', '#7DCAA1', 0, -95, 0, 95), 'leaf1': ('lin', '#86D0A8', '#3E9A6B', 0, -95, 0, 95), 'leaf2': ('lin', '#86D0A8', '#3E9A6B', 0, -95, 0, 95),
   'leaf3': ('lin', '#3E9A6B', '#13442B', 0, -60, 0, 95), 'leaf4': ('lin', '#3E9A6B', '#13442B', 0, -60, 0, 95),
   'glow': ('none',), 'ground': ('lin', '#26734A', '#13442B', 0, 0, 0, 100), 'sprout': ('lin', '#3E9A6B', '#26734A', 0, -90, 0, 60), 'sprout2': ('flat', '#7DCAA1'),
   'tone1': ('flat', '#9AD8B6'), 'tone2': ('flat', '#3E9A6B'), 'tone3': ('flat', '#13442B'),
   'head0': ('flat', '#C7E8D2'), 'head1': ('flat', '#8FD0AC'), 'head2': ('flat', '#55AE80'), 'head3': ('flat', '#2B8355'), 'head4': ('flat', '#18573A'),
   'strand0': ('lin', '#2F8F5C', '#13442B'), 'strand1': ('lin', '#86D0A8', '#3E9A6B'), 'strand2': ('lin', '#2F8F5C', '#13442B'),
   'head': ('rad', '#C7E8D2', 1, '#13442B', 1, 0, 0, 96),
   'fold_a': ('lin', '#9DDCB9', '#3E9A6B', -40, -90, 20, 90), 'fold_b': ('lin', '#26734A', '#0F3A24', 40, -90, -20, 90),
   'shadow': ('shadow', '#0B2A1A', 0.22),
 },
 'dark': {
   'main': ('lin', '#C2EDD3', '#4FA77A'), 'ink': ('lin', '#E4F5E8', '#7DCAA1'), 'ribbon': ('lin', '#F1F4DC', '#3E9A6B', 95, 0, -95, 0),
   'alt': ('lin', '#F1F4DC', '#B5E0A6'), 'rib': ('lin', '#C2EDD3', '#4FA77A'),
   'leaf0': ('lin', '#FBFBEA', '#E3EFC4', 0, -95, 0, 95), 'leaf1': ('lin', '#E6F3D2', '#A9DDBB', 0, -95, 0, 95), 'leaf2': ('lin', '#E6F3D2', '#A9DDBB', 0, -95, 0, 95),
   'leaf3': ('lin', '#9DDCB9', '#3E9A6B', 0, -60, 0, 95), 'leaf4': ('lin', '#9DDCB9', '#3E9A6B', 0, -60, 0, 95),
   'glow': ('rad', '#7DCAA1', 0.38, '#7DCAA1', 0.0), 'ground': ('lin', '#2F8F5C', '#13442B', 0, 0, 0, 100), 'sprout': ('lin', '#FBFBEA', '#C2EDD3', 0, -90, 0, 60), 'sprout2': ('flat', '#A9DDBB'),
   'tone1': ('flat', '#2B7A50'), 'tone2': ('flat', '#5DB385'), 'tone3': ('flat', '#D4F0DF'),
   'head0': ('flat', '#FBFBEA'), 'head1': ('flat', '#D7EFC9'), 'head2': ('flat', '#9DDCB9'), 'head3': ('flat', '#55AE80'), 'head4': ('flat', '#2B7A50'),
   'strand0': ('lin', '#9DDCB9', '#3E9A6B'), 'strand1': ('lin', '#FBFBEA', '#C9E9C0'), 'strand2': ('lin', '#9DDCB9', '#3E9A6B'),
   'head': ('rad', '#FBFBEA', 1, '#26734A', 1, 0, 0, 96),
   'fold_a': ('lin', '#FBFBEA', '#BFE6CB', -40, -90, 20, 90), 'fold_b': ('lin', '#7DCAA1', '#2B7A50', 40, -90, -20, 90),
   'shadow': ('shadow', '#000000', 0.38),
 },
}

def fit_layers(layers, half=92.0, rot=0):
    if rot: layers = [(r, affinity.rotate(g, rot, origin=(0, 0))) for r, g in layers]
    body = unary_union([g for r, g in layers if r not in ('glow', 'shadow') and g is not None and not g.is_empty])
    x0, y0, x1, y1 = body.bounds
    s = half / max((x1 - x0) / 2, (y1 - y0) / 2); cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
    out = [(r, affinity.scale(affinity.translate(g, -cx, -cy), s, s, origin=(0, 0))) for r, g in layers if g is not None and not g.is_empty]
    fit_layers.last = (cx, cy, s, rot)
    return out

def symbol(sid, layers, ground, mono=None):
    pal = PAL[ground]; defs = []; body = []
    mark = unary_union([g for r, g in layers if r not in ('glow', 'shadow')])
    clip_id = f'{sid}-clip'; blur_id = f'{sid}-blur'
    have_shadow = any(r == 'shadow' for r, g in layers)
    if have_shadow:
        defs.append(f'<clipPath id="{clip_id}"><path d="{path_d(mark)}" fill-rule="evenodd"/></clipPath>')
        defs.append(f'<filter id="{blur_id}" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="0.9"/></filter>')
    used = {}
    for r, g in layers:
        d = path_d(g)
        if not d: continue
        if mono:
            if r in ('glow', 'shadow'): continue
            body.append(f'<path fill="{mono}" fill-rule="evenodd" d="{d}"/>'); continue
        spec = pal[r]
        if spec[0] == 'none': continue
        if spec[0] == 'shadow':
            body.append(f'<g clip-path="url(#{clip_id})"><path fill="{spec[1]}" fill-opacity="{spec[2]}" filter="url(#{blur_id})" d="{d}"/></g>')
            continue
        if spec[0] == 'flat':
            fill = spec[1]
        else:
            gid = f'{sid}-{r}'
            if gid not in used:
                used[gid] = 1
                if spec[0] == 'lin': defs.append(lin(gid, *spec[1:]))
                else: defs.append(rad(gid, *spec[1:]))
            fill = f'url(#{gid})'
        body.append(f'<path fill="{fill}" fill-rule="evenodd" d="{d}"/>')
    # draw shadows right after the layer they fall on: simple approach = shadows above fills, clipped to mark
    fills = [b for b in body if 'clip-path' not in b]; shades = [b for b in body if 'clip-path' in b]
    ordered = fills[:1] + shades + fills[1:] if False else _order(layers, body)
    return f'<symbol id="{sid}" viewBox="-100 -100 200 200"><defs>{"".join(defs)}</defs>{"".join(ordered)}</symbol>'

def _order(layers, body):
    # glow first, then fills, with shadows after all fills (they are clipped to the mark)
    glow = [b for b in body if '-glow)' in b]
    shades = [b for b in body if 'clip-path' in b]
    rest = [b for b in body if b not in glow and b not in shades]
    return glow + rest + shades
