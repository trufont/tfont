import attr
from copy import copy
from fontTools.misc import bezierTools
import pprint
from tfont.objects.point import Point
from tfont.util import bezierMath
from tfont.util.tracker import PathPointsList
from typing import Any, List, Optional, Tuple
from uuid import uuid4


@attr.s(cmp=False, repr=False, slots=True)
class Path:
    _points: List[Point] = attr.ib(default=attr.Factory(list))
    _id: str = attr.ib(default="")

    _bounds: Optional[Tuple] = attr.ib(default=None, init=False)
    _graphicsPath: Optional[Any] = attr.ib(default=None, init=False)
    _parent: Optional[Any] = attr.ib(default=None, init=False)

    def __attrs_post_init__(self):
        for point in self._points:
            point._parent = self

    def __bool__(self):
        return bool(self._points)

    def __repr__(self):
        name = self.__class__.__name__
        width = 80 - len(name) - 2
        return "%s(%s)" % (
            name, pprint.pformat(self._points, width=width).replace(
                "\n ", "\n  " + " " * len(name)))  # pad indent

    # __setattr__ not needed thus far

    @property
    def bounds(self):
        bounds = self._bounds
        if bounds is None and self._points:
            # TODO: we could have a rect type, in tools
            segments = self.segments
            left, bottom, right, top = segments[0].bounds
            for segment in segments:
                l, b, r, t = segment.bounds
                if l < left:
                    left = l
                if b < bottom:
                    bottom = b
                if r > right:
                    right = r
                if t > top:
                    top = t
            bounds = self._bounds = (left, bottom, right, top)
        return bounds

    @property
    def graphicsPath(self):
        graphicsPath = self._graphicsPath
        if graphicsPath is None:
            graphicsPath = self._graphicsPath = self.graphicsPathFactory()
        return graphicsPath

    @property
    def id(self):
        id_ = self._id
        if not id_:
            id_ = self._id = str(uuid4())
        return id_

    @property
    def open(self):
        points = self._points
        return not points or points[0].type == "move"

    @property
    def layer(self):
        return self._parent

    @property
    def points(self):
        return PathPointsList(self)

    @property
    def segments(self):
        return SegmentsList(self.points)

    @property
    def selected(self):
        return not any(not point.selected for point in self._points)

    @selected.setter
    def selected(self, value):
        for point in self._points:
            point.selected = value

    def close(self):
        points = self._points
        if not (points and self.open):
            return
        point = points.pop(0)
        point.smooth = False
        point.type = "line"
        points.append(point)
        self.points.applyChange()

    def reverse(self):
        points = self._points
        if not points:
            return
        start = points[0]
        type_ = start.type
        closed = type_ != "move"
        if closed:
            pivot = points.pop(-1)
            points.reverse()
            points.append(pivot)
            type_ = pivot.type
        else:
            points.reverse()
        for point in points:
            if point.type is not None:
                point.type, type_ = type_, point.type
        # notify
        self.points.applyChange()

    def setStartPoint(self, index):
        if self.open:
            # implement for endpoints?
            raise NotImplementedError
        points = self._points
        if not len(points) - index + 1:
            return
        end = points[:index+1]
        if end and end[-1].type is None:
            raise IndexError("index %r breaks a segment" % index)
        points[:] = points[index+1:] + end
        # notify
        self.points.applyChange()

    def transform(self, transformation, selectionOnly=False) -> bool:
        if not transformation:
            return
        changed = transformation.transformSequence(
            self._points, selectionOnly=selectionOnly)
        if changed:
            # notify
            self.points.applyChange()
        return changed


