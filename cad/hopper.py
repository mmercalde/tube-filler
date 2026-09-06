"""Hopper: 4 flat patterns + the throat collar + the barrel slot wrap template.

All four walls of a concentric rectangular frustum are PLANAR trapezoids, so
they develop exactly -- no rolling, no stretch-out approximation.  Cut them
flat, tack the corners, weld the outside.  One sloping edge of each long wall
carries a 20 mm lap so a stick welder has something to aim at.
"""
from _common import *
from math import sqrt


def _trapezoid(top, bottom, slant, lap=0.0):
    """Isosceles trapezoid, bottom edge on y=0, symmetric about x=0.
    `lap` is a TRUE PERPENDICULAR offset of the right-hand sloping edge, not a
    linear stretch -- a tapered lap does not weld square."""
    a, b = (bottom / 2, 0.0), (top / 2, slant)
    pts = [(-bottom / 2, 0.0), a, b, (-top / 2, slant)]
    if lap:
        dx, dy = b[0] - a[0], b[1] - a[1]
        L = sqrt(dx * dx + dy * dy)
        ox, oy = dy / L * lap, -dx / L * lap          # outward normal
        pts[1] = (a[0] + ox, a[1] + oy)
        pts[2] = (b[0] + ox, b[1] + oy)
    return make_face(Polyline(*[(x, y, 0) for x, y in pts], close=True))


def wall_long():
    """x2.  Spans the barrel axis direction.  Carries the lap."""
    return _trapezoid(P.hop_top_l, P.hop_bot_l, P.hop_slant_long, lap=P.hop_lap)


def wall_short():
    """x2.  Across the barrel."""
    return _trapezoid(P.hop_top_w, P.hop_bot_w, P.hop_slant_short)


def collar_side():
    """x2.  Straight bottom edge: at y = +/- hop_bot_w/2 the barrel surface is
    a straight line, so no saddle cut is needed on these two."""
    R = P.barrel_od / 2
    y = P.hop_bot_w / 2
    z0 = sqrt(max(R * R - y * y, 1.0))
    return Rectangle(P.hop_bot_l, P.collar_top_z - z0)


def collar_end():
    """x2.  Bottom edge is a true saddle cut on the barrel OD."""
    R = P.barrel_od / 2
    sk = Pos(0, P.collar_top_z / 2) * Rectangle(P.hop_bot_w, P.collar_top_z)
    return sk - Circle(R)


def barrel_slot_template():
    """Wrap this around the barrel and centre-punch the slot.  Width is the
    DEVELOPED arc length of the 50 mm chord, not the chord itself."""
    from math import asin
    R = P.barrel_od / 2
    dev = 2 * R * asin(min(P.barrel_slot_w / 2 / R, 1.0))
    circ = 2 * 3.141592653589793 * R
    outer = Rectangle(P.barrel_slot_l + 80, circ)
    slot = Rectangle(P.barrel_slot_l, dev)
    return outer - slot, dev, circ


def grate():
    """Tramp grate, NOT a sieve.  See README: 3 mm sizing happens at the sand
    pile, through a real screen, before the mixer.  This keeps stones, trowels
    and hands out of a running auger."""
    sk = Rectangle(P.hop_top_l + 60, P.hop_top_w + 60) - Rectangle(P.hop_top_l, P.hop_top_w)
    n = int(P.hop_top_w // P.grate_pitch)
    for i in range(n + 1):
        y = -P.hop_top_w / 2 + i * P.grate_pitch
        sk += Pos(0, y) * Rectangle(P.hop_top_l, 6)
    return sk
