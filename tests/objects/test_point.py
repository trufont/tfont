from .base import (
    assert_bool, assert_dict, assert_number, assert_parent,
    assert_str)
import pytest
from tfont.objects.point import Point


def makePoint():
    return Point(10, 0, "line")


def test_reexport():
    from tfont.objects import Point as R_
    assert Point is R_


def test_ctor():
    with pytest.raises(TypeError):
        Point()
    with pytest.raises(TypeError):
        Point(10)
    Point(10, 0)
    Point(10, 0, type="line", smooth=True)
    with pytest.raises(TypeError):
        Point(10, 0, parent=object())
    with pytest.raises(TypeError):
        Point(10, 0, selected=True)


def test_x():
    assert_number(makePoint, "x", 10)


def test_y():
    assert_number(makePoint, "y", 0)


def test_type():
    assert_str(makePoint, "type", "line", optional=True)


def test_smooth():
    assert_bool(makePoint, "smooth", False)


def test_parent():
    assert_parent(makePoint)


def test_selected():
    assert_bool(makePoint, "selected", False)


def test_repr():
    inst = makePoint()
    assert repr(inst) == "Point(10, 0, 'line')"
    inst.smooth = True
    assert repr(inst) == "Point(10, 0, 'line', smooth=True)"
    inst.type = None
    assert repr(inst) == "Point(10, 0)"
    inst.type = "curve"
    assert repr(inst) == "Point(10, 0, 'curve', smooth=True)"


def test_setattr():
    raise NotImplementedError


def test_name():
    assert_str(makePoint, "name", None, optional=True)
