repr (type representation)
==========================

Ideally, repr is concise and copy-pasting it in REPL recreates the objects.
Only the important data is shown though.

Here's the repr for some common types:

~~~python
Component('A', Transformation(1, 0, 0, 1, 0, 0))
Point(10, 0, 'curve', smooth=True)
Anchor('top', 10, 0)
Path([Point(10, 0), Point(10, 0), Point(10, 0)])
Guideline(10, 0, angle=0.0)
~~~

You can see `smooth=True` is shown as just True would be unclear.

The path list is pretty-printed, meaning it will wrap if it
exceeds 80 chars.

~~~python
Master('Medium Condensed', wght=500, wdth=200)
~~~

Here the meaningful data is too big to be shown, so we just show
the meaningful stats directly:

~~~python
Font('Charter Nova', v1.0 with 4 masters and 0 instances)
Glyph('A', 2 layers)
Layer('Regular', 3 paths, glyph 'A' master)
~~~
