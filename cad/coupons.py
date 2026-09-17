"""FIT COUPONS -- print these before anything else.

Four short slices of the four printed fits that actually decide whether the
rest of the plastic is usable:

    A   auger CROSS-PIN hole, on a hub ring over the 35 mm drive shaft
    P   post-jig corner channel on the square PTR
    B   template drill bushing on its bit
    C   NPT dust-cap barb in a 1" coupling

Each is printed as a LADDER: five rungs either side of the current
`print_clearance` (or `print_interference` for the cap), each embossed with its
own value.  Print the plate, try every rung on the real stock, and put the one
that fits into params.py.  That single edit retunes every printed part in the
project, because every printed mating feature is derived from it.

Each coupon is modelled in the SAME print orientation as the part it stands
for -- the auger bore vertical, the corner channel on its 45-degree corner, the
bushing flat.  A fit measured in one orientation does not transfer to another:
first-layer squish and seam placement are not the same on a 45-degree face as
on a flat one.
"""
from _common import *
import jigs

H = 16.0                    # coupon height, tall enough to feel a fit
GAP = 8.0                   # spacing on the plate


def ladder(centre, step, n=5):
    k = (n - 1) // 2
    return [round(centre + (i - k) * step, 3) for i in range(n)]


def _tag(txt, size, x, y, z):
    return jigs._emboss(txt, size, x, y, z)


# --------------------------------------------------------------------- A
def coupon_auger_bore(c):
    """Hub ring on the 35 mm shaft, with the 6 mm cross hole through it.

    READ THE CROSS HOLE, not the bore.  The auger's own bore is a fixed
    0.5 mm loose slide (`auger_bore_clear`) and is no longer tuned from here --
    the pin locates and drives the segment, so that is the fit that matters.
    The bore still steps with the rung because it is the project's reference
    "printed bore over round steel" (the pin jig, the barrel jigs), and because
    a ring you can feel on a real shaft is how you judge a rung at all."""
    body = extrude(Circle(P.auger_hub_od / 2), amount=H)
    body -= Pos(0, 0, -1) * extrude(Circle((P.shaft_dia + c) / 2), amount=H + 2)
    body -= (Rot(90, 0, 0) * Pos(0, H / 2, -40)
             * extrude(Circle((P.xpin_dia + c) / 2), amount=80))
    # label tab: the hub annulus is only ~4 mm wide, so text on the ring face
    # floats over the bore.  A tab gives it something to sit on.
    ty = P.auger_hub_od / 2 + 6.0
    body += Pos(0, ty, 0) * Box(30, 14, H,
                                align=(Align.CENTER, Align.CENTER, Align.MIN))
    body += _tag(f"A{c:.2f}", 4.6, 0, ty, H)
    return body.clean()


# --------------------------------------------------------------------- P
def coupon_post_corner(c):
    """A 16 mm slice of the post jig's corner channel.  Push it onto a real
    PTR corner: both faces should touch with no rock and come off by hand.

    Printed on its outer corner at 45 degrees, exactly as the jig is."""
    S, t, reach = P.post_side, 12.0, 35.0
    zc = yc = S / 2 + c / 2                       # register planes
    y_out = -(S / 2 - reach)
    a = Pos(0, (y_out + yc + t) / 2, zc + t / 2) * Box(
        H, (yc + t) - y_out, t)
    b = Pos(0, yc + t / 2, (zc + t + zc - reach) / 2) * Box(
        H, t, (zc + t) - (zc - reach))
    body = a + b
    body += _tag(f"P{c:.2f}", 4.2, 0, y_out + 13, zc + t)
    body = Rot(-135, 0, 0) * body
    bb = body.bounding_box()
    body = Pos(0, 0, -bb.min.Z) * body
    body -= Pos(0, 0, -1) * Box(400, 400, 1.6,
                                align=(Align.CENTER, Align.CENTER, Align.MIN))
    return Pos(0, 0, -0.6) * body.clean()


# --------------------------------------------------------------------- B
def coupon_bushing(c, bit=None):
    """One template drill bushing.  Spin the real bit in it by hand: it should
    turn freely with no perceptible wobble.  This is the tightest use of
    print_clearance in the project -- if a rung is snug here and loose
    everywhere else, this is the one that decides."""
    bit = bit if bit is not None else P.tie_rod_hole
    base, boss = 4.0, 12.0
    body = extrude(Rectangle(34, 30), amount=base)
    body += Pos(0, 0, base) * extrude(Circle(bit / 2 + 4.5), amount=boss)
    body -= Pos(0, 0, -1) * extrude(Circle((bit + c) / 2), amount=base + boss + 2)
    body += _tag(f"B{c:.2f}", 4.2, 0, -11.5, base)
    return body.clean()


# --------------------------------------------------------------------- C
def coupon_dust_cap(i):
    """The dust cap's barb section only.  Push it into a real 1\" NPT half
    coupling: it should need a firm thumb and stay put upside down.

    This rung steps print_INTERFERENCE, not clearance -- a barb that grips is
    the one printed feature that wants to be oversize."""
    bore = P.npt1_bore
    body = extrude(Circle(bore / 2 + 8), amount=3.0)
    body += Pos(0, 0, 3) * extrude(
        Circle((bore - P.print_clearance) / 2), amount=H)
    for k in range(3):
        body += Pos(0, 0, 3 + 3 + k * 5) * extrude(
            Circle((bore + i) / 2) - Circle(bore / 2 - 1.2), amount=2.0)
    body += _tag(f"C{i:.2f}", 4.0, 0, -(bore / 2 + 4.2), 3.0)
    return body.clean()


# ----------------------------------------------------------------- plate
def coupon_groups():
    """[(tag, [(name, shape), ...])] -- one ladder per group, unplaced."""
    cl = ladder(P.print_clearance, P.print_clearance_step)
    inf = ladder(P.print_interference, P.print_clearance_step)
    return [
        ("A", [(f"A_auger_bore_{c:.2f}", coupon_auger_bore(c)) for c in cl]),
        ("P", [(f"P_post_corner_{c:.2f}", coupon_post_corner(c)) for c in cl]),
        ("B", [(f"B_bushing_{c:.2f}", coupon_bushing(c)) for c in cl]),
        ("C", [(f"C_dust_cap_{i:.2f}", coupon_dust_cap(i)) for i in inf]),
    ]


def coupon_set():
    return [it for _tag, items in coupon_groups() for it in items]


def plate():
    """One bed.  Each ladder starts a new row, so a group reads left to right
    in clearance order and you are never hunting for the missing rung."""
    placed, y = [], 0.0
    limit = P.printer_x - 20.0
    for _tag, items in coupon_groups():
        x, row_h = 0.0, 0.0
        for _n, s in items:
            bb = s.bounding_box()
            w, d = bb.size.X, bb.size.Y
            if x > 0 and x + w > limit:
                x, y = 0.0, y + row_h + GAP
                row_h = 0.0
            placed.append(Pos(x - bb.min.X, y - bb.min.Y, -bb.min.Z) * s)
            x += w + GAP
            row_h = max(row_h, d)
        y += row_h + GAP
    total = Compound(children=placed)
    bb = total.bounding_box()
    return Pos(-bb.center().X, -bb.center().Y, 0) * total


def plate_size():
    bb = plate().bounding_box()
    return bb.size.X, bb.size.Y, bb.size.Z
