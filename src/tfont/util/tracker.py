from collections.abc import MutableMapping, MutableSequence
from time import time

obj_setattr = object.__setattr__


class TrackingDict(MutableMapping):
    """
    Note: dict bears a value iterator (given that keys are just cached attrs).
    """
    __slots__ = "_dict", "_parent"

    def applyChange(self):
        pass

    def __init__(self, parent):
        self._parent = parent
        self._dict = getattr(parent, self._property)

    def __delitem__(self, key):
        dict_ = self._dict
        dict_[key]._parent = None
        del dict_[key]
        self.applyChange()

    def __getitem__(self, key):
        return self._dict[key]

    def __iter__(self):
        return iter(self._dict.values())

    def __len__(self):
        return len(self._dict)

    def __setitem__(self, key, value):
        parent = self._parent
        if value._parent is parent:
            oldKey = getattr(value, self._attr)
            del self._dict[oldKey]
        else:
            value._parent = parent
        obj_setattr(value, self._attr, key)
        self._dict[key] = value
        self.applyChange()

    # aux methods

    def __repr__(self):
        return repr(self._dict)

    def clear(self):
        dict_ = self._dict
        for value in dict_.values():
            value._parent = None
        dict_.clear()

    def keys(self):
        return self._dict.keys()

    def items(self):
        return self._dict.items()

    def popitem(self):
        item = self._dict.popitem()
        item[1]._parent = None
        self.applyChange()
        return item

    def values(self):
        return self._dict.values()


class TrackingList(MutableSequence):
    __slots__ = "_list", "_parent"

    def applyChange(self):
        pass

    def __init__(self, parent):
        self._parent = parent
        self._list = getattr(parent, self._property)

    def __delitem__(self, key):
        list_ = self._list
        value = list_[key]
        del list_[key]
        if key.__class__ is slice:
            for v in value:
                v._parent = None
        else:
            value._parent = None
        self.applyChange()

    def __getitem__(self, key):
        return self._list[key]

    def __len__(self):
        return len(self._list)

    def __setitem__(self, key, value):
        self._list[key] = value
        parent = self._parent
        if key.__class__ is slice:
            for v in value:
                v._parent = parent
        else:
            value._parent = parent
        self.applyChange()

    def insert(self, index, value):
        value._parent = self._parent
        self._list.insert(index, value)
        self.applyChange()

    # aux methods

    def __iter__(self):
        return iter(self._list)

    def __repr__(self):
        return repr(self._list)

    def __reversed__(self):
        return reversed(self._list)

# ---------------
# Specializations
# ---------------

# Font


class FontAxesDict(TrackingDict):
    __slots__ = ()

    _attr = "tag"
    _property = "_axes"


class FontFeaturesDict(TrackingDict):
    __slots__ = ()

    _attr = "tag"
    _property = "_features"

    def applyChange(self):
        font = self._parent
        font._layoutEngine = None


class FontFeatureClassesDict(TrackingDict):
    __slots__ = ()

    _attr = "name"
    _property = "_featureClasses"

    def applyChange(self):
        font = self._parent
        font._layoutEngine = None


class FontFeatureHeadersList(TrackingList):
    __slots__ = ()

    _property = "_featureHeaders"

    def applyChange(self):
        font = self._parent
        font._layoutEngine = None


class FontGlyphsList(TrackingList):
    __slots__ = ()

    _property = "_glyphs"

    def applyChange(self):
        font = self._parent
        font._cmap = font._layoutEngine = None


# Note: when adding or deleting a master, do we cycle
# through all glyphs to add/remove corresponding master layers?
class FontMastersDict(TrackingDict):
    __slots__ = ()

    _attr = "name"
    _property = "_masters"

    def applyChange(self):
        font = self._parent
        selectedMaster = font._selectedMaster
        if selectedMaster is not None and selectedMaster not in font._masters:
            font._selectedMaster = None


class FontInstancesList(TrackingList):
    __slots__ = ()

    _property = "_instances"

# Glyph


class GlyphLayersList(TrackingList):
    __slots__ = ()

    _property = "_layers"

    def applyChange(self):
        glyph = self._parent
        glyph._lastModified = time()

# Layer


class LayerAnchorsDict(TrackingDict):
    __slots__ = ()

    _attr = "name"
    _property = "_anchors"

    def applyChange(self):
        layer = self._parent
        layer._bounds = None
        glyph = layer._parent
        if glyph is None:
            return
        glyph._lastModified = time()

    def __delitem__(self, key):
        dict_ = self._dict
        value = dict_[key]
        del dict_[key]
        value._parent = None
        if value.selected:
            layer = self._parent._parent
            if layer is not None:
                layer._selection.remove(value)
                layer._selectionBounds = None
        self.applyChange()

    def __setitem__(self, key, value):
        parent = self._parent
        if value._parent is parent:
            oldKey = getattr(value, self._attr, key)
            del self._dict[oldKey]
        else:
            value._parent = parent
        obj_setattr(value, self._attr, key)
        self._dict[key] = value
        if value.selected:
            layer = self._parent._parent
            if layer is not None:
                layer._selection.add(value)
                layer._selectionBounds = None
        self.applyChange()

    def popitem(self):
        item = self._dict.popitem()
        value = item[1]
        value._parent = None
        if value.selected:
            layer = self._parent._parent
            if layer is not None:
                layer._selection.remove(value)
                layer._selectionBounds = None
        self.applyChange()
        return item


