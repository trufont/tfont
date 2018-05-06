import attr
from tfont.objects.guideline import Guideline
from tfont.objects.misc import AlignmentZone
from tfont.util.tracker import MasterGuidelinesList, obj_setattr
from typing import Any, Dict, List, Optional


@attr.s(cmp=False, repr=False, slots=True)
class Master:
    name: str = attr.ib(default="")
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

    _parent: Optional[Any] = attr.ib(default=None, init=False)
    visible: bool = attr.ib(default=False, init=False)

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

    def __setattr__(self, key, value):
        try:
            font = self._parent
        except AttributeError:
            pass
        else:
            if font is not None and key == "name":
                oldValue = getattr(self, key)
                if value != oldValue:
                    font.masters[value] = self
                return
        obj_setattr(self, key, value)

    @property
    def font(self):
        return self._parent

    @property
    def guidelines(self):
        return MasterGuidelinesList(self)


fontMasterDict = lambda: {"Regular": Master(name="Regular")}
