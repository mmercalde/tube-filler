"""Printed parts.  PETG or ASA.  These GUIDE, FEED, ALIGN and SEAL-ASSIST.
None of them contains pressure or carries structural load -- see README RULES."""
from _common import *
from math import pi


def _pin_boss():
    """The cross-pin boss: a LENS, not a cylinder, built at z = 0..boss_len.

    The boss is the only local restriction in the feed channel, and the old
    plain 56 x 22 cylinder left 61% of the open-hub free area -- enough to drop
    the LOCAL overfeed to 0.58x and starve the pump at the one station that
    metered least.  Two changes, and they do different jobs:

      * the swept diameter comes down to auger_pin_boss, which is capped by the
        local-overfeed gate in calcs section 5b.  That is what fixes the AREA.
      * the shape is faired, which is what stops it DAMMING.  Axially it is a
        double cone into a short land, so grout rides over it instead of
        hitting a step; in plan it is an ellipse whose major axis lies on the
        pin, blended flush into the hub at +-90 deg.  Material ends up only
        where the pin actually bears, and the two quarters of the channel that
        carry no load stay at full hub diameter.

    The fairing is AXIAL -- the along-channel component of the helix.  Skewing
    the lens to the true helix angle would make the boss asymmetric about the
    pin, which is the one thing it may not be: both bearing patches have to be
    the same, or the pin cocks and digs in on one side.
    """
    r_hub, r_bos = P.auger_hub_od / 2, P.auger_pin_boss / 2
    fair, L = P.auger_boss_fair, P.auger_boss_len
    land = L - 2 * fair
    ogive = Pos(0, 0, fair) * Solid.make_cylinder(r_bos, land)
    if fair > 0:                        # fair = 0 is a plain cylinder again
        ogive = (Solid.make_cone(r_hub, r_bos, fair) + ogive
                 + Pos(0, 0, fair + land) * Solid.make_cone(r_bos, r_hub, fair))
    # Ellipse wants major on x, the pin lies on y -- build it, then turn it.
    lens = extrude(Rot(0, 0, 90) * Ellipse(r_bos, P.auger_boss_minor / 2), amount=L)
    return (ogive & lens).clean()


def auger_segment(pitch=None, seg_len=None):
    """Keyed feed-auger segment.  Print axis-VERTICAL, no supports:
    consecutive layers overlap 97% of the flight, so the helicoid is
    self-supporting.  100% infill, 4 perimeters.

    Hub bore is shaft_dia + auger_bore_clear (a fixed 0.5 mm loose slide).
    Cross-pin hole is xpin_dia + print_clearance (a tuned fit).
    The cross-pin boss is a faired lens, not a cylinder -- see _pin_boss()."""
    pitch = pitch or P.auger_pitch
    seg_len = seg_len or P.auger_seg_len
    turns = seg_len / pitch

    hub = extrude(Circle(P.auger_hub_od / 2), amount=seg_len)
    boss = Pos(0, 0, (seg_len - P.auger_boss_len) / 2) * _pin_boss()

    # Flight section = an ANGULAR WEDGE of an annulus, not a rectangle.
    # A wedge of half-angle a gives axial thickness (2a/2pi)*pitch at EVERY
    # radius, so the flight is a constant 6 mm thick from root to tip and the
    # swept envelope is exactly auger_od.  A rectangle would taper to ~2 mm at
    # the tip and swell the OD past the barrel clearance.
    from math import radians, cos, sin, pi as _pi
    a = _pi * P.auger_flight_t / pitch                       # half-angle, rad
    r0, r1 = P.auger_hub_od / 2 - 1.0, P.auger_od / 2
    R = 2 * r1
    wedge = make_face(Polyline((0, 0, 0),
                               (R * cos(-a), R * sin(-a), 0),
                               (R * cos(a), R * sin(a), 0), close=True))
    sec = (Circle(r1) - Circle(r0)) & wedge
    # OCC's rotating extrude goes wrong past ~360 deg, so stack half-turn
    # chunks and fuse.  (Caught by a volume check, not by an exception.)
    from math import ceil
    n_chunk = max(1, int(ceil(seg_len / (pitch * 0.5))))
    h_ch = seg_len / n_chunk
    a_ch = 360.0 * h_ch / pitch
    flight = None
    for i in range(n_chunk):
        pc = Solid.extrude_linear_with_rotation(
            sec.faces()[0], center=(0, 0, 0), normal=(0, 0, h_ch), angle=a_ch)
        pc = pc.rotate(Axis.Z, i * a_ch).moved(Location((0, 0, i * h_ch)))
        flight = pc if flight is None else flight.fuse(pc)

    body = hub.fuse(boss).fuse(flight).clean()
    # The BORE is a fixed loose slide (auger_bore_clear), NOT print_clearance:
    # the cross pin locates the segment and carries the drive, so the bore only
    # has to go on and come off a wet, gritty shaft.  The PIN HOLE is the fit,
    # and it is the one that stays tuned to the coupons.
    bore = extrude(Circle(P.auger_hub_bore / 2), amount=seg_len)
    pin = (Rot(90, 0, 0) * Pos(0, (seg_len - P.auger_boss_len) / 2 + P.auger_boss_len / 2, -60)
           * extrude(Circle((P.xpin_dia + P.print_clearance) / 2), amount=120))
    return body.cut(bore).cut(pin).clean()


