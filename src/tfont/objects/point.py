import attr
from tfont.util.tracker import obj_setattr
from time import time
from typing import Any, Dict, Optional, Union
from uuid import uuid4


@attr.s(cmp=False, repr=False, slots=True)
class Point:
    x: Union[int, float] = attr.ib()
    y: Union[int, float] = attr.ib()
    type: Optional[str] = attr.ib(default=None)
    smooth: bool = attr.ib(default=False)

    _extraData: Optional[Dict] = attr.ib(default=None)

    _parent: Optional[Any] = attr.ib(default=None, init=False)
    selected: bool = attr.ib(default=False, init=False)

    def __repr__(self):
        if self.type is not None:
            more = ", %r" % self.type
            if self.smooth:
                more += ", smooth=%r" % self.smooth
        else:
            more = ""
        return "%s(%r, %r%s)" % (
            self.__class__.__name__, self.x, self.y, more)

    def __setattr__(self, key, value):
        try:
            path = self._parent
        except AttributeError:
            pass
        else:
            if path is not None and key[0] != "_":
                oldValue = getattr(self, key)
                if value != oldValue:
                    obj_setattr(self, key, value)
                    layer = path._parent
                    if key == "selected":
                        if value:
                            layer._selection.add(self)
                        else:
                            layer._selection.remove(self)
                        layer._selectedPaths = layer._selectionBounds = None
                    else:
                        glyph = layer._parent
                        if key == "x" or key == "y":
                            if self.selected:
                                layer._selectedPaths = \
                                    layer._selectionBounds = None
                            path._bounds = path._graphicsPath = \
                                layer._bounds = \
                                layer._closedGraphicsPath = \
                                layer._openGraphicsPath = None
                        glyph._lastModified = time()
                return
        obj_setattr(self, key, value)

    @property
    def extraData(self):
        extraData = self._extraData
        if extraData is None:
            extraData = self._extraData = {}
        return extraData

    @property
    def id(self):
        extraData = self.extraData
        try:
            return extraData["id"]
        except KeyError:
            extraData["id"] = id_ = str(uuid4())
            return id_

    @property
    def _id(self):
        return self.extraData.get("id", "")

    @_id.setter
    def _id(self, value):
        if value:
            self.extraData["id"] = value
        else:
            self.extraData.pop("id", None)

    @property
    def path(self):
        return self._parent
