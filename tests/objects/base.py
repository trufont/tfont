import pytest


def assert_bool(factory, attr, default):
    inst = factory()
    assert getattr(inst, attr) is default

    setattr(inst, attr, True)
    assert getattr(inst, attr) is True


def assert_dict(factory, attr, optional=False):
    inst = factory()
    if optional:
        assert getattr(inst, "_" + attr) is None
    d = getattr(inst, attr)
    assert isinstance(d, dict)
    # assumes readonly attr
    with pytest.raises(AttributeError):
        setattr(inst, attr, d)
    d["1"] = 1
    assert getattr(inst, attr) == d


def assert_number(factory, attr, default):
    inst = factory()
    assert getattr(inst, attr) == default
    setattr(inst, attr, 5)
    assert getattr(inst, attr) == 5
    setattr(inst, attr, .25)
    assert getattr(inst, attr) == .25


def assert_parent(factory):
    inst = factory()
    assert inst.parent is inst._parent is None
    parent = object()

    with pytest.raises(AttributeError):
        inst.parent = parent

    inst._parent = parent
    assert inst.parent == inst._parent == parent


def assert_str(factory, attr, default, optional=False):
    inst = factory()
    assert getattr(inst, attr) == default
    setattr(inst, attr, "line")
    assert getattr(inst, attr) == "line"
    if optional:
        setattr(inst, attr, None)
        assert getattr(inst, attr) is None
