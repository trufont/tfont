import attr
from datetime import datetime
from functools import partial
from tfont.objects.point import Point
from tfont.objects.anchor import Anchor
from tfont.objects.component import Component
from tfont.objects.guideline import Guideline
from tfont.objects.misc import Transformation, obj_setattr
from tfont.objects.path import Path
from tfont.util.slice import slicePaths
from tfont.util.tracker import (
    LayerAnchorsDict, LayerComponentsList, LayerGuidelinesList, LayerPathsList)
from time import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import logging


def squaredDistance(x1, y1, item):
    x2, y2 = item
    dx, dy = x2 - x1, y2 - y1
    return dx*dx + dy*dy

@attr.s(cmp=False, repr=False, slots=True)
class Layer:
    masterName: str = attr.ib(default="")
    _name: str = attr.ib(default="")
    location: Optional[Dict[str, int]] = attr.ib(default=None)

    width: Union[int, float] = attr.ib(default=600)
    # should default to ascender+descender and only be stored if different from
    # that value -- add a None value for it and a property?
    height: Union[int, float] = attr.ib(default=0)
    yOrigin: Optional[Union[int, float]] = attr.ib(default=None)

    _anchors: Dict[str, Anchor] = attr.ib(default=attr.Factory(dict))
    _components: List[Component] = attr.ib(default=attr.Factory(list))
    _guidelines: List[Guideline] = attr.ib(default=attr.Factory(list))
    _paths: List[Path] = attr.ib(default=attr.Factory(list))

    # Color format: RGBA8888.
    color: Optional[Tuple[int, int, int, int]] = attr.ib(default=None)
    _extraData: Optional[Dict] = attr.ib(default=None)

    _bounds: Optional[Tuple] = attr.ib(default=None, init=False)
    _closedGraphicsPath: Optional[Any] = attr.ib(default=None, init=False)
    _openGraphicsPath: Optional[Any] = attr.ib(default=None, init=False)
    _parent: Optional[Any] = attr.ib(default=None, init=False)
    _selectedPaths: Optional[Any] = attr.ib(default=None, init=False)
    _selection: Set = attr.ib(default=attr.Factory(set), init=False)
    _selectionBounds: Optional[Tuple] = attr.ib(default=None, init=False)
    _visible: bool = attr.ib(default=False, init=False)

    # For undo/redo
    _undo: Optional[Dict] = attr.ib(default=None, init=False)

    def __attrs_post_init__(self):
        for anchor in self._anchors.values():
            anchor._parent = self
        for component in self._components:
            component._parent = self
        for guideline in self._guidelines:
            guideline._parent = self
        for path in self._paths:
            path._parent = self

    def __bool__(self):
        return bool(self._paths or self._components)

    # add __lt__ to display layers ordered

    def __repr__(self):
        try:
            more = ", glyph %r%s" % (
                self._parent.name, " master" * self.masterLayer)
        except AttributeError:
            more = ""
        return "%s(%r, %d paths%s)" % (
            self.__class__.__name__, self.name, len(self._paths), more)

    def __setattr__(self, key, value):
        try:
            glyph = self._parent
        except AttributeError:
            pass
        else:
            if glyph is not None and key[0] != "_":
                oldValue = getattr(self, key)
                if value != oldValue:
                    obj_setattr(self, key, value)
                    glyph._lastModified = time()
                return
        obj_setattr(self, key, value)

    @property
    def anchors(self):
        return LayerAnchorsDict(self)

    @property
    def bottomMargin(self):
        bounds = self.bounds
        if bounds is not None:
            value = bounds[1]
            if self.yOrigin is not None:
                value -= self.yOrigin - self.height
            return value
        return None

    @bottomMargin.setter
    def bottomMargin(self, value):
        bounds = self.bounds
        if bounds is None:
            return
        oldValue = bounds[1]
        if self.yOrigin is not None:
            oldValue -= self.yOrigin - self.height
        else:
            self.yOrigin = self.height
        self.height += value - oldValue

    @property
    def bounds(self):
        bounds = self._bounds
        left = None
        if bounds is None:
            # TODO: we could have a rect type, in tools
            paths = self._paths
            for path in paths:
                l, b, r, t = path.bounds
                if left is None:
                    left, bottom, right, top = l, b, r, t
                else:
                    if l < left:
                        left = l
                    if b < bottom:
                        bottom = b
                    if r > right:
                        right = r
                    if t > top:
                        top = t
            if left is not None:
                bounds = self._bounds = (left, bottom, right, top)
        # we can't stash component bounds, we aren't notified when it changes
        for component in self._components:
            l, b, r, t = component.bounds
            if left is None:
                if bounds is not None:
                    left, bottom, right, top = bounds
                else:
                    left, bottom, right, top = l, b, r, t
                    continue
            if l < left:
                left = l
            if b < bottom:
                bottom = b
            if r > right:
                right = r
            if t > top:
                top = t
        if left is not None:
            return (left, bottom, right, top)
        return bounds

    @property
    def closedComponentsGraphicsPath(self):
        return self.closedComponentsGraphicsPathFactory()

    @property
    def closedGraphicsPath(self):
        graphicsPath = self._closedGraphicsPath
        if graphicsPath is None:
            graphicsPath = self._closedGraphicsPath = \
                self.closedGraphicsPathFactory()
        return graphicsPath

    @property
    def components(self):
        return LayerComponentsList(self)

    @property
    def extraData(self):
        extraData = self._extraData
        if extraData is None:
            extraData = self._extraData = {}
        return extraData

    @property
    def font(self):
        glyph = self._parent
        if glyph is not None:
            return glyph._parent
        return None

    @property
    def glyph(self):
        return self._parent

    @property
    def guidelines(self):
        return LayerGuidelinesList(self)

    @property
    def leftMargin(self):
        bounds = self.bounds
        if bounds is not None:
            return bounds[0]
        return None

    @leftMargin.setter
    def leftMargin(self, value):
        bounds = self.bounds
        if bounds is None:
            return
        delta = value - bounds[0]
        self.transform(Transformation(xOffset=delta))
        self.width += delta

    @property
    def master(self):
        try:
            return self._parent._parent._masters[self.masterName]
        except (AttributeError, KeyError):
            pass
        return None

    @property
    def masterLayer(self):
        return self.masterName and not self._name

    @property
    def name(self):
        if self.masterLayer:
            return self.master.name
        return self._name

    @name.setter
    def name(self, value):
        self._name = value

    @property
    def openComponentsGraphicsPath(self):
        return self.openComponentsGraphicsPathFactory()

    @property
    def openGraphicsPath(self):
        graphicsPath = self._openGraphicsPath
        if graphicsPath is None:
            graphicsPath = self._openGraphicsPath = \
                self.openGraphicsPathFactory()
        return graphicsPath

    @property
    def paths(self):
        return LayerPathsList(self)

    @property
    def rightMargin(self):
        bounds = self.bounds
        if bounds is not None:
            return self.width - bounds[2]
        return None

    @rightMargin.setter
    def rightMargin(self, value):
        bounds = self.bounds
        if bounds is None:
            return
        self.width = bounds[2] + value

    @property
    def selectedPaths(self):
        paths = self._selectedPaths
        if paths is None:
            paths = self._selectedPaths = self.selectedPathsFactory()
        return paths

    @property
    def selection(self):
        return self._selection

    @property
    def selectionBounds(self):
        selectionBounds = self._selectionBounds
        left = None
        if selectionBounds is None:
            for element in self._selection:
                if element.__class__ is Component:
                    # we can't stash component bounds, we aren't notified when
                    # it changes
                    continue
                x, y = element.x, element.y
                if left is None:
                    left, bottom, right, top = x, y, x, y
                else:
                    if x < left:
                        left = x
                    elif x > right:
                        right = x
                    if y < bottom:
                        bottom = y
                    elif y > top:
                        top = y
            if left is not None:
                selectionBounds = self._selectionBounds = (
                    left, bottom, right, top)
        for component in self._components:
            if component.selected:
                l, b, r, t = component.bounds
                if left is None:
                    if selectionBounds is not None:
                        left, bottom, right, top = selectionBounds
                    else:
                        left, bottom, right, top = l, b, r, t
                        continue
                if l < left:
                    left = l
                if b < bottom:
                    bottom = b
                if r > right:
                    right = r
                if t > top:
                    top = t
        if left is not None:
            return (left, bottom, right, top)
        return selectionBounds

    @property
    def topMargin(self):
        bounds = self.bounds
        if bounds is not None:
            value = -bounds[3]
            if self.yOrigin is not None:
                value += self.yOrigin
            else:
                value += self.height
            return value
        return None

    @topMargin.setter
    def topMargin(self, value):
        bounds = self.bounds
        if bounds is None:
            return
        top = bounds[3]
        oldValue = -top
        if self.yOrigin is not None:
            oldValue += self.yOrigin
        else:
            oldValue += self.height
        self.yOrigin = top + value
        self.height += value - oldValue

    @property
    def visible(self):
        if self.masterLayer:
            return self.master.visible
        return self._visible

    @visible.setter
    def visible(self, value):
        if self.masterLayer:
            self.master.visible = value
        else:
            self._visible = value

    def clearSelection(self):
        for element in list(self._selection):
            element.selected = False
        for guideline in self.master.guidelines:
            guideline.selected = False

    def copy(self):
        global TFontConverter
        try:
            TFontConverter
        except NameError:
            from tfont.converters.tfontConverter import TFontConverter
        conv = TFontConverter(indent=None)
        l = conv.structure(conv.unstructure(self), self.__class__)
        l._name = datetime.now().strftime("%b %d %y {} %H:%M").format("–")
        l.visible = False
        return l

    def decomposeComponents(self):
        for component in self._components:
            component.decompose()

    # components=False?
    def intersectLine(self, x1, y1, x2, y2):
        intersections = [(x1, y1), (x2, y2)]
        intersections_append = intersections.append
        for path in self._paths:
            for segment in path.segments:
                for x, y, _ in segment.intersectLine(x1, y1, x2, y2):
                    intersections_append((x, y))
        intersections.sort(key=partial(squaredDistance, x1, y1))
        return intersections

    def sliceLine(self, x1, y1, x2, y2):
        paths = self._paths
        if not paths:
            return
        newPaths = slicePaths(self, x1, y1, x2, y2)
        if not newPaths:
            return
        self._paths = newPaths
        # notify
        self.paths.applyChange()

    def transform(self, transformation, selectionOnly=False) -> bool:
        changed = False
        anchors = self._anchors
        if anchors:
            if transformation.transformSequence(
                    anchors, selectionOnly=selectionOnly):
                self.anchors.applyChange()
                changed = True
        for component in self._components:
            doTransform = not selectionOnly or component.selected
            changed |= doTransform
            if doTransform:
                component.transformation.concat(transformation)
        for path in self._paths:
            changed |= path.transform(
                transformation, selectionOnly=selectionOnly)
        return changed

    def snapshot(self, paths=False, anchors=False, components=False, guidelines=False):
        """serializes (parts) of the layer in order the restore the layer to that state later on.
        Returns a lambda that performs this state restoration."""
        from tfont.converters.tfontConverter import TFontConverter as TFC
        tfc = TFC(indent=None) # indent=None means: "Do not dump JSON, but just plain Dict"
        snaps = []
        if paths:
            snaps.append(('paths', tfc.unstructure(self._paths)))
        if anchors:
            # unstructure Anchors as List of values,
            # one of these values is the name of anchor -- using as key 
            # see clipboard util/clipboard.py
            # -------------------------------
            snaps.append(('anchors', tfc.unstructure([value for value in self._anchors.values()])))
        if guidelines:
            snaps.append(('guidelines', tfc.unstructure(self._guidelines)))
        if components:
            snaps.append(('components', tfc.unstructure(self._components)))
        if self.selection:
            sel = tfc.unstructure(self._selection)
            logging.debug("LAYER: selection snapshot - selection is: {}".format(list(sel)))
            snaps.append(('selection',list(sel)))
        return snaps

    def setToSnapshot(self, snaps):
        from tfont.converters.tfontConverter import TFontConverter as TFC
        tfc = TFC(indent=None)
        for snap in snaps:
            name, unstructured = snap
            if name == 'paths':
                self.paths[:] = [] # this removes the deleted points from the layer.selection
                # The line below will also add the new point to the layer.selection
                self.paths[:] = tfc.structure(unstructured, List[Path])
                self.paths.applyChange()
            elif name == 'anchors':
                self.anchors.clear()
                self.anchors.update({value.name:value for value in tfc.structure(unstructured, List[Anchor])})
                # for value in self.anchors.values:
                #     value.selected = True
                self.anchors.applyChange()
            elif name == 'guidelines':
                self.guidelines[:] = tfc.structure(unstructured, List[Guideline])
                # for guideline in self.guidelines:
                #     guideline.selected = True
                self.guidelines.applyChange()
            elif name == 'components':
                self.components[:] = tfc.structure(unstructured, List[Guideline])
                # for comp in self.components:
                #     comp.selected = True
                self.components.applyChange()
            elif name == 'selection': 
                logging.debug("LAYER: setToSnapshot - selection before is: {}".format(self.selection))
                self.selection.clear()
                selection = tfc.structure(unstructured, List[Any]) 
                
                # update _parent field
                for obj in selection:
                    logging.debug("LAYER: setToSnapshot - obj is {}".format(obj))
                    try:
                        if isinstance(obj, Point):
                            logging.debug("LAYER: setToSnapshot - is a point")
                            # for path in self._paths:
                            #     for pt in path._points:
                            for pt in (pt for path in self._paths for pt in path._points):
                                if pt.x == obj.x and pt.y == obj.y and pt.type == obj.type:
                                    self._selection.add(pt)
                                    logging.debug("LAYER: setToSnapshot - find a point to update")
                                    break 

                        elif isinstance(obj, Path):
                            logging.debug("LAYER: setToSnapshot - is a path") 
                            for path in self._paths:
                                if obj == path:
                                    self._selection.add(path)
                                    logging.debug("LAYER: setToSnapshot - find a path to update")
                                    break 

                        elif isinstance(obj, (Anchor, Guideline, Component)):
                            raise NotImplementedError

                    except Exception as e:
                        logging.error("LAYER: setToSnapshot - error iterate obj from selection -> {}".format(str(e)))
                logging.debug("LAYER: setToSnapshot - selection after is: {}".format(self.selection))

    def beginUndo(self, group_name: str, paths=True, anchors=True, components=True, guidelines=True):
        #FIXME: if self._undo is not None, then log it / throw an exception
        if not self._undo:
            self._undo = {}
        if group_name not in self._undo:
            self._undo[group_name] = self.snapshot(paths, anchors, components, guidelines)

    def endUndo(self, group_name: str):
        if self._undo is None or group_name not in self._undo: 
            raise KeyError("LAYER: endUndoGroup -> Key error {} does not exist".format(group_name))

        # get all saved parts (as name)
        names = [name for (name, snap) in self._undo[group_name]]
        paths = 'paths' in names
        anchors = 'anchors' in names
        guidelines = 'guidelines' in names
        components = 'components' in names

        redoSnaps = self.snapshot(paths, anchors, components, guidelines)
        redoAction = lambda: self.setToSnapshot(redoSnaps)
        undoSnaps = self._undo[group_name] # we can't put "self._undo" in the lambda below since it is set to None just after
        undoAction = lambda: self.setToSnapshot(undoSnaps)
        
        # end of save for this key 
        del self._undo[group_name]
        return undoAction, redoAction, (undoSnaps, redoSnaps)  
