import attr
from tfont.objects.misc import Transformation, obj_setattr
from time import time
from typing import Optional


@attr.s(cmp=False, repr=False, slots=True)
class Component:
    glyphName: str = attr.ib()
    transformation: Transformation = attr.ib(default=attr.Factory(
        Transformation))

    _parent: Optional[object] = attr.ib(default=None, init=False)
    selected: bool = attr.ib(default=False, init=False)

    def __repr__(self):
        return "%s(%r, %r)" % (
            self.__class__.__name__, self.glyphName, self.transformation)

    def __setattr__(self, key, value):
        try:
            layer = self._parent
        except AttributeError:
            pass
        else:
            if layer is not None and key[0] != "_":
                oldValue = getattr(self, key)
                # the bypass means we don't sustain idempotence on the
                # transformation key, though it doesn't matter so much
                if key == "transformation" or value != oldValue:
                    obj_setattr(self, key, value)
                    if key == "selected":
                        if value:
                            layer._selection.add(self)
                        else:
                            layer._selection.remove(self)
                        layer._selectionBounds = None
                    else:
                        glyph = layer._parent
                        layer._bounds = layer._selectionBounds = None
                        glyph._lastModified = time()
                return
        obj_setattr(self, key, value)

    @property
    def bounds(self):
        try:
            l, b, r, t = self.layer.bounds
        except (AttributeError, TypeError):
            return
        transformation = self.transformation
        l, b, r, t = (l * transformation.xScale +
                      b * transformation.yxScale + transformation.xOffset,
                      b * transformation.yScale +
                      l * transformation.xyScale + transformation.yOffset,
                      r * transformation.xScale +
                      t * transformation.yxScale + transformation.xOffset,
                      t * transformation.yScale +
                      r * transformation.xyScale + transformation.yOffset)
        if l > r:
            l, r = r, l
        if b > t:
            t, b = b, t
        return l, b, r, t

    @property
    def closedGraphicsPath(self):
        return self.closedGraphicsPathFactory()

    @property
    def glyph(self):
        try:
            return self._parent._parent._parent.glyphForName(self.glyphName)
        except (AttributeError, KeyError):
            pass

    @property
    def layer(self):
        layer = self._parent
        try:
            return layer._parent._parent.glyphForName(
                self.glyphName).layerForMaster(layer.masterName)
        except (AttributeError, KeyError):
            pass

    @property
    def openGraphicsPath(self):
        return self.openGraphicsPathFactory()

    @property
    def origin(self):
        return self.transformation.transform(0, 0)

    def decompose(self):
        raise NotImplementedError
