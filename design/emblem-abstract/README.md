# Endive abstract marks (round 10)

No leaves or plants: four original one-colour marks for a tech company, drawn from circles and
straight cuts with an even band weight and real over/under where bands cross.

- `shapes.py`: all sketches (including dropped ones). Uses the weave engine in `../emblem-blank/engine.py`.
- `final.py`: builds the four final marks. Run: `pip install shapely numpy && python3 final.py OUT_DIR`.
- `svg/endive-mark-<id>[-white|-black|-mint].svg`:
  - `split`: Split Ring (recommended): one ring cut in two, halves sliding past each other.
  - `tiles`: Linked Tiles, `rings`: Two Rings, `trefoil`: Trefoil.

The live brand pack is unchanged.

## Round 11: The Joint

- `shapes2.py`: less-archetypal sketches (all dropped).
- `joint.py`: the dovetail-joint family; `final_joint.py` builds the four finals.
- `svg/endive-mark-joint*.svg`: `joint` (recommended disc), `jtile`, `jpill`, `jshift`.
