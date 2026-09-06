"""OPERATIONAL PRINTED PARTS -- things that stay with the machine.

Same rule as everything else printed here: these GUIDE, HOLD, SCREEN and
COVER.  Not one of them contains pressure or carries structural load.  The
drill cradle is the case worth being explicit about: it clamps the drill down,
and the reaction torque goes drill collar -> STEEL lug -> STEEL upright ->
braces -> skid.  The plastic never sees it.
"""
from _common import *
from math import pi, ceil

CLR = 0.4


def _emboss(txt, size, x, y, z, depth=0.8):
    return Pos(x, y, z - 0.4) * extrude(
        Text(txt, font_size=size, align=(Align.CENTER, Align.CENTER)),
        amount=depth + 0.4)


# ===========================================================================
# Drill cradle -- CLAMPING LOAD ONLY
# ===========================================================================
def _cradle_common():
    R = P.drill_body_dia / 2 + P.cradle_clr
    L = P.cradle_plate_l
    axis = P.cradle_foot_t + P.cradle_wall + R        # above the steel plate
    y_ear = R + P.cradle_wall + 26.0
    y_foot = R + P.cradle_wall + 54.0
    return R, L, axis, y_ear, y_foot


def drill_cradle_saddle():
    """Semicircular cradle, not a vee: the drill body is a moulded plastic
    gearcase, and a vee would dig two lines into it.  A matched radius spreads
    the clamp.  Prints as a valley -- no overhang, no supports.

    Bolts down to the 10 mm steel cradle plate through four slots (slots, not
    holes: the drill has to come out at the same height every time, and the
    slots let you square it to the hex stub)."""
    R, L, axis, y_ear, y_foot = _cradle_common()
    foot = Box(L, 2 * y_foot, P.cradle_foot_t,
               align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = Pos(0, 0, P.cradle_foot_t) * Box(
        L, 2 * y_ear, axis - P.cradle_foot_t,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = foot + body
    body -= Pos(0, 0, axis) * Rot(0, 90, 0) * extrude(
        Circle(R), amount=L + 20, both=True)
    # Bolt rows: one at x=0, and a second pair only if the saddle is long
    # enough to space them.  The saddle length follows the drill body available
    # behind the aux-handle collar, and that is often only ~46 mm.
    xs = [0.0] if L < 90 else [-(L / 2 - 22), L / 2 - 22]
    for sx in xs:
        for sy in (-1, 1):
            body -= Pos(sx, sy * (y_foot - 16), -1) * extrude(
                SlotOverall(26, 9.0), amount=P.cradle_foot_t + 2)       # M8 slots
            body -= Pos(sx, sy * y_ear * 0.78, -1) * extrude(
                Circle(4.4), amount=axis + 2)                           # M8 strap
    body += _emboss("CLAMP ONLY", 5.0, 0, y_foot - 8, P.cradle_foot_t)
    return body.clean()


def drill_cradle_strap():
    """Upper half.  Four M8 pull it down onto the saddle.  Line it with a strip
    of inner tube: you are clamping a plastic gearcase, not a shaft."""
    R, L, axis, y_ear, y_foot = _cradle_common()
    # teardrop bore, and the block must clear the teardrop apex -- a bore whose
    # crown pokes out of the top does not make an arch, it makes two loose
    # cheeks.  The 45-degree roof also means this prints with no supports.
    a = R * 0.70710678
    h = R * 1.4142136 + P.cradle_strap_t
    body = Box(L, 2 * y_ear, h, align=(Align.CENTER, Align.CENTER, Align.MIN))
    bore = Circle(R) + make_face(Polyline((-a, a, 0), (0, R * 1.4142136, 0),
                                          (a, a, 0), close=True))
    body -= Pos(0, 0, 0) * extrude(Plane.YZ * bore, amount=L + 20, both=True)
    xs = [0.0] if L < 90 else [-(L / 2 - 22), L / 2 - 22]
    for sx in xs:
        for sy in (-1, 1):
            body -= Pos(sx, sy * y_ear * 0.78, -1) * extrude(
                Circle(4.4), amount=h + 2)
    return body.clean()


# ===========================================================================
# Hopper guard grate -- four tiles, dropped into the welded steel rim
# ===========================================================================
def hopper_guard_tile():
    """One quarter of the hopper guard.  The STEEL rim and its 6 mm bars carry
    any load that lands on this; the printed ribs run the other way and turn
    the 25 mm slots into 25 mm squares, which is what actually stops a hand.

    Four identical tiles.  They lap on two edges, so one part covers all four
    positions -- rotate them."""
    tw, tl = P.hop_top_w / 2, P.hop_top_l / 2
    t, rib, frame = 12.0, 6.0, 9.0
    body = Box(tl, tw, t, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body -= Pos(0, 0, -1) * Box(tl - 2 * frame, tw - 2 * frame, t + 2,
                                align=(Align.CENTER, Align.CENTER, Align.MIN))
    n = int(round((tw - 2 * frame) / P.grate_pitch))
    for i in range(1, n):
        y = -tw / 2 + frame + (tw - 2 * frame) * i / n
        body += Pos(0, y, 0) * Box(tl - 2 * frame + 2, rib, t,
                                   align=(Align.CENTER, Align.CENTER, Align.MIN))
    # lap on two adjacent edges so tiles overlap rather than butt
    body += Pos(tl / 2 - 1, 0, 0) * Box(18, tw, t / 2,
                                        align=(Align.CENTER, Align.CENTER, Align.MIN))
    body -= Pos(-tl / 2 + 8, 0, t / 2) * Box(18, tw + 2, t / 2 + 1,
                                             align=(Align.CENTER, Align.CENTER, Align.MIN))
    return body.clean()


# ===========================================================================
# Sand screen -- 1/8" hardware cloth on a 5-gal bucket
# ===========================================================================
def screen_od():
    return P.bucket_rim_od + 16.0


def screen_fits():
    """One piece, or two halves?  Decided from the MEASURED bucket rim and the
    MEASURED bed, not assumed.  Splitting costs nothing: the hardware cloth is
    one continuous piece, so a seam in the frame under it leaks no sand."""
    return screen_od() <= min(P.printer_x, P.printer_y) - 8


def _maybe_half(body, seam_h):
    if screen_fits():
        return body
    od = screen_od()
    half = body & Pos(0, od / 4 + 1, 0) * Box(
        od + 40, od / 2, seam_h + 40, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # two M4 seam lugs so the halves bolt to each other
    for sx in (-1, 1):
        lug = Pos(sx * (od / 2 - 26), 1, 0) * Box(
            22, 16, seam_h, align=(Align.CENTER, Align.CENTER, Align.MIN))
        half += lug
        half -= Pos(sx * (od / 2 - 26), 8, -1) * extrude(Circle(2.3), amount=seam_h + 2)
    return half.clean()


def sand_screen_frame():
    """Sits on the bucket rim.  1/8\" (3.175 mm) hardware cloth is what actually
    guarantees the <= 3 mm grain the stator needs -- the hopper grate is a hand
    guard, not a sieve, and sizing has to happen at the sand pile.

    Screen it into the bucket, then tip the bucket into the mixer."""
    rim = P.bucket_rim_od
    od, seat, lip = rim + 16.0, 8.0, 14.0
    body = extrude(Circle(od / 2) - Circle(rim / 2 - 14), amount=seat)
    body += Pos(0, 0, -lip) * extrude(
        Circle(rim / 2 + 6) - Circle(rim / 2 + 1.5), amount=lip)   # locates on the rim
    # cloth support grid, under the seat
    n = int((rim / 2 - 20) // 60.0)
    for i in range(-n, n + 1):
        for rot in (0, 90):
            bar = Pos(0, i * 60.0, 0) * Box(od, 8.0, seat,
                                            align=(Align.CENTER, Align.CENTER, Align.MIN))
            body += (Rot(0, 0, rot) * bar) & extrude(Circle(rim / 2 - 6), amount=seat)
    for i in range(8):
        body -= (Rot(0, 0, i * 45) * Pos((od - 16) / 2, 0, -lip - 1)
                 * extrude(Circle(2.3), amount=seat + lip + 2))
    body += _emboss("1/8in CLOTH", 6.0, 0, (od / 2 + (rim / 2 - 14)) / 2, seat)
    return _maybe_half(body.clean(), seat)


def sand_screen_retainer():
    """Traps the cloth against the frame.  8 x M4.  Two minutes to re-cloth."""
    rim = P.bucket_rim_od
    od = rim + 16.0
    body = extrude(Circle(od / 2) - Circle(rim / 2 - 14), amount=6.0)
    for i in range(8):
        body -= (Rot(0, 0, i * 45) * Pos((od - 16) / 2, 0, -1)
                 * extrude(Circle(2.3), amount=8))
    return _maybe_half(body.clean(), 6.0)


# ===========================================================================
# Hopper funnel
# ===========================================================================
def hopper_funnel():
    """Bucket-to-hopper chute.  Hooks over the hopper rim so nobody has to
    hold it while tipping 20 kg of grout.  Printed small-end-down: the walls
    lean out about 14 degrees from vertical, well inside self-supporting."""
    tb, tt, H, w = 190.0, 270.0, 180.0, 2.6
    outer = loft([Plane.XY * Rectangle(tb, tb * 0.7),
                  Plane.XY.offset(H) * Rectangle(tt, tt)])
    inner = loft([Plane.XY.offset(-2) * Rectangle(tb - 2 * w, tb * 0.7 - 2 * w),
                  Plane.XY.offset(H + 2) * Rectangle(tt - 2 * w, tt - 2 * w)])
    body = outer - inner
    for sy in (-1, 1):
        hook = Pos(0, sy * (tt / 2 - 3), H - 40) * Box(
            60, 22, 46, align=(Align.CENTER, Align.CENTER, Align.MIN))
        hook -= Pos(0, sy * (tt / 2 + 3), H - 40) * Box(
            64, 10, 40, align=(Align.CENTER, Align.CENTER, Align.MIN))
        body += hook
    return body.clean()


# ===========================================================================
# 1" NPT port dust caps -- x12, one per post
# ===========================================================================
def npt_dust_cap():
    """Push-in debris cap for the 1\" NPT half coupling welded to each post.
    NOT a pressure cap and not a thread: it keeps rain, grit and wasps out of
    an open port between drilling day and pour day.  Pull tab and a lanyard
    hole, because twelve small caps on a site is twelve lost caps."""
    # 1" NPT female thread minor.  This is the COUPLING bore, not the hole in
    # the post, so it is unaffected by post_shape -- square or round, the cap
    # plugs the same fitting.
    bore = 26.6
    body = extrude(Circle(42 / 2), amount=4.0)
    body += Pos(0, 0, 4) * extrude(Circle(bore / 2 - 0.5), amount=16)
    for i in range(3):              # sealing/gripping barbs
        body += Pos(0, 0, 4 + 4 + i * 5) * extrude(
            Circle(bore / 2 + 0.25) - Circle(bore / 2 - 1.2), amount=2.0)
    body += Pos(30, 0, 0) * Box(26, 20, 4.0,
                                align=(Align.CENTER, Align.CENTER, Align.MIN))
    body -= Pos(38, 0, -1) * extrude(Circle(2.6), amount=6)
    return body.clean()


# ===========================================================================
# Packing tools
# ===========================================================================
def packing_cone():
    """Sits on the stuffing-box mouth and squeezes each packing ring down to
    the bore as you push it in.  Without it you deform the ring on the box lip
    and it never seats square -- which is most of why home-built glands weep
    from one side."""
    box_id, box_od = P.gland_box_id, P.gland_box_od
    top_id = box_id + 2 * P.packing_sq * 0.35
    H, spig = 34.0, 7.0
    body = extrude(Circle(box_od / 2 + 6), amount=H)
    body += Pos(0, 0, -spig) * extrude(Circle(box_id / 2 - 0.4), amount=spig)
    body -= Pos(0, 0, -spig - 1) * (
        loft([Plane.XY.offset(-spig - 1) * Circle(box_id / 2 - 0.35),
              Plane.XY.offset(0) * Circle(box_id / 2 - 0.35),
              Plane.XY.offset(H + 1) * Circle(top_id / 2)]))
    body += _emboss("PACKING GUIDE", 5.0, 0, box_od / 2, H)
    return body.clean()


def packing_drift():
    """Half-shell push drift, qty 2.  Split, because the shaft is already in
    the machine when you repack and a closed tube will not go on.

    Drive each ring home with a mallet on this, not with the gland plate --
    the gland plate is for the last 2 mm, not for seating four rings."""
    od = P.gland_box_id - 0.6
    idd = P.sleeve_od + 1.2
    L = 120.0
    ring = extrude(Circle(od / 2) - Circle(idd / 2), amount=L)
    ring += Pos(0, 0, L) * extrude(Circle(od / 2 + 12) - Circle(idd / 2), amount=8)
    half = ring & Pos(0, od / 2 + 14, 0) * Box(
        od + 40, od + 40, L + 20, align=(Align.CENTER, Align.CENTER, Align.MIN))
    return half.clean()
