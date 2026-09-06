"""Printed parts.  PETG or ASA.  These GUIDE, FEED, ALIGN and SEAL-ASSIST.
None of them contains pressure or carries structural load -- see README RULES."""
from _common import *
from math import pi


def auger_segment(pitch=None, seg_len=None):
    """Keyed feed-auger segment.  Print axis-VERTICAL, no supports:
    consecutive layers overlap 97% of the flight, so the helicoid is
    self-supporting.  100% infill, 4 perimeters."""
    pitch = pitch or P.auger_pitch
    seg_len = seg_len or P.auger_seg_len
    turns = seg_len / pitch

    hub = extrude(Circle(P.auger_hub_od / 2), amount=seg_len)
    boss = Pos(0, 0, (seg_len - P.auger_boss_len) / 2) * extrude(
        Circle(P.auger_pin_boss / 2), amount=P.auger_boss_len)

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
    bore = extrude(Circle(P.shaft_dia / 2 + 0.30), amount=seg_len)      # 0.6 dia clearance
    pin = (Rot(90, 0, 0) * Pos(0, (seg_len - P.auger_boss_len) / 2 + P.auger_boss_len / 2, -60)
           * extrude(Circle((P.xpin_dia + 0.4) / 2), amount=120))
    return body.cut(bore).cut(pin).clean()


def lantern_ring():
    """Sits mid-stack in the packing.  Grease injected through the box wall
    reaches the shaft HERE and pushes grout back out of the box.  This is what
    keeps abrasive out of the packing; on a grout pump it is not optional."""
    od, idd, L = P.gland_box_id - 0.6, P.sleeve_od + 0.6, P.lantern_len
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
    od, idd, L = P.gland_box_id - 0.5, P.sleeve_od + 0.8, P.follower_len
    body = extrude(Circle(od / 2) - Circle(idd / 2), amount=L)
    body += Pos(0, 0, L) * extrude(Circle(68 / 2) - Circle(idd / 2), amount=6)
    # shoulder stays OUTSIDE the box: when it touches the box rim, repack.
    return body.clean()


def stator_cradle(height=None):
    """Non-structural.  The stator hangs off the tie rods; this only stops it
    drooping into a banana, which closes the bore and spikes the torque."""
    H = height if height is not None else P.collar_top_z
    r = P.stator_od / 2 + 0.5
    w = P.stator_od + 110
    body = extrude(Rectangle(w, 90), amount=H)
    body -= Pos(0, 0, H) * Rot(90, 0, 0) * extrude(Circle(r), amount=200, both=True)
    for x in (-w / 2 + 22, w / 2 - 22):
        body -= Pos(x, 0, -1) * extrude(SlotOverall(26, 9), amount=H + 2)
    return body.clean()


def stator_strap():
    """Printed keeper over the cradle.  2 x M8, FINGER TIGHT -- it aligns the
    stator, it does not clamp it.  Local z = 0 is the stator centreline."""
    r = P.stator_od / 2 + 0.5
    w = P.stator_od + 110
    body = Pos(0, 0, -r) * extrude(Rectangle(w, 40), amount=2 * r + 14)
    body -= Rot(90, 0, 0) * extrude(Circle(r), amount=200, both=True)
    body -= Pos(0, 0, -r - 1) * extrude(Rectangle(P.stator_od + 1, 50), amount=1.5)
    for x in (-w / 2 + 22, w / 2 - 22):
        body -= Pos(x, 0, -r - 1) * extrude(Circle(4.4), amount=2 * r + 20)
    return body.clean()


def auger_pin_jig():
    """Slips on the 35 mm shaft; the 6 mm bushed hole indexes every cross-pin
    hole on the same clock angle.  Drill press, 6 mm bit, done."""
    body = extrude(Rectangle(70, 30), amount=60)
    body -= Pos(0, 0, -1) * extrude(Circle(P.shaft_dia / 2 + 0.25), amount=62)
    body -= Rot(90, 0, 0) * Pos(0, 30, -50) * extrude(Circle(P.xpin_dia / 2 + 0.15), amount=100)
    body -= Pos(0, 0, -1) * extrude(Rectangle(2.5, 40), amount=62)          # split, clamps on
    for z in (18, 42):
        body -= Rot(0, 90, 0) * Pos(-z, 0, -40) * extrude(Circle(2.6), amount=80)
    return body.clean()


def joint_boot_clamp():
    """Two-piece retainer for a bicycle inner-tube boot over the pin joint."""
    body = extrude(Circle((P.conrod_bar + 14) / 2) - Circle((P.conrod_bar + 3) / 2), amount=12)
    body -= Pos(0, 0, -1) * extrude(Rectangle(2.0, 80), amount=14)
    return body.clean()
