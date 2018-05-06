import attr
from tfont.util.tracker import obj_setattr
from typing import Optional


@attr.s(cmp=False, repr=False, slots=True)
class Feature:
    tag: str = attr.ib(default="")
    content: str = attr.ib(default="")

    _parent: Optional[object] = attr.ib(default=None, init=False)

    def __repr__(self):
        return "%s(%r, %r)" % (self.__class__.__name__, self.tag, self.content)

    def __setattr__(self, key, value):
        try:
            font = self._parent
        except AttributeError:
            pass
        else:
            if font is not None and key[0] != "_":
                oldValue = getattr(self, key)
                if value != oldValue:
                    if key == "tag":
                        font.features[value] = self
                        return
                    obj_setattr(self, key, value)
                    font._layoutEngine = None
                return
        obj_setattr(self, key, value)

    def __str__(self):
        tag = self.tag
        return "feature %s {\n%s\n} %s;" % (tag, self.content, tag)

    @property
    def font(self):
        return self._parent


@attr.s(cmp=False, repr=False, slots=True)
class FeatureClass:
    name: str = attr.ib(default="")
    content: str = attr.ib(default="")

    _parent: Optional[object] = attr.ib(default=None, init=False)

    def __repr__(self):
        return "%s(%r, %r)" % (
            self.__class__.__name__, self.name, self.content)

    def __setattr__(self, key, value):
        try:
            font = self._parent
        except AttributeError:
            pass
        else:
            if font is not None and key[0] != "_":
                oldValue = getattr(self, key)
                if value != oldValue:
                    if key == "name":
                        font.featureClasses[value] = self
                        return
                    obj_setattr(self, key, value)
                    font._layoutEngine = None
                return
        obj_setattr(self, key, value)

    def __str__(self):
        return "@%s = [%s];" % (self.name, self.content)

    @property
    def font(self):
        return self._parent


@attr.s(cmp=False, repr=False, slots=True)
class FeatureHeader:
    description: str = attr.ib(default="")
    content: str = attr.ib(default="")

    _parent: Optional[object] = attr.ib(default=None, init=False)

    def __repr__(self):
        return "%s(%r, %r)" % (
            self.__class__.__name__, self.description, self.content)

    def __setattr__(self, key, value):
        try:
            font = self._parent
        except AttributeError:
            pass
        else:
            if font is not None and key[0] != "_":
                oldValue = getattr(self, key)
                if value != oldValue:
                    obj_setattr(self, key, value)
                    font._layoutEngine = None
                return
        obj_setattr(self, key, value)

    def __str__(self):
        return str(self.content)

    @property
    def font(self):
        return self._parent
