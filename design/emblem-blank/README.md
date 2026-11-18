# Endive emblem: blank page (round 8)

Ten concepts built from scratch. The only rule kept: nothing that reads as a hooked cross from any angle.

- `engine.py`: ribbons with tapering widths, automatic crossings and a consistent over/under weave,
  grooves that taper to points where a band dives under, pointed leaves with tapering ribs.
- `concepts.py`: one function per concept (plus two that were dropped: glass rosette, twin-leaf ribbon).
- `render.py`: colours, gradients and soft crossing shadows for light and dark grounds.
- `generate.py`: builds everything. Run: `pip install shapely numpy && python3 generate.py OUT_DIR`.
- `review.py`: big side-by-side review sheet used while iterating.
- `svg/endive-<concept>-light.svg` / `-dark.svg`: final marks for each concept
  (trinity, head, braid, bloom, sprout, linked, folded, spear, brush, pentafoil).

Top three: Leaf Trinity (`trinity`), Golden Head (`head`), Braided Spear (`braid`).
The live brand pack is unchanged.