# TODO use abc superclass
@attr.s(cmp=False, repr=False, slots=True)
class SegmentsList:
    _points: PathPointsList = attr.ib()
    _segments: List[int] = attr.ib(default=attr.Factory(list), init=False)

    def __attrs_post_init__(self):
        points = self._points
        segments = self._segments
        start = 0
        for index, point in enumerate(points):
            if point.type is not None:
                segments.append(Segment(points, start, index))
                start = index + 1

    def __repr__(self):
        name = self.__class__.__name__
        width = 80 - len(name) - 2
        return "%s(%s)" % (
            name, pprint.pformat(self._segments, width=width).replace(
                "\n ", "\n  " + " " * len(name)))  # pad indent

    def __delitem__(self, index):
        points = self._points
        segments = self._segments
        seg = segments[index]
        stop = seg._end + 1
        del points[seg._start:stop]
        del segments[index]
        size = stop - seg._start
        for seg in segments[index:]:
            seg._start -= size
            seg._end -= size

    def __getitem__(self, index):
        return self._segments[index]

    def __iter__(self):
        return iter(self._segments)

    def __len__(self):
        return len(self._segments)

    def __reversed__(self):
        return reversed(self._segments)

    def iterfrom(self, start):
        segments = self._segments
        yield from segments[start:]
        yield from segments[:start]

    def splitSegment(self, index, t):
        segments = self._segments
        segment = segments[index]
        pts = segment.points
        pts_len = len(pts)
        if pts_len == 2:
            p1, p2 = pts
            p = Point(
                p1.x + (p2.x - p1.x) * t,
                p1.y + (p2.y - p1.y) * t,
                "line")
            self._points.insert(segment._start, p)
            newSegment = copy(segment)
            segments.insert(index, newSegment)
            for seg in segments[index+1:]:
                seg._start += 1
                seg._end += 1
        elif pts_len == 4:
            # inline
            p1, p2, p3, p4 = [(p.x, p.y) for p in pts]
            (p1, p2, p3, p4), (p5, p6, p7, p8) = bezierTools.splitCubicAtT(
                p1, p2, p3, p4, t)
            points = self._points
            start = segment._start
            p = points[start]
            p.x, p.y = p6
            p = points[start+1]
            p.x, p.y = p7
            p = points[start+2]
            p.x, p.y = p8
            points[start:start] = [
                Point(*p2), Point(*p3), Point(*p4, "curve", smooth=True)]
            newSegment = copy(segment)
            segments.insert(index, newSegment)
            for seg in segments[index+1:]:
                seg._start += 3
                seg._end += 3
        else:
            raise ValueError("unattended len %d" % pts_len)
        return newSegment


# inline the math code
@attr.s(cmp=False, repr=False, slots=True)
class Segment:
    _points: PathPointsList = attr.ib()
    _start: int = attr.ib()
    _end: int = attr.ib()

    def __repr__(self):
        return "%s(%d:%d, %r)" % (
            self.__class__.__name__, self._start, self._end, self.type)

    @property
    def bounds(self):
        points = self.points
        pts_len = len(points)
        if pts_len == 1:
            # move
            p = points[0]
            x, y = p.x, p.y
            return x, y, x, y
        elif pts_len == 2:
            # line
            p0, p1 = points[0], points[1]
            left, right = p0.x, p1.x
            if left > right:
                left, right = right, left
            bottom, top = p0.y, p1.y
            if bottom > top:
                bottom, top = top, bottom
            return left, bottom, right, top
        elif pts_len == 4:
            # curve
            return bezierMath.curveBounds(*points)
        else:
            # quads?
            raise NotImplementedError(
                "cannot compute bounds for %r segment" % self.type)

    @property
    def offCurves(self):
        return self._points[self._start:self._end]

    @property
    def offSelected(self) -> Optional[bool]:
        offCurves = self._points[self._start:self._end]
        if offCurves:
            return any(p.selected for p in offCurves)

    @property
    def onCurve(self):
        return self._points[self._end]

    @property
    def onSelected(self):
        return self._points[self._end].selected

    @property
    def path(self):
        return self._points._parent

    @property
    def penPoints(self):
        return self._points[self._start:self._end+1]

    @property
    def points(self):
        start = self._start - (self._points[self._end].type != "move")
        if start < 0:  # -:+ slice won't work
            return self._points[start:] + self._points[:self._end+1]
        return self._points[start:self._end+1]

    @property
    def selected(self):
        return self._points[self._end].selected and \
            self._points[self._start].selected

    @property
    def type(self):
        return self._points[self._end].type

    def intersectLine(self, x1, y1, x2, y2):
        points = self.points
        pts_len = len(points)
        if pts_len == 2:
            # line
            ret = bezierMath.lineIntersection(x1, y1, x2, y2, *points)
            if ret is not None:
                return [ret]
        elif pts_len == 4:
            # curve
            return bezierMath.curveIntersections(x1, y1, x2, y2, *points)
        # move, quads
        return []

    # ! this will invalidate the segments
    def intoCurve(self):
        points = self._points
        index = self._end
        onCurve = points[index]
        if onCurve.type == "line":
            start = points[self._start-1]
            points.insert(
                index, Point(
                    start.x + .65 * (onCurve.x - start.x),
                    start.y + .65 * (onCurve.y - start.y),
                ))
            points.insert(
                index, Point(
                    start.x + .35 * (onCurve.x - start.x),
                    start.y + .35 * (onCurve.y - start.y),
                ))
            onCurve.type = "curve"

    # ! this will invalidate the segments
    def intoLine(self):
        points = self._points
        end = self._end
        if points[end].type == "curve":
            start = self._start
            del points[start:end]
            points[start].type = "line"

    def projectPoint(self, x, y):
        points = self.points
        pts_len = len(points)
        if pts_len == 2:
            # line
            return bezierMath.lineProjection(x, y, *points)
        elif pts_len == 4:
            # curve
            return bezierMath.curveProjection(x, y, *points)
        return None
