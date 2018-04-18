Rounding
========

Never really round in the model, but when we use the data:

- when building the graphics path
- when showing coordinates (or making the segment bounds, there we always round
  to int)
- when saving the file? (round to 1 decimal or sth? or honor the std param)

The thing with rounding is we want to see its effects (however small) live,
otherwise we'd just round when saving to a file or so.

Undoing transformations seems useful w.r.t rounding.

We oughta have a customizable rounding grid, and (optionally?) exempt offCurves
from said rounding.
