from .base import assert_bool, assert_parent, assert_str
import pytest
from tfont.objects.component import Component
from tfont.objects.misc import Transformation


def makeComponent():
    return Component("A")


def test_reexport():
    from tfont.objects import Component as R_
    assert Component is R_


def test_ctor():
    with pytest.raises(TypeError):
        Component()
    Component("A", Transformation())
    Component(glyphName="A", transformation=Transformation())
    with pytest.raises(TypeError):
        Component("A", Transformation(), parent=object())
    with pytest.raises(TypeError):
        Component("A", Transformation(), selected=True)


def test_glyphName():
    assert_str(makeComponent, "glyphName", "A")


def test_transformation():
    component = makeComponent()
    assert component.transformation == Transformation()
    component.transformation = t = Transformation(2, 0, 0, 2, 1, 0)
    assert component.transformation == t


def test_bounds():
    raise NotImplementedError


def test_graphicsPath():
    raise NotImplementedError


def test_parent():
    assert_parent(makeComponent)


def test_selected():
    assert_bool(makeComponent, "selected", False)


def test_repr():
    inst = makeComponent()
    assert repr(inst) == "Component('A', Transformation(1, 0, 0, 1, 0, 0))"
    inst.glyphName = "Z"
    assert repr(inst) == "Component('Z', Transformation(1, 0, 0, 1, 0, 0))"
    inst.transformation = Transformation(5, 4, 3, 2, 1, 0)
    assert repr(inst) == "Component('Z', Transformation(5, 4, 3, 2, 1, 0))"


def test_setattr():
    raise NotImplementedError


def test_glyph():
    raise NotImplementedError


def test_decompose():
    raise NotImplementedError


def test_transform():
    raise NotImplementedError
