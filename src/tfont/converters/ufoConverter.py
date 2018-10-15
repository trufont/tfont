import cattr
from datetime import datetime
from tfont.objects.anchor import Anchor
from tfont.objects.component import Component
from tfont.objects.feature import FeatureHeader
from tfont.objects.font import Font
from tfont.objects.glyph import Glyph
from tfont.objects.guideline import Guideline
from tfont.objects.misc import AlignmentZone, Transformation
from tfont.objects.path import Path
from typing import Union
try:
    import ufoLib2
except ImportError:
    pass


class UFOConverter(cattr.Converter):
    __slots__ = ()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.register_structure_hook(Union[int, float], lambda d, _: d)

    def open(self, path, font=None):
        if font is None:
            font = Font()
        ufo = ufoLib2.Font(path)
        # font
        info = ufo.info
        if info.openTypeHeadCreated:
            try:
                font.date = datetime.strptime(
                    info.openTypeHeadCreated, "%Y/%m/%d %H:%M:%S")
            except ValueError:
                pass
        if info.familyName:
            font.familyName = info.familyName
        if info.copyright:
            font.copyright = info.copyright
        if info.openTypeNameDesigner:
            font.designer = info.openTypeNameDesigner
        if info.openTypeNameDesignerURL:
            font.designerURL = info.openTypeNameDesignerURL
        if info.openTypeNameManufacturer:
            font.manufacturer = info.openTypeNameManufacturer
        if info.openTypeNameManufacturerURL:
            font.manufacturerURL = info.openTypeNameManufacturerURL
        if info.unitsPerEm:
            font.unitsPerEm = info.unitsPerEm
        if info.versionMajor:
            font.versionMajor = info.versionMajor
        if info.versionMinor:
            font.versionMinor = info.versionMinor
        if ufo.lib:
            font._extraData = ufo.lib
        # features
        if ufo.features:
            font.featureHeaders.append(FeatureHeader("fea", ufo.features))
        # master
        master = font.selectedMaster
        if info.styleName:
            master.name = info.styleName
        for blues in (info.postscriptBlueValues, info.postscriptOtherBlues):
            for yMin, yMax in zip(blues[::2], blues[1::2]):
                master.alignmentZones.append(AlignmentZone(yMin, yMax-yMin))
        if info.postscriptStemSnapH:
            master.hStems = info.postscriptStemSnapH
        if info.postscriptStemSnapV:
            master.vStems = info.postscriptStemSnapV
        for g in ufo.guidelines:
            guideline = Guideline(
                x=g.x or 0, y=g.y or 0, angle=g.angle or 0, name=g.name or ""
            )
            # ufo guideline color and identifier are skipped
            master.guidelines.append(guideline)
        # note: unlike ufo, we store kerning in visual order. hard to convert
        # between the two (given that ltr and rtl pairs can be mixed)
        if ufo.kerning:
            hKerning = {}
            for (first, second), value in ufo.kerning.items():
                if first not in hKerning:
                    hKerning[first] = {}
                hKerning[first][second] = value
            master.hKerning = hKerning
        if info.ascender:
            master.ascender = info.ascender
        if info.capHeight:
            master.capHeight = info.capHeight
        if info.descender:
            master.descender = info.descender
        if info.italicAngle:
            master.italicAngle = info.italicAngle
        if info.xHeight:
            master.xHeight = info.xHeight
        # glyphs
        font._glyphs.clear()
        glyphs = font.glyphs
        for g in ufo:
            glyph = Glyph(g.name)
            glyphs.append(glyph)
            if g.unicodes:
                glyph.unicodes = ["%04X" % uniValue for uniValue in g.unicodes]
            # TODO assign kerning groups
            # layer
            layer = glyph.layerForMaster(None)
            layer.width = g.width
            layer.height = g.height
            lib = g.lib
            vertOrigin = lib.pop("public.verticalOrigin", None)
            if vertOrigin:
                layer.yOrigin = vertOrigin
            if lib:
                layer._extraData = lib
            # anchors
            anchors = layer.anchors
            for a in g.anchors:
                if not a.name:
                    continue
                anchors[a.name] = Anchor(a.x or 0, a.y or 0)
                # ufo color and identifier are skipped
            # components
            components = layer.components
            for c in g.components:
                component = Component(c.baseGlyph)
                if c.transformation:
                    component.transformation = Transformation(
                        *tuple(c.transformation))
                # ufo identifier is skipped
                components.append(component)
            # guidelines
            guidelines = layer.guidelines
            for g_ in g.guidelines:
                guideline = Guideline(g_.x or 0, g_.y or 0, g_.angle or 0)
                if g_.name:
                    guideline.name = g_.name
                # ufo color and identifier are skipped
                guidelines.append(guideline)
            # paths
            paths = layer.paths
            for c in self.unstructure(g.contours):
                pts = c.pop("_points")
                for p in pts:
                    name = p.pop("name", None)
                    ident = p.pop("identifier", None)
                    if name or ident:
                        p["extraData"] = d = {}
                        if name:
                            d["name"] = name
                        if ident:
                            d["id"] = ident
                while pts[-1]["type"] is None:
                    pts.insert(0, pts.pop())
                c["points"] = pts
                ident = c.pop("identifier", None)
                if ident:
                    c["id"] = ident
                path = self.structure(c, Path)
                paths.append(path)
            glyph._lastModified = None
        return font

    def save(self, font, path):
        pass

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

        return cl(**conv_obj)
