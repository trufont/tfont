import cattr
from collections.abc import Collection
from datetime import datetime
from functools import partial
import rapidjson as json
from rapidjson import RawJSON, dumps
from tfont.objects.anchor import Anchor
from tfont.objects.axis import Axis
from tfont.objects.feature import Feature, FeatureClass
from tfont.objects.font import Font
from tfont.objects.layer import Layer
from tfont.objects.master import Master
from tfont.objects.misc import AlignmentZone, Transformation
from tfont.objects.path import Path
from tfont.objects.point import Point
from typing import Dict, Union


# TODO we should have a custom type for caching dicts
def _structure_seq_dict(self, attr, data, type_):
    cls = type_.__args__[1]  # dict key type
    return dict((e[attr], self.structure(e, cls)) for e in data)


def _structure_Path(data, cls):
    points = []
    for element in data:
        if element.__class__ is dict:
            point._extraData = element
        else:
            point = Point(*element)
            points.append(point)
    return cls(points)


def _unstructure_Path(path):
    data = []
    for point in path._points:
        ptType = point.type
        if ptType is not None:
            if point.smooth:
                value = (point.x, point.y, ptType, True)
            else:
                value = (point.x, point.y, ptType)
        else:
            value = (point.x, point.y)
        data.append(RawJSON(dumps(value)))
        extraData = point._extraData
        if extraData:
            data.append(extraData)
    return data


def _unstructure_Path_base(path):
    data = []
    for point in path._points:
        ptType = point.type
        if ptType is not None:
            if point.smooth:
                value = (point.x, point.y, ptType, True)
            else:
                value = (point.x, point.y, ptType)
        else:
            value = (point.x, point.y)
        data.append(value)
        extraData = point._extraData
        if extraData:
            data.append(extraData)
    return data


class TFontConverter(cattr.Converter):
    __slots__ = "_font", "_indent"

    version = 0

    def __init__(self, indent=0, **kwargs):
        super().__init__(**kwargs)
        self._indent = indent

        # datetime
        dateFormat = '%Y-%m-%d %H:%M:%S'
        self.register_structure_hook(
            datetime, lambda d, _: datetime.strptime(d, dateFormat))
        self.register_unstructure_hook(
            datetime, lambda dt: dt.strftime(dateFormat))
        # Number disambiguation (json gave the right type already)
        self.register_structure_hook(Union[int, float], lambda d, _: d)

        structure_seq = lambda d, t: t(*d)
        if indent is None:
            unstructure_seq = lambda o: tuple(o)
        else:
            unstructure_seq = lambda o: RawJSON(dumps(tuple(o)))
            self.register_unstructure_hook(tuple, unstructure_seq)
        # Alignment zone
        self.register_structure_hook(AlignmentZone, structure_seq)
        self.register_unstructure_hook(AlignmentZone, unstructure_seq)
        # Path
        self.register_structure_hook(Path, _structure_Path)
        if indent is None:
            self.register_unstructure_hook(Path, _unstructure_Path_base)
        else:
            self.register_unstructure_hook(Path, _unstructure_Path)
        # Transformation
        self.register_structure_hook(Transformation, structure_seq)
        self.register_unstructure_hook(Transformation, unstructure_seq)

        unstructure_seq_dict = lambda d: list(
            self.unstructure(v) for v in d.values())
        structure_dict_name = partial(_structure_seq_dict, self, "name")
        structure_dict_tag = partial(_structure_seq_dict, self, "tag")
        # Anchor
        self.register_structure_hook(Dict[str, Anchor], structure_dict_name)
        self.register_unstructure_hook(Dict[str, Anchor], unstructure_seq_dict)
        # Axis
        self.register_structure_hook(Dict[str, Axis], structure_dict_tag)
        self.register_unstructure_hook(Dict[str, Axis], unstructure_seq_dict)
        # Feature
        self.register_structure_hook(Dict[str, Feature], structure_dict_tag)
        self.register_unstructure_hook(
            Dict[str, Feature], unstructure_seq_dict)
        # FeatureClass
        self.register_structure_hook(
            Dict[str, FeatureClass], structure_dict_name)
        self.register_unstructure_hook(
            Dict[str, FeatureClass], unstructure_seq_dict)
        # Master
        self.register_structure_hook(Dict[str, Master], structure_dict_name)
        self.register_unstructure_hook(Dict[str, Master], unstructure_seq_dict)

    def open(self, path, font=None):
        with open(path, 'r') as file:
            d = json.load(file)
        assert self.version >= d.pop(".formatVersion")
        if font is not None:
            self._font = font
        return self.structure(d, Font)

    def save(self, font, path):
        d = self.unstructure(font)
        with open(path, 'w') as file:
            json.dump(d, file, indent=self._indent)

    def structure_attrs_fromdict(self, obj, cl):
        conv_obj = obj.copy()  # Dict of converted parameters.
        dispatch = self._structure_func.dispatch
        for a in cl.__attrs_attrs__:
            # We detect the type by metadata.
            type_ = a.type
            if type_ is None:
                # No type.
                continue
            name = a.name
            if name[0] == "_":
                name = name[1:]
            try:
                val = obj[name]
            except KeyError:
                continue
            conv_obj[name] = dispatch(type_)(val, type_)

        if cl is Font:
            try:
                font = self._font
                font.__init__(**conv_obj)
                del self._font
                return font
            except:
                pass
        return cl(**conv_obj)

    def unstructure_attrs_asdict(self, obj):
        cls = obj.__class__
        attrs = cls.__attrs_attrs__
        dispatch = self._unstructure_func.dispatch
        # add version stamp
        if cls is Font:
            rv = {".formatVersion": self.version}
        else:
            rv = {}
        override = cls is Font or cls is Layer
        for a in attrs:
            # skip internal attrs
            if not a.init:
                continue
            name = a.name
            v = getattr(obj, name)
            if not v:
                # skip attrs that have trivial default values set
                if v == a.default:
                    continue
                # skip empty collections
                if isinstance(v, Collection):
                    continue
            # force our specialized types overrides
            type_ = v.__class__
            if override:
                t = a.type
                try:
                    if issubclass(t.__origin__, dict) and t.__args__[0] is str:
                        type_ = t
                except (AttributeError, TypeError):
                    pass
            # remove underscore from private attrs
            if name[0] == "_":
                name = name[1:]
            rv[name] = dispatch(type_)(v)
        return rv
