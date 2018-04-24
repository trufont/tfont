import attr
from tfont.objects.layer import Layer
from tfont.util.tracker import GlyphLayersList, obj_setattr
from time import time
from typing import Any, Dict, List, Optional, Tuple


@attr.s(cmp=False, repr=False, slots=True)
class Glyph:
    name: str = attr.ib(default="")
    unicodes: List[str] = attr.ib(default=attr.Factory(list))

    leftKerningGroup: str = attr.ib(default="")
    rightKerningGroup: str = attr.ib(default="")
    bottomKerningGroup: str = attr.ib(default="")
    topKerningGroup: str = attr.ib(default="")

    _layers: List[Layer] = attr.ib(default=attr.Factory(list))

    color: Optional[Tuple] = attr.ib(default=None)
    _extraData: Optional[Dict] = attr.ib(default=None)

    _lastModified: Optional[float] = attr.ib(default=None, init=False)
    _parent: Optional[Any] = attr.ib(default=None, init=False)
    selected: bool = attr.ib(default=False, init=False)

    def __attrs_post_init__(self):
        for layer in self._layers:
            layer._parent = self

    def __repr__(self):
        return "%s(%r, %d layers)" % (
            self.__class__.__name__, self.name, len(self._layers))

    def __setattr__(self, key, value):
        try:
            font = self._parent
        except AttributeError:
            pass
        else:
            if font is not None and key[0] != "_" \
                                and key != "selected":
                oldValue = getattr(self, key)
                if value != oldValue:
                    if key == "name":
                        font.glyphs[value] = self
                        return
                    obj_setattr(self, key, value)
                    self._lastModified = time()
                return
        obj_setattr(self, key, value)

    @property
    def extraData(self):
        extraData = self._extraData
        if extraData is None:
            extraData = self._extraData = {}
        return extraData

    @property
    def font(self):
        return self._parent

    @property
    def lastModified(self):
        return self._lastModified

    @property
    def layers(self):
        return GlyphLayersList(self)

    @property
    def unicode(self):
        unicodes = self.unicodes
        if unicodes:
            return unicodes[0]
        return None

    def layerForId(self, key):
        if key is None:
            font = self._parent
            if font is not None:
                key = font.selectedMaster.id
        layers = self._layers
        for layer in layers:
            if layer.masterLayer and layer.masterId == key:
                return layer
        if not key or key.__class__ is not str:
            raise ValueError("invalid id %r" % key)
        layer = Layer(masterId=key, masterLayer=True)
        layer._parent = self
        layers.append(layer)
        return layer
