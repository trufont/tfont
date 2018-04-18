import attr
from tfont.objects.layer import Layer
from tfont.objects.misc import obj_setattr
from tfont.util.tracker import TrackingDictList
from time import time
from typing import List, Optional


class GlyphLayersDictList(TrackingDictList):
    __slots__ = ()

    _getattr = lambda obj, attr: getattr(
        obj, attr) if obj.masterLayer else None
    _property = "masterId"

    def __init__(self, parent):
        self._parent = parent
        font = parent._parent
        if font is None:
            return
        sequence = self._sequence
        count = sum(layer.masterLayer for layer in sequence)
        masters = font._masters
        if count >= len(masters):
            return
        for master in masters:
            # lame, this is n^2
            # we should spell out the lookup
            if master.id not in self:
                layer = Layer(masterId=master.id, masterLayer=True)
                layer._parent = parent
                sequence.append(layer)

    @property
    def _sequence(self):
        return self._parent._layers


@attr.s(cmp=False, repr=False, slots=True)
class Glyph:
    name: str = attr.ib()
    unicodes: List[str] = attr.ib(default=attr.Factory(list))

    leftKerningGroup: str = attr.ib(default="")
    rightKerningGroup: str = attr.ib(default="")
    bottomKerningGroup: str = attr.ib(default="")
    topKerningGroup: str = attr.ib(default="")

    _layers: List[Layer] = attr.ib(default=attr.Factory(list))

    color: Optional[tuple] = attr.ib(default=None)
    _extraData: Optional[dict] = attr.ib(default=None)

    _lastModified: Optional[float] = attr.ib(default=None, init=False)
    _parent: Optional[object] = attr.ib(default=None, init=False)
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
        return GlyphLayersDictList(self)

    @property
    def unicode(self):
        unicodes = self.unicodes
        if unicodes:
            return unicodes[0]
        return None
