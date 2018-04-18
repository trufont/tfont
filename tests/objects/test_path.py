from .base import assert_parent
import pytest
from tfont.objects.path import Path, SegmentsList
from tfont.objects.point import Point


def makePath():
    return Path([Point(10, 0, "move"), Point(0, 10, "line")])


def test_reexport():
    from tfont.objects import Path as R_
    assert Path is R_


def test_ctor():
    Path()
    Path(points=[Point(10, 0, "move")])
    with pytest.raises(TypeError):
        Path([Point(10, 0, "move")], parent=object())
    #with pytest.raises(TypeError):
    #    Path([Point(10, 0, "move")], selected=True)


def test_children_parent():
    path = makePath()
    for point in path:
        assert point.parent == path


def test_repr():
    inst = makePath()
    assert repr(inst) == "Path([Point(10, 0, 'move'), Point(0, 10, 'line')])"
    for i in range(2):
        coord = 10*(i+1)
        inst.append(Point(coord, coord, 'line'))
    assert repr(inst) == "Path([Point(10, 0, 'move'),\n      Point(0, 10, 'line'),\n      Point(10, 10, 'line'),\n      Point(20, 20, 'line')])"


def test_bounds():
    raise NotImplementedError


def test_graphicsPath():
    raise NotImplementedError


def test_parent():
    assert_parent(makePath)


def test_points():
    path = makePath()
    tracker = path.points
    assert tracker._sequence == path._points
    point = Point(11, 3)
    tracker.append(point)
    assert point.parent == path


def test_segments():
    path = makePath()
    assert path.segments == SegmentsList(path)


def test_selected():
    raise NotImplementedError


def test_reverse():
    raise NotImplementedError


def test_setStartPoint():
    raise NotImplementedError


def test_transform():
    raise NotImplementedError


# TODO test SegmentsList/Segment
