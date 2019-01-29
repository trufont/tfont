import pytest

import tfont.util.tracker
from tfont.objects import Glyph, Layer, Path, Point
from tfont.objects.path import Segment


def test_Path_bounds(ConvertedTestFont):
    font = ConvertedTestFont
    b = (0, 0, 700, 700)
    assert font.glyphForName("A").layerForMaster("Regular").bounds == b
    assert font.glyphForName("B").layerForMaster("Regular").bounds == b
    assert font.glyphForName("B.qcurve").layerForMaster("Regular").bounds == b
    assert font.glyphForName("C").layerForMaster("Regular").bounds == b


def test_Path_intersection():
    # Example cribbed from https://stackoverflow.com/questions/27664298/calculating-intersection-point-of-quadratic-bezier-curve
    qcurve = Path([Point(125, 200, "move"), Point(250, 225), Point(275, 100, "qcurve")])
    x, y, _, _ = qcurve.segments[1].intersectLine(30, 125, 300, 175)[0]
    assert (round(x), round(y)) == (248, 165)


@pytest.fixture
def short_qcurve():
    test_glyph = Glyph("a")
    test_layer = Layer("test")
    qcurve = Path(
        [
            Point(50, 347, "line"),
            Point(50, 433),
            Point(104, 568),
            Point(198, 661),
            Point(328, 709),
            Point(404, 709, "qcurve"),
        ]
    )
    test_layer.paths.append(qcurve)
    test_glyph.layers.append(test_layer)
    return qcurve


def test_SegmentList_splitSegment_qcurve_start(short_qcurve):
    short_qcurve.segments.splitSegment(1, 0.4, 0)

    qps = [(int(p.x), int(p.y), p.type) for p in short_qcurve.points]
    qps_expected = [
        (int(p.x), int(p.y), p.type)
        for p in [
            Point(50, 347, "line"),
            Point(50, 381),
            Point(54, 412, "qcurve"),
            Point(60, 460),
            Point(77, 500, "qcurve"),
            Point(104, 568),
            Point(198, 661),
            Point(328, 709),
            Point(404, 709, "qcurve"),
        ]
    ]
    assert qps == qps_expected

    qps_segments = [(s._start, s._end, s.type) for s in short_qcurve.segments._segments]
    qps_segments_expected = [
        (0, 0, "line"),
        (1, 2, "qcurve"),
        (3, 4, "qcurve"),
        (5, 8, "qcurve"),
    ]
    assert qps_segments == qps_segments_expected


def test_SegmentList_splitSegment_qcurve_middle(short_qcurve):
    short_qcurve.segments.splitSegment(1, 0.4, 1)

    qps = [(int(p.x), int(p.y), p.type) for p in short_qcurve.points]
    qps_expected = [
        (int(p.x), int(p.y), p.type)
        for p in [
            Point(50, 347, "line"),
            Point(50, 433),
            Point(77, 500, "qcurve"),
            Point(87, 527),
            Point(101, 551, "qcurve"),
            Point(122, 586),
            Point(151, 614, "qcurve"),
            Point(198, 661),
            Point(328, 709),
            Point(404, 709, "qcurve"),
        ]
    ]
    assert qps == qps_expected

    qps_segments = [(s._start, s._end, s.type) for s in short_qcurve.segments._segments]
    qps_segments_expected = [
        (0, 0, "line"),
        (1, 2, "qcurve"),
        (3, 4, "qcurve"),
        (5, 6, "qcurve"),
        (7, 9, "qcurve"),
    ]
    assert qps_segments == qps_segments_expected


def test_SegmentList_splitSegment_qcurve_end(short_qcurve):
    short_qcurve.segments.splitSegment(1, 0.4, 3)

    qps = [(int(p.x), int(p.y), p.type) for p in short_qcurve.points]
    qps_expected = [
        (int(p.x), int(p.y), p.type)
        for p in [
            Point(50, 347, "line"),
            Point(50, 433),
            Point(104, 568),
            Point(198, 661),
            Point(263, 685, "qcurve"),
            Point(289, 694),
            Point(316, 700, "qcurve"),
            Point(358, 709),
            Point(404, 709, "qcurve"),
        ]
    ]
    assert qps == qps_expected

    qps_segments = [(s._start, s._end, s.type) for s in short_qcurve.segments._segments]
    qps_segments_expected = [
        (0, 0, "line"),
        (1, 4, "qcurve"),
        (5, 6, "qcurve"),
        (7, 8, "qcurve"),
    ]
    assert qps_segments == qps_segments_expected
