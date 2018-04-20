import attr
import cattr
from collections.abc import Collection
from datetime import datetime
from io import StringIO
import rapidjson as json
import re
from tfont.objects.font import Font
from tfont.objects.misc import AlignmentZone, Transformation
from tfont.objects.path import Path
from tfont.objects.point import Point
from typing import Union

# lists that don't contain containers
_re_tuple = re.compile(r'\[\n(([^\[\]\{\n])+\n)*\]')


def _structure_Path(data, cls):
    points = []
    for element in data:
        if element.__class__ is list:
            point = Point(*element)
            points.append(point)
        else:
            point._extraData = element
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
        data.append(value)
        extraData = point._extraData
        if extraData:
            data.append(extraData)
    return data


class TFontConverter(cattr.Converter):
    __slots__ = "_font",

    version = 0

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # datetime
        dateFormat = '%Y-%m-%d %H:%M:%S'
        self.register_structure_hook(
            datetime, lambda d, _: datetime.strptime(d, dateFormat))
        self.register_unstructure_hook(
            datetime, lambda dt: dt.strftime(dateFormat))
        # Number disambiguation (json gave the right type already)
        self.register_structure_hook(Union[int, float], lambda d, _: d)

        structure_seq = lambda d, t: t(*d)
        # Alignment zone
        self.register_structure_hook(AlignmentZone, structure_seq)
        self.register_unstructure_hook(AlignmentZone, tuple)
        # Path
        self.register_structure_hook(Path, _structure_Path)
        self.register_unstructure_hook(Path, _unstructure_Path)
        # Transformation
        self.register_structure_hook(Transformation, structure_seq)
        self.register_unstructure_hook(Transformation, tuple)

    def open(self, path, font=None):
        with open(path, 'r') as file:
            d = json.load(file)
        assert self.version >= d.pop(".formatVersion")
        if font is not None:
            self._font = font
        return self.structure(d, Font)

    def save(self, font, path):
        d = self.unstructure(font)
        dump_s = json.dumps(d, indent=0)
        start = 0
        for m in _re_tuple.finditer(dump_s):
            if not start:
                out = StringIO()
            rstart, rend = m.start(), m.end()
            out.write(dump_s[start:rstart])
            out.write(dump_s[rstart:rend].replace('\n', ''))
            start = rend
        if start:
            out.write(dump_s[start:])
            s = out.getvalue()
        else:
            s = dump_s
        with open(path, 'w') as file:
            file.write(s)

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
            # remove underscore from private attrs
            if name[0] == "_":
                name = name[1:]
            rv[name] = dispatch(v.__class__)(v)
        return rv
