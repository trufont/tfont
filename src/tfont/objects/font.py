import attr
from datetime import datetime
from tfont.objects.axis import Axis
from tfont.objects.feature import Feature, FeatureClass, FeatureHeader
from tfont.objects.glyph import Glyph
from tfont.objects.instance import Instance
from tfont.objects.master import Master, fontMasterList
from tfont.util.tracker import TaggingDictList, TaggingList
from typing import Any, Dict, List, Optional


class FontAxesDictList(TaggingDictList):
    __slots__ = ()

    _property = "tag"
    _strict = True

    @property
    def _sequence(self):
        return self._parent._axes


class FontFeaturesDictList(TaggingDictList):
    __slots__ = ()

    _property = "tag"
    _strict = True

    @property
    def _sequence(self):
        return self._parent._features


class FontFeatureClassesDictList(TaggingDictList):
    __slots__ = ()

    _property = "name"
    _strict = True

    @property
    def _sequence(self):
        return self._parent._featureClasses


class FontFeatureHeadersDictList(TaggingDictList):
    __slots__ = ()

    _property = "description"
    _strict = True

    @property
    def _sequence(self):
        return self._parent._featureHeaders


class FontGlyphsDictList(TaggingDictList):
    __slots__ = ()

    _property = "name"
    _strict = True

    @property
    def _sequence(self):
        return self._parent._glyphs


# Note: when adding or deleting a master, do we cycle
# through all glyphs to add/remove corresponding master layers?
class FontMastersDictList(TaggingDictList):
    __slots__ = ()

    _property = "id"

    @property
    def _sequence(self):
        return self._parent._masters


class FontInstancesList(TaggingList):
    __slots__ = ()

    @property
    def _sequence(self):
        return self._parent._instances


@attr.s(cmp=False, repr=False, slots=True)
class Font:
    date: datetime = attr.ib(default=attr.Factory(datetime.utcnow))
    familyName: str = attr.ib(default="New Font")

    _axes: List[Axis] = attr.ib(default=attr.Factory(list))
    _features: List[Feature] = attr.ib(default=attr.Factory(list))
    _featureClasses: List[FeatureClass] = attr.ib(default=attr.Factory(list))
    _featureHeaders: List[FeatureHeader] = attr.ib(default=attr.Factory(list))
    _glyphs: List[Glyph] = attr.ib(default=attr.Factory(list))
    _masters: List[Master] = attr.ib(default=attr.Factory(fontMasterList))
    _instances: List[Instance] = attr.ib(default=attr.Factory(list))

    copyright: str = attr.ib(default="")
    designer: str = attr.ib(default="")
    designerURL: str = attr.ib(default="")
    manufacturer: str = attr.ib(default="")
    manufacturerURL: str = attr.ib(default="")
    unitsPerEm: int = attr.ib(default=1000)
    versionMajor: int = attr.ib(default=1)
    versionMinor: int = attr.ib(default=0)

    extraData: Dict = attr.ib(default=attr.Factory(dict))

    _cmap: Optional[Any] = attr.ib(default=None, init=False)
    _layoutEngine: Optional[Any] = attr.ib(default=None, init=False)
    _modified: bool = attr.ib(default=False, init=False)
    _selectedMaster: int = attr.ib(default=0, init=False)

    def __attrs_post_init__(self):
        for axis in self._axes:
            axis._parent = self
        for glyph in self._glyphs:
            glyph._parent = self
        for master in self._masters:
            master._parent = self
        for instance in self._instances:
            instance._parent = self

    def __repr__(self):
        return "%s(%r, v%d.%d with %d masters and %d instances)" % (
            self.__class__.__name__, self.familyName, self.versionMajor,
            self.versionMinor, len(self._masters), len(self._instances))

    @property
    def axes(self):
        return FontAxesDictList(self)

    @property
    def features(self):
        return FontFeaturesDictList(self)

    @property
    def featureClasses(self):
        return FontFeatureClassesDictList(self)

    @property
    def featureHeaders(self):
        return FontFeatureHeadersDictList(self)

    @property
    def glyphs(self):
        return FontGlyphsDictList(self)

    @property
    def instances(self):
        return FontInstancesList(self)

    @property
    def layoutEngine(self):
        layoutEngine = self._layoutEngine
        if layoutEngine is None:
            layoutEngine = self._layoutEngine = self.layoutEngineFactory()
        return layoutEngine

    @property
    def masters(self):
        return FontMastersDictList(self)

    @property
    def modified(self):
        modified = self._modified
        # undo will challenge that assumption,
        if not modified:
            for glyph in self._glyphs:
                if glyph._lastModified is not None:
                    modified = self._modified = True
                    break
        return modified

    @property
    def selectedMaster(self):
        # TODO when deleting a master, adjust self._selectedMaster
        return self._masters[self._selectedMaster]

    def glyphForUnicode(self, value):
        gid = self.glyphIdForCodepoint(int(value, 16))
        if gid is not None:
            return self._glyphs[gid]
        return None

    def glyphIdForCodepoint(self, value, default=None):
        cache = self._cmap
        if cache is None:
            cache = self._cmap = {}
            for index, glyph in enumerate(self._glyphs):
                uni = glyph.unicode
                if uni is None:
                    continue
                ch = int(uni, 16)
                cache[ch] = index
        return cache.get(value, default)

    # maybe we could only have glyphForName and inline this func
    def glyphIdForName(self, name):
        for index, glyph in enumerate(self._glyphs):
            if glyph.name == name:
                return index
        return None
