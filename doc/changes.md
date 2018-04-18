Changes propagation
===================

In the interest of keeping things simple (and low overhead), we have
two kinds of changes propagation mechanisms:

- change *tracking* in the model, that directly clears caches (such
  as Layer.bounds, or in the case of Layer.selection, updates) and
  adds to the undo stack.
  * clearing caches is pretty much free, direct attribute access/set
    to None on slotted classes and/or up the parent tree. no extra
    function calls
  * the cost of undo can be offset for large changes by calling
    `Layer.beginChanges()`
- change *signaling* in the view, which is based on the insight that
  the model can only be mutated through the view (e.g. run a script,
  press a key, click a button), and therefore the refresh step can be
  handled purely in the view after each operation, which means e.g.
  that if you run a script that does many operations, you'll only pay
  the cost of "UpdateUI" callbacks once after it's done.

The other nice thing here is both model and view are maximally
insulated from each other's internals. The model does fast change
tracking with hardcoded attribute access, whereas the view just calls
refresh once a chain of operations is done.

That the view doesn't have to know/do too much about the model is a
plus for the developer, since it's the part of the code that changes
the most.

Also worth noting here, going through ctors is zero-cost (aside from
setting the objects parent field, custom `__setattr__` skips all
special processing until parent is set).

UpdateUI
--------

Have a simple UpdateUI callback that signals refresh when steps that
could change the font were made, expensive and/or repeated processing
(e.g. bounds) is cached in the model, the rest is done on each
UpdateUI call (which is still triggered smartly, e.g. a tool that
made no visible changes wouldn't call a refresh).

glyph.lastModified timestamp can also be useful for selective
invalidation outside of the builtin cached attributes.

Changes
-------

First, we don't track each and every change. We care primarily
about glyph changes (Glyph.lastModified), which is updated every
time an attribute or a child of glyph sees a change.

The way to implement it is with a subclass of `__setattr__`,
triggers only:

- when the parent attribute is set
- if the key doesn't start with `_`
- if the key isn't part of a handwritten blacklist

Then the value is compared to the old value. If it's changed
relevant cached objects in the parent elements are destroyed.
(We don't call separate functions to do so because function
calls are slow and this is performance critical code.)

Caching must be simple -- no need for (costly) abstractions.

Note: we could have a global switch to disable notifications,
like `attr.disable_validators`. Layer.beginChanges()/endChanges()
should also be useful, with `Layer._disabled` flag that custom
`__setattr__` can check.

Non-data changes (like `selected`) do not yield an update to
Glyph.lastModified.

What do we want to cache?

- Glyph undo
- Glyph.lastModified
- Layer.bounds
- Layer.graphicsPath
- Layer.noComponentsGraphicsPath
- Layer.selection <-- list of all selected stuff
                      (points, anchor, component, guideline)
                      good for fetching selectionBounds
- Layer.selectionBounds
- Path.bounds
- Path.graphicsPath

Undo
----

Implementing undo will mean basically replacing every glyph.lastModified
mutation with an undo transaction, and then the undo manager tracks
lastModified, i.e.:

~~~py
class Glyph:

    @property
    def lastModified(self):
        return self._undoManager.lastModified
~~~

To this we oughta add a grouping api, and a batching api (such as
Layer.beginChanges()/endChanges()) to improve performance in the face of many
incoming changes.

Undo change tracking:

Value, glyph attrs we can access directly:

- name
- unicode
- width
- height

Content, fat attrs that we store in serialized form:
here the difference is it's in Layer, hence Layer.beginChanges()/endChanges()

- paths
- components
- anchors
- guidelines

Note: when reading from file, we can keep the serialized form
then update as we go.

Also, we might want to consider font-level undo for font info and adding/del'in
glyphs. kerning? probably not worth it

Headless
--------

For headless code (non-UI) I'm thinking class decorators could strip the class
of irrelevant attributes/functionality before it is passed on to attrs,
depending on the value of an environment variable, e.g. `TFONT_HEADLESS`.

Code
----

~~~py
class Glyph:

    _value_keys = {"name", "unicode", "width", "height"} # ..

    def __setattr__(self, key, value):
        # we must also make sure we're past __init__
        if change_tracking and key in self._value_keys:
            oldValue = self.__getattribute__(key)
            object.__setattr__(self, key, value)
            if value != oldValue:
                self._undoManager.pushValueChange(
                    key, oldValue, value)
        else:
            object.__setattr__(self, key, value)


class Layer:

    # what can be set?
    # - width, height and corresponding leftMargin etc.
    # ...

    def __attrs_post_init__(self):
        # cattrs prevents us from keeping the parameters
        # in serialized form
        # we can catch em by subclassing __setattr__!
        # -- actually can we? I guess cattrs does bottom-to-top
        #    object creation so we'll get the objects
        self._state = _json_bundle
        # actually not the full bundle, but:
        # {
        #   "anchors": [..],
        #   "components": [..],
        #   "guidelines": [..],
        #   "paths": [..]
        # }
        # then we store a diff e.g. when anchors changed
        # we'll push:
        # {
        #   "anchors": [new list]
        # }
        # and signal to the glyph

    # bounds = actual contour bounds, used for margin calc
    # selectionBounds = controlPointBounds, used for selection bbox and alignment


class Path:

    # what can be set?
    # - point ops (PathPointsList tracker)
    # - reverse()
    # - segment ops <-- if we access points through tracker
    #                   then we've got nothing more to do
    # - selected <-- what does setter do anyway?
    # - setStartPoint()
    # - transform() <-- no-op if 1 0 0 1 0 0
    #                   or if layer is empty

    @property
    def clockwise(self):
        pen = AreaPen()
        pen.endPath = pen.closePath
        self.draw(pen)
        return pen.value < 0

    def addPointsAtExtrema(self):
        # let's see we got
        # - bezierMath.curveBounds
        # - then we need contour splitting code
        # make sure we notify
        raise NotImplementedError

    def draw(self, pen):
        points = self._points
        if not points:
            return
        start = points[0]
        skip = start.type is not None
        if skip:
            pen.moveTo((start.x, start.y))
        else:
            start = points[-1]
            assert start.type is not None
            pen.moveTo((start.x, start.y))
        stack = []
        for point in points:
            if skip:
                skip = False
                continue
            stack.append((point.x, point.y))
            if point.type == "line":
                pen.lineTo(*stack)
                stack = []
            elif point.type == "curve":
                pen.curveTo(*stack)
                stack = []
        assert not stack
        if start.type == "move":
            pen.endPath()
        else:
            pen.closePath()

~~~
