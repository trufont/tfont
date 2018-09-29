from fontTools.misc import bezierTools
import math

# TODO remove fontTools dependency/inline some of these funcs


def curveBounds(p0, p1, p2, p3):
    x0, x1, x2, x3 = p0.x, p1.x, p2.x, p3.x
    y0, y1, y2, y3 = p0.y, p1.y, p2.y, p3.y
    ts, xs, ys = [], [x0, x3], [y0, y3]

    for i in range(2):
        if i == 0:
            b = 6 * x0 - 12 * x1 + 6 * x2
            a = -3 * x0 + 9 * x1 - 9 * x2 + 3 * x3
            c = 3 * x1 - 3 * x0
        else:
            b = 6 * y0 - 12 * y1 + 6 * y2
            a = -3 * y0 + 9 * y1 - 9 * y2 + 3 * y3
            c = 3 * y1 - 3 * y0

        if abs(a) < 1e-12:
            if abs(b) < 1e-12:
                continue
            t = -c / b
            if 0 < t < 1:
                ts.append(t)
            continue

        b2ac = b * b - 4 * c * a
        if b2ac < 0:
            continue
        sqrtb2ac = math.sqrt(b2ac)
        t1 = (-b + sqrtb2ac) / (2 * a)
        if 0 < t1 < 1:
            ts.append(t1)
        t2 = (-b - sqrtb2ac) / (2 * a)
        if 0 < t2 < 1:
            ts.append(t2)

    for j in range(len(ts) - 1, -1, -1):
        t = ts[j]
        mt = 1 - t
        xValue = mt * mt * mt * x0 + 3 * mt * mt * t * x1 + 3 * mt * t * t * x2 + t * t * t * x3
        if len(xs) > 0:
            xs[j] = xValue
        else:
            xs.append(xValue)
        yValue = mt * mt * mt * y0 + 3 * mt * mt * t * y1 + 3 * mt * t * t * y2 + t * t * t * y3
        if len(ys) > 0:
            ys[j] = yValue
        else:
            ys.append(yValue)

    return min(xs), min(ys), max(xs), max(ys)

# ------------
# Intersection
# ------------


def curveIntersections(x1, y1, x2, y2, p1, p2, p3, p4):
    """
    Computes intersection between a line and a cubic curve.
    Adapted from: https://www.particleincell.com/2013/cubic-line-intersection/

    Takes four scalars describing line parameters and four points describing
    curve.
    """
    bx, by = x1 - x2, y2 - y1
    m = x1 * (y1 - y2) + y1 * (x2 - x1)
    a, b, c, d = bezierTools.calcCubicParameters(
        (p1.x, p1.y), (p2.x, p2.y), (p3.x, p3.y), (p4.x, p4.y))

    pc0 = by * a[0] + bx * a[1]
    pc1 = by * b[0] + bx * b[1]
    pc2 = by * c[0] + bx * c[1]
    pc3 = by * d[0] + bx * d[1] + m
    r = bezierTools.solveCubic(pc0, pc1, pc2, pc3)

    sol = []
    for t in r:
        if t < 0 or t > 1:
            continue
        s0 = ((a[0] * t + b[0]) * t + c[0]) * t + d[0]
        s1 = ((a[1] * t + b[1]) * t + c[1]) * t + d[1]
        if (x2 - x1) != 0:
            s = (s0 - x1) / (x2 - x1)
        else:
            s = (s1 - y1) / (y2 - y1)
        if s < 0 or s > 1:
            continue
        sol.append((s0, s1, t))
    return sol


def lineIntersection(x1, y1, x2, y2, p3, p4):
    """
    Computes intersection between two lines.
    Adapted from Andre LaMothe, "Tricks of the Windows Game Programming Gurus".
    G. Bach, http://stackoverflow.com/a/1968345

    Takes four scalars describing line parameters and two points describing
    line.
    """
    x3, y3 = p3.x, p3.y
    x4, y4 = p4.x, p4.y

    Bx_Ax = x4 - x3
    By_Ay = y4 - y3
    Dx_Cx = x2 - x1
    Dy_Cy = y2 - y1
    determinant = -Dx_Cx * By_Ay + Bx_Ax * Dy_Cy
    if abs(determinant) < 1e-12:
        return None
    s = (-By_Ay * (x3 - x1) + Bx_Ax * (y3 - y1)) / determinant
    t = (Dx_Cx * (y3 - y1) - Dy_Cy * (x3 - x1)) / determinant
    if 0 <= s <= 1 and 0 <= t <= 1:
        return x3 + (t * Bx_Ax), y3 + (t * By_Ay), t
    return None

# ----------
# Projection
# ----------


def curveProjection(x, y, p0, p1, p2, p3):
    """
    Returns projection of point x, y on line p0 p1 p2 p3.
    Adapted from PaperJS getNearestTime().
    """
    x0, x1, x2, x3 = p0.x, p1.x, p2.x, p3.x
    y0, y1, y2, y3 = p0.y, p1.y, p2.y, p3.y
    steps = 100
    minSqDist = None
    minX, minY, minT = 0, 0, 0

    def refineProjection(t):
        if t >= 0 and t <= 1:
            nonlocal minSqDist, minX, minY, minT
            mt = 1 - t
            xValue = mt * mt * mt * x0 + 3 * mt * mt * t * x1 + 3 * mt * t * t * x2 + t * t * t * x3
            yValue = mt * mt * mt * y0 + 3 * mt * mt * t * y1 + 3 * mt * t * t * y2 + t * t * t * y3
            dx = xValue - x
            dy = yValue - y
            sqDist = dx * dx + dy * dy
            if minSqDist is None or sqDist < minSqDist:
                minSqDist = sqDist
                minX = xValue
                minY = yValue
                minT = t
                return True
        return False

    for i in range(steps+1):
        t = i / steps
        refineProjection(t)

    step = 1 / (2 * steps)
    while step > 1e-8:
        if not refineProjection(minT - step) and not refineProjection(minT + step):
            step = .5 * step
    return minX, minY, minT


def lineProjection(x, y, p1, p2, ditchOutOfSegment=True):
    """
    Returns projection of point x, y on line p1 p2.
    Adapted from Grumdrig, http://stackoverflow.com/a/1501725/2037879.

    If *ditchOutOfSegment* is set, this function will return None if point p
    cannot be projected on the segment, i.e. if there's no line perpendicular
    to p1 p2 that intersects both p and a point of p1 p2.
    This is useful for certain GUI usages. Set by default.
    """
    bX = p2.x - p1.x
    bY = p2.y - p1.y
    l2 = bX * bX + bY * bY
    if not l2:
        return p1.x, p1.y, 0.0
    aX = x - p1.x
    aY = y - p1.y
    t = (aX * bX + aY * bY) / l2
    if ditchOutOfSegment:
        if t < 0:
            return p1.x, p1.y, t
        elif t > 1:
            return p2.x, p2.y, t
    projX = p1.x + t * bX
    projY = p1.y + t * bY
    return projX, projY, t