def _Layer_selectible_delitem(self, key):
    list_ = self._list
    value = list_[key]
    del list_[key]
    layer = self._parent
    if key.__class__ is slice:
        for v in value:
            v._parent = None
            if v.selected:
                layer._selection.remove(v)
                layer._selectionBounds = None
    else:
        value._parent = None
        if value.selected:
            layer._selection.remove(value)
            layer._selectionBounds = None
    self.applyChange()


def _Layer_selectible_setitem(self, key, value):
    self._list[key] = value
    layer = self._parent
    if key.__class__ is slice:
        for v in value:
            v._parent = layer
            if v.selected:
                layer._selection.add(v)
                layer._selectionBounds = None
    else:
        value._parent = layer
        if value.selected:
            layer._selection.add(value)
            layer._selectionBounds = None
    self.applyChange()


def _Layer_selectible_insert(self, index, value):
    self._list.insert(index, value)
    value._parent = layer = self._parent
    if value.selected:
        layer._selection.add(value)
        layer._selectionBounds = None
    self.applyChange()


class LayerComponentsList(TrackingList):
    __slots__ = ()

    _property = "_components"

    def applyChange(self):
        layer = self._parent
        layer._bounds = None
        glyph = layer._parent
        if glyph is None:
            return
        glyph._lastModified = time()

    __delitem__ = _Layer_selectible_delitem

    __setitem__ = _Layer_selectible_setitem

    insert = _Layer_selectible_insert


class LayerGuidelinesList(TrackingList):
    __slots__ = ()

    _property = "_guidelines"

    def applyChange(self):
        layer = self._parent
        layer._bounds = None
        glyph = layer._parent
        if glyph is None:
            return
        glyph._lastModified = time()

    __delitem__ = _Layer_selectible_delitem

    __setitem__ = _Layer_selectible_setitem

    insert = _Layer_selectible_insert


class LayerPathsList(TrackingList):
    __slots__ = ()

    _property = "_paths"

    def applyChange(self):
        layer = self._parent
        layer._bounds = layer._closedGraphicsPath = layer._openGraphicsPath = \
            None
        glyph = layer._parent
        if glyph is None:
            return
        glyph._lastModified = time()

    def __delitem__(self, key):
        list_ = self._list
        value = list_[key]
        del list_[key]
        layer = self._parent
        layer._selectedPaths = None
        if key.__class__ is slice:
            for v in value:
                v._parent = None
        else:
            value._parent = None
        self.applyChange()

    def __setitem__(self, key, value):
        self._list[key] = value
        layer = self._parent
        layer._selectedPaths = None
        if key.__class__ is slice:
            for v in value:
                v._parent = layer
        else:
            value._parent = layer
        self.applyChange()

    def insert(self, index, value):
        self._list.insert(index, value)
        value._parent = layer = self._parent
        layer._selectedPaths = None
        self.applyChange()

# Master


class MasterGuidelinesList(TrackingList):
    __slots__ = ()

    _property = "_guidelines"

# Path


class PathPointsList(TrackingList):
    __slots__ = ()

    _property = "_points"

    def applyChange(self):
        path = self._parent
        path._bounds = path._graphicsPath = None
        layer = path._parent
        if layer is None:
            return
        layer._bounds = layer._closedGraphicsPath = layer._openGraphicsPath = \
            None
        glyph = layer._parent
        if glyph is None:
            return
        glyph._lastModified = time()

    def __delitem__(self, key):
        list_ = self._list
        value = list_[key]
        del list_[key]
        layer = self._parent._parent
        if key.__class__ is slice:
            for v in value:
                v._parent = None
                if layer is not None and v.selected:
                    layer._selection.remove(v)
                    layer._selectedPaths = layer._selectionBounds = None
        else:
            value._parent = None
            if layer is not None and value.selected:
                layer._selection.remove(value)
                layer._selectedPaths = layer._selectionBounds = None
        self.applyChange()

    def __setitem__(self, key, value):
        self._list[key] = value
        parent = self._parent
        layer = parent._parent
        if key.__class__ is slice:
            for v in value:
                v._parent = parent
                if layer is not None and v.selected:
                    layer._selection.add(v)
                    layer._selectedPaths = layer._selectionBounds = None
        else:
            value._parent = parent
            if layer is not None and value.selected:
                layer._selection.add(value)
                layer._selectedPaths = layer._selectionBounds = None
        self.applyChange()

    def insert(self, index, value):
        self._list.insert(index, value)
        value._parent = parent = self._parent
        if value.selected:
            layer = parent._parent
            if layer is not None:
                layer._selection.add(value)
                layer._selectedPaths = layer._selectionBounds = None
        self.applyChange()
