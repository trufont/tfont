import pytest
from tfont.objects.path import Path
from tfont.objects.point import Point
from tfont.util.tracker import TaggingList


class ManualList(TaggingList):
    __slots__ = ("_data")

    @property
    def _sequence(self):
        return self._data


def makeManualList():
    # note we set parent manually here, each implementor should
    # test that parent is set properly
    parent = object()
    inst = ManualList(parent)
    inst._data = Path([Point(10, 0, "move"), Point(0, 10, "line")])
    for point in inst._data:
        point._parent = parent
    return inst


def test_taggingList_ctor():
    with pytest.raises(TypeError):
        TaggingList()
    TaggingList(parent=object())


def test_taggingList_delitem():
    inst = makeManualList()
    point = inst._data[-1]
    assert point.parent == inst._parent
    del inst[-1]
    assert point.parent is None


def test_taggingList_getitem():
    inst = makeManualList()
    point = Point(1, 2, "line")
    inst.append(point)
    assert inst._data[2] == point


def test_taggingList_setitem():
    inst = makeManualList()
    point = Point(1, 2, "line")
    orig = inst[1]
    inst[1] = point
    assert inst._data[1] == point
    assert orig.parent is None
    assert point.parent == inst._parent


def test_taggingList_contains():
    inst = makeManualList()
    point = Point(1, 2, "line")
    inst.append(point)
    assert point in inst
    point = Point(2, 0)
    assert point not in inst
    assert Point(1, 2, "line") not in inst


def test_taggingList_iter():
    inst = makeManualList()
    assert len(list(iter(inst))) == 2


def test_taggingList_len():
    inst = makeManualList()
    assert len(inst) == 2


def test_taggingList_repr():
    inst = makeManualList()
    assert repr(inst) == "Path([Point(10, 0, 'move'), Point(0, 10, 'line')])"
    for i in range(2):
        coord = 10*(i+1)
        inst.append(Point(coord, coord, 'line'))
    assert repr(inst) == "Path([Point(10, 0, 'move'),\n      Point(0, 10, 'line'),\n      Point(10, 10, 'line'),\n      Point(20, 20, 'line')])"


def test_taggingList_reversed():
    inst = makeManualList()
    points = list(inst)
    rev = list(reversed(inst))
    points.reverse()
    assert points == rev


def test_taggingList_append():
    inst = makeManualList()
    point = Point(1, 2, "line")
    inst.append(point)
    assert inst._data[-1] == point
    assert point.parent == inst._parent


def test_taggingList_clear():
    inst = makeManualList()
    points = list(inst)
    inst.clear()
    assert len(inst._data) == 0
    for point in points:
        assert point.parent is None


def test_taggingList_extend():
    inst = makeManualList()
    morePoints = list(makeManualList())
    inst.extend(morePoints)
    assert len(inst._data) == 4
    for point in morePoints:
        assert point.parent == inst._parent


def test_taggingList_index():
    inst = makeManualList()
    point = inst[1]
    assert inst.index(point) == 1


def test_taggingList_insert():
    inst = makeManualList()
    point = Point(1, 2, "line")
    inst.insert(1, point)
    assert inst._data[1] == point
    assert point.parent == inst._parent


def test_taggingList_pop():
    inst = makeManualList()
    point = inst.pop(1)
    assert point.parent is None
    assert len(inst._data) == 1


def test_taggingList_remove():
    inst = makeManualList()
    point = inst[1]
    inst.remove(point)
    assert point.parent is None
    assert len(inst._data) == 1


def test_taggingList_reverse():
    inst = makeManualList()
    points = list(inst)
    inst.reverse()
    points.reverse()
    assert points == inst
