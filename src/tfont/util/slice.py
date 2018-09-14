from copy import copy
from functools import partial
from tfont.objects.path import Path


def bytwo(iterable):
    i = iter(iterable)
    try:
        while True:
            yield next(i), next(i)
    except StopIteration:
        pass


def makePath(endSegment, segmentsMap, path=None, targetSegment=None):
    if path is None:
        path = Path()
    if targetSegment is None:
        targetSegment = endSegment
    iterator = segmentsMap.pop(targetSegment)
    points = path._points
    point = copy(next(iterator).onCurve)
    point.smooth = False
    point.type = "line"
    point._parent = path
    points.append(point)
    for segment in iterator:
        isJump = segment in segmentsMap
        isLast = segment is endSegment
        for point in segment.penPoints:
            # original segment will be trashed so we only need to
            # copy the overlapping section
            if isJump or isLast and point.type is not None:
                point = copy(point)
                point.smooth = False
            point._parent = path
            points.append(point)
        if isLast:
            break
        elif isJump:
            makePath(endSegment, segmentsMap, path, segment)
            break
    return path


def segmentSqDist(x1, y1, item):
    p2 = item[0].onCurve
    dx, dy = p2.x - x1, p2.y - y1
    return dx*dx + dy*dy


def slicePaths(layer, x1, y1, x2, y2):
    paths = layer._paths
    # cut and store new segments
    # TODO: handle open contours
    pathSegments = []
    splitSegments = []
    for path in paths:
        segments = path.segments
        index = 0
        while index < len(segments):
            segment = segments[index]
            intersections = segment.intersectLine(x1, y1, x2, y2)
            if not intersections:
                index += 1
                continue
            # TODO: handle more
            intersection = intersections[0]
            splitSegments.append((
                segments.splitSegment(index, intersection[-1]),
                segments.iterfrom(index)
            ))
            index += 2
        pathSegments.append(segments)
    size = len(splitSegments)
    if size < 2:
        return None
    # TODO: use bw area for odd len elision
    # -- a temp solution could use graphicsPath.Contains
    # won't work well for overlapping paths though
    if size % 2:
        del splitSegments[-1]
    # sort newSegments by distance of their onCurve from (x1, y1)
    # and build the graph of pairs
    segmentsMap = {}
    for (segA, iterA), (segB, iterB) in bytwo(
            sorted(splitSegments, key=partial(segmentSqDist, x1, y1))):
        segmentsMap[segA] = iterB
        segmentsMap[segB] = iterA
    # draw the new paths
    newPaths = []
    for path, segments in zip(paths, pathSegments):
        newPath = None
        for segment in segments:
            if segment in segmentsMap:
                newPath = makePath(segment, segmentsMap)
                newPath._parent = layer
                newPaths.append(newPath)
        if newPath is None:
            newPaths.append(path)
    return newPaths
