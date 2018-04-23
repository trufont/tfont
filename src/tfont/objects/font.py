import attr
from datetime import datetime
from tfont.objects.axis import Axis
from tfont.objects.feature import Feature, FeatureClass, FeatureHeader
from tfont.objects.glyph import Glyph
from tfont.objects.instance import Instance
from tfont.objects.master import Master, fontMasterList
from tfont.util.tracker import (
    FontAxesDict, FontFeaturesDict, FontFeatureClassesDict,
    FontFeatureHeadersDict, FontGlyphsDict, FontInstancesList, FontMastersList)
from typing import Any, Dict, List, Optional


@attr.s(cmp=False, repr=False, slots=True)
class Font:
    date: datetime = attr.ib(default=attr.Factory(datetime.utcnow))
    familyName: str = attr.ib(default="New Font")

    _axes: Dict[str, Axis] = attr.ib(default=attr.Factory(dict))
    _features: Dict[str, Feature] = attr.ib(default=attr.Factory(dict))
    _featureClasses: Dict[
        str, FeatureClass] = attr.ib(default=attr.Factory(dict))
    _featureHeaders: Dict[
        str, FeatureHeader] = attr.ib(default=attr.Factory(dict))
    _glyphs: Dict[str, Glyph] = attr.ib(default=attr.Factory(dict))
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
        for axis in self._axes.values():
            axis._parent = self
        for feature in self._features.values():
            feature._parent = self
        for featCls in self._featureClasses.values():
            featCls._parent = self
        for featHdr in self._featureHeaders.values():
            featHdr._parent = self
        for glyph in self._glyphs.values():
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
        return FontAxesDict(self)

    @property
    def features(self):
        return FontFeaturesDict(self)

    @property
    def featureClasses(self):
        return FontFeatureClassesDict(self)

    @property
    def featureHeaders(self):
        return FontFeatureHeadersDict(self)

    @property
    def glyphs(self):
        return FontGlyphsDict(self)

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
        return FontMastersList(self)

    @property
    def modified(self):
        modified = self._modified
        # undo will challenge that assumption,
        if not modified:
            for glyph in self._glyphs.values():
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
            for index, glyph in enumerate(self._glyphs.values()):
                uni = glyph.unicode
                if uni is None:
                    continue
                ch = int(uni, 16)
                cache[ch] = index
        return cache.get(value, default)

    # maybe we could only have glyphForName and inline this func
    def glyphIdForName(self, name):
        for index, glyph in enumerate(self._glyphs.values()):
            if glyph.name == name:
                return index
        return None

    def masterForId(self, key):
        masters = self._masters
        for master in masters:
            if master.id == key:
                return master
        raise KeyError(key)