def lantern_ring():
    """Sits mid-stack in the packing.  Grease injected through the box wall
    reaches the shaft HERE and pushes grout back out of the box.  This is what
    keeps abrasive out of the packing; on a grout pump it is not optional."""
    od = P.gland_box_id - P.print_clearance          # fit: slides in the box
    idd = P.sleeve_od + P.running_clearance          # gap: the sleeve turns
    L = P.lantern_len
    body = extrude(Circle(od / 2) - Circle(idd / 2), amount=L)
    for i in range(8):
        body -= (Rot(0, 0, i * 45) * Pos(0, 0, L / 2) * Rot(90, 0, 0)
                 * extrude(Circle(1.6), amount=od, both=True))
    g = (L - 6) / 2
    body -= Pos(0, 0, g) * extrude(Circle(od / 2) - Circle(od / 2 - 1.5), amount=6)
    body -= Pos(0, 0, g) * extrude(Circle(idd / 2 + 1.5) - Circle(idd / 2), amount=6)
    return body.clean()


def gland_follower():
    """Anti-extrusion bushing.  The steel gland plate pushes this; this pushes
    the packing.  Fully supported inside the box bore -- pure compression, no
    pressure containment.  Consumable: reprint when the nose is chewed."""
    od = P.gland_box_id - P.print_clearance          # fit: slides in the box
    idd = P.sleeve_od + P.running_clearance          # gap: the sleeve turns
    L = P.follower_len
    body = extrude(Circle(od / 2) - Circle(idd / 2), amount=L)
    body += Pos(0, 0, L) * extrude(Circle(68 / 2) - Circle(idd / 2), amount=6)
    # shoulder stays OUTSIDE the box: when it touches the box rim, repack.
    return body.clean()


def stator_cradle(height=None):
    """Non-structural.  The stator hangs off the tie rods; this only stops it
    drooping into a banana, which closes the bore and spikes the torque."""
    H = height if height is not None else P.stator_cradle_h
    r = (P.stator_od + P.print_clearance) / 2
    w = P.stator_od + 150
    body = extrude(Rectangle(w, 90), amount=H)
    body -= Pos(0, 0, H) * Rot(90, 0, 0) * extrude(Circle(r), amount=200, both=True)
    for x in (-w / 2 + 22, w / 2 - 22):
        body -= Pos(x, 0, -1) * extrude(SlotOverall(26, 9), amount=H + 2)
    # channels for the two LOWER tie-rod spacers.  Without them the cradle sits
    # straight through them -- which is what the assembly clash check found.
    # 21 mm of material bridges over each channel, so it stays one piece.
    # Circular channels, not open slots: the web left between the stator groove
    # and the spacer is only ~3.5 mm and an open slot cuts it, which splits the
    # cradle into three loose pieces.  The spacers slide out axially with the
    # stator at washout, so a closed channel costs nothing.
    for sx in (-1, 1):
        body -= (Pos(sx * P.tie_xy, 0, H - P.tie_xy) * Rot(90, 0, 0)
                 * extrude(Circle((P.spacer_od + 4 * P.print_clearance) / 2),
                           amount=200, both=True))
    return body.clean()


def stator_strap():
    """Printed keeper that caps the stator on the cradle.  2 x M8, FINGER TIGHT
    -- it aligns the stator, it does not clamp it.

    Printed valley-up (bore centred on the TOP face), so there is no crown
    overhang and no supports.  The assembly flips it.  The earlier version
    spanned a full arch from -r to +r and duplicated the cradle's lower half --
    which the assembly clash check found the moment both were placed."""
    r = (P.stator_od + P.print_clearance) / 2
    w = P.stator_od + 150
    h = r + 16.0
    body = extrude(Rectangle(w, 40), amount=h)
    body -= Pos(0, 0, h) * Rot(90, 0, 0) * extrude(Circle(r), amount=200, both=True)
    for x in (-w / 2 + 22, w / 2 - 22):
        body -= Pos(x, 0, -1) * extrude(Circle(4.4), amount=h + 2)
    # channels for the two UPPER tie-rod spacers, open at the face that goes
    # down over the stator (local +z here, because this prints inverted).
    for sx in (-1, 1):
        body -= (Pos(sx * P.tie_xy, 0, h - P.tie_xy) * Rot(90, 0, 0)
                 * extrude(Circle((P.spacer_od + 4 * P.print_clearance) / 2),
                           amount=200, both=True))
    return body.clean()


def auger_pin_jig():
    """Slips on the 35 mm shaft; the 6 mm bushed hole indexes every cross-pin
    hole on the same clock angle.  Drill press, 6 mm bit, done."""
    body = extrude(Rectangle(70, 30), amount=60)
    body -= Pos(0, 0, -1) * extrude(
        Circle((P.shaft_dia + P.print_clearance) / 2), amount=62)
    body -= Rot(90, 0, 0) * Pos(0, 30, -50) * extrude(
        Circle((P.xpin_dia + P.print_clearance) / 2), amount=100)
    body -= Pos(0, 0, -1) * extrude(Rectangle(2.5, 40), amount=62)          # split, clamps on
    for z in (18, 42):
        body -= Rot(0, 90, 0) * Pos(-z, 0, -40) * extrude(Circle(2.6), amount=80)
    return body.clean()


def joint_boot_clamp():
    """Two-piece retainer for a bicycle inner-tube boot over the pin joint."""
    body = extrude(Circle((P.conrod_bar + 14) / 2) - Circle((P.conrod_bar + 3) / 2), amount=12)
    body -= Pos(0, 0, -1) * extrude(Rectangle(2.0, 80), amount=14)
    return body.clean()
