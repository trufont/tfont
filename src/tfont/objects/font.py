import attr
from datetime import datetime
from tfont.objects.axis import Axis
from tfont.objects.feature import Feature, FeatureClass, FeatureHeader
from tfont.objects.glyph import Glyph
from tfont.objects.instance import Instance
from tfont.objects.master import Master, fontMasterDict
from tfont.util.tracker import (
    FontAxesDict, FontFeaturesDict, FontFeatureClassesDict,
    FontFeatureHeadersList, FontGlyphsList, FontInstancesList, FontMastersDict)
from typing import Any, Dict, List, Optional


@attr.s(cmp=False, repr=False, slots=True)
class Font:
    date: datetime = attr.ib(default=attr.Factory(datetime.utcnow))
    familyName: str = attr.ib(default="New Font")

    _axes: Dict[str, Axis] = attr.ib(default=attr.Factory(dict))
    _features: Dict[str, Feature] = attr.ib(default=attr.Factory(dict))
    _featureClasses: Dict[
        str, FeatureClass] = attr.ib(default=attr.Factory(dict))
    _featureHeaders: List[FeatureHeader] = attr.ib(default=attr.Factory(list))
    _glyphs: List[Glyph] = attr.ib(default=attr.Factory(list))
    _masters: Dict[str, Master] = attr.ib(default=attr.Factory(fontMasterDict))
    _instances: List[Instance] = attr.ib(default=attr.Factory(list))

    copyright: str = attr.ib(default="")
    designer: str = attr.ib(default="")
    designerURL: str = attr.ib(default="")
    manufacturer: str = attr.ib(default="")
    manufacturerURL: str = attr.ib(default="")
    unitsPerEm: int = attr.ib(default=1000)
    versionMajor: int = attr.ib(default=1)
    versionMinor: int = attr.ib(default=0)

    _extraData: Optional[Dict] = attr.ib(default=None)

    _cmap: Optional[Dict[int, int]] = attr.ib(default=None, init=False)
    _layoutEngine: Optional[Any] = attr.ib(default=None, init=False)
    _modified: bool = attr.ib(default=False, init=False)
    _selectedMaster: Optional[str] = attr.ib(default=None, init=False)

    def __attrs_post_init__(self):
        for axis in self._axes.values():
            axis._parent = self
        for feature in self._features.values():
            feature._parent = self
        for featCls in self._featureClasses.values():
            featCls._parent = self
        for featHdr in self._featureHeaders:
            featHdr._parent = self
        for glyph in self._glyphs:
            glyph._parent = self
        for master in self._masters.values():
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
    def extraData(self):
        extraData = self._extraData
        if extraData is None:
            extraData = self._extraData = {}
        return extraData

    @property
    def features(self):
        return FontFeaturesDict(self)

    @property
    def featureClasses(self):
        return FontFeatureClassesDict(self)

    @property
    def featureHeaders(self):
        return FontFeatureHeadersList(self)

    @property
    def glyphs(self):
        return FontGlyphsList(self)

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
        return FontMastersDict(self)

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
        try:
            return self._masters[self._selectedMaster]
        except KeyError:
            master = next(iter(self._masters.values()))
            self._selectedMaster = master.name
            return master

    def glyphForName(self, name):
        for glyph in self._glyphs:
            if glyph.name == name:
                return glyph

    def glyphForUnicode(self, value):
        gid = self.glyphIdForCodepoint(int(value, 16))
        if gid is not None:
            return self._glyphs[gid]

    def glyphIdForCodepoint(self, value, default=None):
        cache = self._cmap
        if cache is None:
            cache = self._cmap = {}
            for index, glyph in enumerate(self._glyphs):
                uni = glyph.unicode
                if uni is not None:
                    ch = int(uni, 16)
                    cache[ch] = index
        return cache.get(value, default)

    # maybe we could only have glyphForName and inline this func
    def glyphIdForName(self, name):
        for index, glyph in enumerate(self._glyphs):
            if glyph.name == name:
                return index
