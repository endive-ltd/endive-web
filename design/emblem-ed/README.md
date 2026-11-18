# Endive E–D rings (emblem exploration, round 3)

Brief: stylise N1's upright ring as a semi "E" and the flat ring as a semi "D", keeping the interlocked rings.

- `generate.py` builds all 16 variants parametrically (shapely): rounded-polygon centre lines, buffered bands,
  optional grooves, true over/under weave with a linking-number check and a sliver report.
  Run: `pip install shapely numpy && python3 generate.py OUT_DIR` (writes per-variant SVGs, `variants.json`, `picks/`).
- `svg/`: final files for the recommended picks, grooved and solid cuts, in green / mint / white / black:
  - `endive-ed-chain-arms-*` = B2 "Chain link, E arms" (top pick)
  - `endive-ed-cross-*` = A3 "D slides right" (closest to N1)
  - `endive-ed-chain-*` = B1 "Chain link" (runner-up)

These are exploration files only; the live brand pack in `site/public/brand/` is unchanged.

## Round 7 ("refined")

- `generate_r7.py`: each ring is one smooth superellipse whose exponent blends from a squarer left
  (E) to a rounder right (D), so there are no corners or straight-to-curve joins. It uses a lighter
  N1-weight band with a subtle thinning at crossings, even gaps with softened cut ends, optical
  centring, and slight overshoot on round ends. Run: `python3 generate_r7.py OUT_DIR`.
- `svg-r7/`: picks in green / mint / white / black, grooved and solid:
  - `endive-ed-r7-soft-cross-*` = S2 "Soft E, round D" (top pick)
  - `endive-ed-r7-chain-*` = S5 "Chain link, sleek" (second pick)
  - `endive-ed-r7-n1-touch-*` = S1 "N1, barely touched" (safe baseline)
