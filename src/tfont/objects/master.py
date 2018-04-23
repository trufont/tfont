import attr
from tfont.objects.guideline import Guideline
from tfont.objects.misc import AlignmentZone, uuid4_str
from tfont.util.tracker import TrackingList
from typing import Any, Dict, List, Optional


class MasterGuidelinesList(TrackingList):
    __slots__ = ()

    _property = "_guidelines"


@attr.s(cmp=False, repr=False, slots=True)
class Master:
    name: str = attr.ib(default="Regular")
    id: str = attr.ib(default=attr.Factory(uuid4_str))
    location: Dict[str, int] = attr.ib(default=attr.Factory(dict))

    alignmentZones: List[AlignmentZone] = attr.ib(default=attr.Factory(list))
    hStems: List[int] = attr.ib(default=attr.Factory(list))
    vStems: List[int] = attr.ib(default=attr.Factory(list))

    ascender: int = attr.ib(default=800)
    capHeight: int = attr.ib(default=700)
    descender: int = attr.ib(default=-200)
    italicAngle: float = attr.ib(default=0.)
    xHeight: int = attr.ib(default=500)

    _guidelines: List[Guideline] = attr.ib(default=attr.Factory(list))
    hKerning: Dict[str, Dict[str, int]] = attr.ib(default=attr.Factory(dict))
    vKerning: Dict[str, Dict[str, int]] = attr.ib(default=attr.Factory(dict))

    visible: bool = attr.ib(default=False)

    _parent: Optional[Any] = attr.ib(default=None, init=False)

    def __repr__(self):
        more = ""
        font = self._parent
        if font is not None:
            loc = self.location
            axes = font.axes
            for tag in ("wght", "wdth"):
                try:
                    more += ", %s=%r" % (tag, loc.get(tag, axes[tag]))
                except KeyError:
                    pass
        return "%s(%r%s)" % (self.__class__.__name__, self.name, more)

    @property
    def font(self):
        return self._parent

    @property
    def guidelines(self):
        return MasterGuidelinesList(self)


fontMasterList = lambda: [Master()]
