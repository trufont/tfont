import attr
from typing import Any, Dict, Optional

# add access to interpolated glyphs --> Instance.glyphs

# api to export font
# api to convert an instance into a master?


@attr.s(cmp=False, repr=False, slots=True)
class Instance:
    familyName: str = attr.ib(default="")
    styleName: str = attr.ib(default="")
    location: Dict[str, int] = attr.ib(default=attr.Factory(dict))

    bold: bool = attr.ib(default=False)
    italic: bool = attr.ib(default=False)
    preferredFamilyName: str = attr.ib(default="")
    preferredSubfamilyName: str = attr.ib(default="")
    postscriptFontName: str = attr.ib(default="")
    postscriptFullName: str = attr.ib(default="")

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
        name = f"{self.familyName} {self.styleName}".rstrip()
        return "%s(%r%s)" % (self.__class__.__name__, name, more)
