import attr
from tfont.util.tracker import obj_setattr
from typing import Optional


@attr.s(cmp=False, repr=False, slots=True)
class Axis:
    tag: str = attr.ib(default="")
    min: int = attr.ib(default=0)
    max: int = attr.ib(default=0)
    default: int = attr.ib(default=0)
    name: str = attr.ib(default="")

    _parent: Optional[object] = attr.ib(default=None, init=False)

    def __repr__(self):
        return "%s(%r, [%d:%d:%d])" % (
            self.__class__.__name__, self.tag, self.minimum, self.default,
            self.maximum)

    def __setattr__(self, key, value):
        try:
            font = self._parent
        except AttributeError:
            pass
        else:
            if font is not None and key == "tag":
                oldValue = getattr(self, key)
                if value != oldValue:
                    font.axes[value] = self
                return
        obj_setattr(self, key, value)
