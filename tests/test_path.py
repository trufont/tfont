import tfont.util.tracker
from tfont.objects import Path, Point, Layer, Glyph


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


def test_SegmentList_splitSegment_qcurve():
    test_glyph = Glyph("a")
    test_layer = Layer("test")
    qcurve = Path([Point(0, 0), Point(50, 100), Point(100, 0, "qcurve")])
    test_layer.paths.append(qcurve)
    test_glyph.layers.append(test_layer)

    assert len(qcurve.segments) == 1
    qcurve.segments.splitSegment(0, 0.5, 1)
    assert len(qcurve.segments) == 2
    qps = [(p.x, p.y, p.type) for p in qcurve.points]
    qps_expected = [
        (p.x, p.y, p.type)
        for p in [
            Point(0, 0),
            Point(25, 50),
            Point(50, 50, "qcurve"),
            Point(75, 50),
            Point(100, 0, "qcurve"),
        ]
    ]
    assert qps == qps_expected


def test_SegmentList_splitSegment_qcurve_implied():
    test_glyph = Glyph("a")
    test_layer = Layer("test")
    qcurve = Path(
        [
            Point(1, 2),
            Point(3, 4),
            Point(5, 6),
            Point(7, 8),
            Point(0, 0),
            Point(50, 100),
            Point(100, 0, "qcurve"),
        ]
    )
    test_layer.paths.append(qcurve)
    test_glyph.layers.append(test_layer)

    assert len(qcurve.segments) == 1
    qcurve.segments.splitSegment(0, 0.5, 5)
    assert len(qcurve.segments) == 2
    qps = [(p.x, p.y, p.type) for p in qcurve.points]
    qps_expected = [
        (p.x, p.y, p.type)
        for p in [
            Point(1, 2),
            Point(3, 4),
            Point(5, 6),
            Point(7, 8),
            Point(0, 0),
            Point(25, 50),
            Point(50, 50, "qcurve"),
            Point(75, 50),
            Point(100, 0, "qcurve"),
        ]
    ]
    assert qps == qps_expected


def test_SegmentList_splitSegment_qcurve_implied2():
    test_glyph = Glyph("a")
    test_layer = Layer("test")
    qcurve = Path(  # Ubuntu-B "C"
        [
            Point(50, 347, "line"),
            Point(50, 433),  # subsegment_index 1
            Point(104, 568),
            Point(198, 661),
            Point(328, 709),
            Point(404, 709, "qcurve"),
        ]
    )
    test_layer.paths.append(qcurve)
    test_glyph.layers.append(test_layer)

    qcurve.segments.splitSegment(1, 0.4, 1)

    qps = [(p.x, p.y, p.type) for p in qcurve.points]
    qps_expected = [
        (int(p.x), int(p.y), p.type)
        for p in [  # XXX: turn implied on curves before and after into real on curves and use them in splitQuadraticAtT? t accurate then?
            Point(50, 347, "line"),  # original start of segment
            Point(50, 433),  #
            Point(77, 500, "qcurve"),  # implied on curve -> on curve
            Point(87, 529),  #
            Point(103, 527, "qcurve"),  # split point
            Point(122, 586),  #
            Point(151, 614, "qcurve"),  # implied on curve -> on curve
            Point(198, 661),
            Point(328, 709),
            Point(404, 709, "qcurve"),
        ]
    ]
    assert qps == qps_expected
