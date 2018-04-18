import attr
from typing import Optional


@attr.s(cmp=False, repr=False, slots=True)
class Axis:
    tag: str = attr.ib()
    minimum: int = attr.ib(default=0)
    maximum: int = attr.ib(default=0)
    default: int = attr.ib(default=0)
    name: str = attr.ib(default="")

    _parent: Optional[object] = attr.ib(default=None, init=False)

    def __repr__(self):
        return "%s(%r, [%d:%d:%d])" % (
            self.__class__.__name__, self.tag, self.minimum, self.default,
            self.maximum)
