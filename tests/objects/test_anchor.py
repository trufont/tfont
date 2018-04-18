from .base import (
    assert_bool, assert_number, assert_parent, assert_str)
import pytest
from tfont.objects.anchor import Anchor


def makeAnchor():
    return Anchor("top", 10, 0)


def test_reexport():
    from tfont.objects import Anchor as R_
    assert Anchor is R_


def test_ctor():
    # we might want to allow empty ctors?
    # might be more practical for ui stuff
    with pytest.raises(TypeError):
        Anchor()
    with pytest.raises(TypeError):
        Anchor("top")
    with pytest.raises(TypeError):
        Anchor("top", 10)
    Anchor(name="top", x=10, y=0)
    with pytest.raises(TypeError):
        Anchor("top", 10, 0, parent=object())
    with pytest.raises(TypeError):
        Anchor("top", 10, 0, selected=True)


def test_name():
    assert_str(makeAnchor, "name", "top")


def test_x():
    assert_number(makeAnchor, "x", 10)


def test_y():
    assert_number(makeAnchor, "y", 0)


def test_parent():
    assert_parent(makeAnchor)


def test_selected():
    assert_bool(makeAnchor, "selected", False)


def test_repr():
    inst = makeAnchor()
    assert repr(inst) == "Anchor('top', 10, 0)"
    inst.name = "bottom"
    assert repr(inst) == "Anchor('bottom', 10, 0)"
    inst.x = 5
    assert repr(inst) == "Anchor('bottom', 5, 0)"
    inst.y = 2.5
    assert repr(inst) == "Anchor('bottom', 5, 2.5)"


def test_setattr():
    raise NotImplementedError
