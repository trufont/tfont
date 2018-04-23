import attr
from tfont.util.tracker import obj_setattr
from time import time
from typing import Optional, Union


@attr.s(cmp=False, repr=False, slots=True)
class Anchor:
    x: Union[int, float] = attr.ib()
    y: Union[int, float] = attr.ib()
    name: str = attr.ib(default="")

    _parent: Optional[object] = attr.ib(default=None, init=False)
    selected: bool = attr.ib(default=False, init=False)

    def __repr__(self):
        return "%s(%r, %r, %r)" % (
            self.__class__.__name__, self.name, self.x, self.y)

    def __setattr__(self, key, value):
        try:
            layer = self._parent
        except AttributeError:
            pass
        else:
            if layer is not None and key[0] != "_":
                oldValue = getattr(self, key)
                if value != oldValue:
                    if key == "name":
                        layer.anchors[value] = self
                        return
                    obj_setattr(self, key, value)
                    if key == "selected":
                        if value:
                            layer._selection.add(self)
                        else:
                            layer._selection.remove(self)
                        layer._selectionBounds = None
                    else:
                        if self.selected:
                            layer._selectionBounds = None
                        glyph = layer._parent
                        glyph._lastModified = time()
                return
        obj_setattr(self, key, value)
