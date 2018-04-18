Tracker (for sequence type mutation)
====================================

The tracking concept (rather than subclassing list with extra methods to e.g.
set parent attribute or index anchors by key) allows us to use standard lists
for storage and not store a ptr to us in said list. This way our bottom-up
tree is consistent:

~~~
    parent
  +---------+
  ↓         |
layer --> anchor
~~~

layer.anchors returns a tracking list, that puts anchors in `layer._anchors`
and sets `anchor._parent`, amongst other things like ensuring key uniqueness.

That's good otherwise we'd have to store yet another parent pointer in
`layer._anchors` list.

Trackers also serve to flush caches and update Glyph.lastModified after each
operation.

Other nice thing about tracker is with internal functions one can just work on
the bare lists etc. and not pay the cost of extra function calls.
