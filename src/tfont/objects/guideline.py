import attr
from tfont.util.tracker import obj_setattr
from time import time
from typing import Any, Optional, Union


@attr.s(cmp=False, repr=False, slots=True)
class Guideline(object):
    x: Union[int, float] = attr.ib()
    y: Union[int, float] = attr.ib()
    angle: Union[int, float] = attr.ib()
    name: str = attr.ib(default="")

    _parent: Optional[Any] = attr.ib(default=None, init=False)
    selected: bool = attr.ib(default=False, init=False)

    def __repr__(self):
        # name?
        return "%s(%r, %r, angle=%r)" % (
            self.__class__.__name__, self.x, self.y, self.angle)

    def __setattr__(self, key, value):
        try:
            parent = self._parent
        except AttributeError:
            pass
        else:
            if hasattr(parent, "masterName") and key[0] != "_":
                oldValue = getattr(self, key)
                if value != oldValue:
                    obj_setattr(self, key, value)
                    if key == "selected":
                        if value:
                            parent._selection.add(self)
                        else:
                            parent._selection.remove(self)
                        parent._selectionBounds = None
                    else:
                        # we don't really care about guidelines in the
                        # selection bounds, tbh
                        if (key == "x" or key == "y") and self.selected:
                            parent._selectionBounds = None
                        glyph = parent._parent
                        glyph._lastModified = time()
                return
        obj_setattr(self, key, value)

    @property
    def font(self):
        parent = self._parent
        if parent is not None:
            return parent.font
