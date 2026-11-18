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
