from tfont.objects import Path, Point


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
    x, y, _ = qcurve.segments[1].intersectLine(30, 125, 300, 175)[0]
    assert (round(x), round(y)) == (248, 165)
