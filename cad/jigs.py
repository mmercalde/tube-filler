"""FAB TEMPLATES -- printed drill jigs, weld fixtures and gauges.

Every one of these is a ONE-TIME SHOP TOOL.  None is on the machine when it
runs, none is in the pressure path, and the weld fixtures are explicitly
sacrificial and embossed to say so -- PETG within 20 mm of an arc is gone.

All saddle jigs parametrize on the MEASURED tube diameters (`barrel_od` for the
machine, `post_side` / `post_od` for the twelve posts), so stock that measures
75.4 instead of 76.2 costs one reprint, not a scrapped hole.

The barrel and the posts are DIFFERENT STOCK -- round tube and square PTR --
and nothing here derives one from the other.

Conventions:
  * tube axis along +X;
  * every part is modelled in the orientation it should be PRINTED, flat face
    on z=0, features growing upward -- no supports anywhere;
  * upper clamp halves get a teardrop bore so the crown is self-supporting.
"""
from _common import *
from math import sin, cos, radians, asin, degrees, ceil

CLEAR = P.print_clearance / 2   # RADIAL: half the diametral print_clearance
BOLT = 6.0              # M6 clamp bolts where a jig is bolted
EAR = 20.0
WALL = 8.0
STRAP_W = 26.0          # nylon strap / hose clamp through the ears


def _vee(apex_z, up, span):
    """90-degree vee profile in the YZ plane.  `up=True` opens upward."""
    s = 1 if up else -1
    return make_face(Polyline((0, apex_z, 0),
                              (-span, apex_z + s * span, 0),
                              (span, apex_z + s * span, 0), close=True))


def _along_x(sk, length, x0=0.0):
    return Pos(x0, 0, 0) * extrude(Plane.YZ * sk, amount=length)


def _emboss(txt, size, x, y, z, depth=0.8):
    """Sunk 0.4 mm into the face on purpose: text extruded exactly ON a plane
    is coplanar with it, and a coplanar fuse leaves the letters as separate
    lumps in the STL.  Found by counting solids, not by looking."""
    return Pos(x, y, z - 0.4) * extrude(
        Text(txt, font_size=size, align=(Align.CENTER, Align.CENTER)),
        amount=depth + 0.4)


def _emboss_side(txt, size, x, z, y_face, depth=0.8):
    """Same, on a vertical face whose outward normal is -Y."""
    t = extrude(Text(txt, font_size=size, align=(Align.CENTER, Align.CENTER)),
                amount=depth + 0.4)
    return Pos(x, y_face - 0.4, z) * Rot(-90, 0, 0) * t


class Saddle:
    """A self-centring 90-degree V-block pair for a round tube.

    Two vees, not a bored clamp.  Three reasons, all of them learned the hard
    way on this part:
      * a vee self-centres on ANY tube diameter, so a barrel that measures
        75.4 instead of 76.2 still drills on centre;
      * both halves print with 45-degree walls -- zero overhang, no supports,
        no droop at a bore crown;
      * a bored upper half whose bore crown rises above the block simply falls
        apart into two loose cheeks, which is exactly what the first version
        of this file produced.

    Each half is modelled in its PRINT orientation, flat face on z=0.
    `.axis_lower` / `.axis_upper` give the tube centre height in each half's
    own frame, so features can be placed radially about the real tube axis.
    """

    def __init__(self, tube_od, length, label="", grip=2.0, lower_t=10.0,
                 upper_t=10.0, mode="strap"):
        self.od, self.length, self.grip, self.mode = tube_od, length, grip, mode
        R = tube_od / 2
        self.R = R
        d = R * 1.4142136                       # apex-to-axis for a 90 deg vee
        self.d = d
        self.w = w = 2 * (d + WALL + EAR)
        self.yb = yb = d + WALL + EAR / 2
        self.apex_lower = lower_t
        self.axis_lower = lower_t + d
        self.hl = hl = self.axis_lower
        self.hu = hu = d - grip + upper_t
        self.axis_upper = -grip                 # tube centre, upper frame

        upper = Box(length, w, hu, align=(Align.CENTER, Align.CENTER, Align.MIN))
        upper -= _along_x(_vee(d - grip, False, w), length + 4, -length / 2 - 2)

        if mode == "strap":
            # No lower half at all.  Two nylon straps (or two hose clamps) pass
            # through the ears and round the tube.  The drill pushes the jig
            # ONTO the work, so a strap is as rigid as a bolted lower half and
            # it halves both the print time and the part count.
            self.lower = None
            for sy in (-1, 1):
                for xb in (-length / 2 + 22, length / 2 - 22):
                    upper -= Pos(xb, sy * yb, -2) * Box(
                        STRAP_W, 6.0, hu + 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
        else:
            lower = Box(length, w, hl, align=(Align.CENTER, Align.CENTER, Align.MIN))
            lower -= _along_x(_vee(self.apex_lower, True, w), length + 4,
                              -length / 2 - 2)
            for sy in (-1, 1):
                for xb in (-length / 2 + 18, length / 2 - 18):
                    lower -= Pos(xb, sy * yb, -2) * extrude(
                        Circle(BOLT / 2 + 0.25), amount=hl + 4)
                    lower -= Pos(xb, sy * yb, -0.1) * extrude(
                        RegularPolygon(10.6 / 2 / 0.8660254, 6), amount=6)
                    upper -= Pos(xb, sy * yb, -2) * extrude(
                        Circle(BOLT / 2 + 0.25), amount=hu + 4)
            self.lower = lower
        if label:
            upper += _emboss(label, 5.5, 0, yb - 17, hu)
        self.upper = upper

    def bushing(self, x, ang_deg, hole_d, boss_d=13.0, h=15.0, sink=8.0):
        """Radial drill bushing on the UPPER half, aimed at the tube axis."""
        base = Pos(x, 0, self.axis_upper) * Rot(ang_deg, 0, 0)
        self.upper += base * Pos(0, 0, self.R - 1) * extrude(
            Circle(boss_d / 2), amount=h + 1)
        self.upper -= base * Pos(0, 0, self.R - sink) * extrude(
            Circle((hole_d + P.print_clearance) / 2), amount=h + sink + 30)

    def result(self):
        if self.lower is None:
            return (self.upper.clean(),)
        return self.lower.clean(), self.upper.clean()


# ===========================================================================
# J1  barrel hopper-slot jig
# ===========================================================================
def jig_barrel_hopper_slot():
    """Clamps the barrel and turns the hopper cutout into a chain-drilling
    exercise: bushings all the way round the DEVELOPED slot perimeter at 14 mm
    pitch.  Drill every hole 6.4, knock the slug out, dress with a grinder.

    The perimeter width is the developed arc of the 50 mm chord, not the
    chord.  Cutting to the chord is the easiest way to end up 4 mm narrow."""
    R = P.barrel_od / 2
    L = P.barrel_slot_l + 76
    half_ang = asin(min(P.barrel_slot_w / 2 / R, 1.0))
    dev = 2 * R * half_ang
    S = Saddle(P.barrel_od, L, label="HOPPER SLOT")
    hx, ha = P.barrel_slot_l / 2, degrees(half_ang)
    n_long = int(ceil(P.barrel_slot_l / 14.0))
    for i in range(n_long + 1):
        x = -hx + P.barrel_slot_l * i / n_long
        S.bushing(x, +ha, 6.4)
        S.bushing(x, -ha, 6.4)
    n_end = max(2, int(ceil(dev / 14.0)))
    for i in range(1, n_end):
        a = degrees(-half_ang + 2 * half_ang * i / n_end)
        S.bushing(+hx, a, 6.4)
        S.bushing(-hx, a, 6.4)
    S.upper += _emboss(f"DEV WIDTH {dev:.1f}", 5.5, 0, -(S.yb - 20), S.hu)
    return S.result()


# ===========================================================================
# J2  barrel end jigs -- bolt circles concentric with the barrel
# ===========================================================================
def jig_barrel_end_ring(bc, hole_d, label, diagonal=True):
    """Slips OVER the barrel end (registers on the OD, not the bore) and drills
    a bolt circle concentric with the tube.  Register rim and drill bushings
    both grow UP from a flat disc, so it prints flat with no supports.

    Concentricity to the tube is what matters here: a flange 2 mm off-centre on
    its outline is invisible, a bolt circle 2 mm off-centre means the flange
    will not swap end for end."""
    rim_ir = P.barrel_od / 2 + CLEAR
    disc_r = max(bc / 2 + hole_d / 2 + 12, rim_ir + 16)
    body = extrude(Circle(disc_r), amount=6)
    body += Pos(0, 0, 6) * extrude(Circle(rim_ir + 8) - Circle(rim_ir), amount=26)
    body -= Pos(0, 0, -1) * extrude(Circle(rim_ir - 12), amount=10)   # see-through
    r = bc / 2
    off = r * 0.70710678 if diagonal else r
    pts = ([(sx * off, sy * off) for sx in (-1, 1) for sy in (-1, 1)] if diagonal
           else [(off, 0), (-off, 0), (0, off), (0, -off)])
    for x, y in pts:
        body += Pos(x, y, 6) * extrude(Circle(hole_d / 2 + 5), amount=16)
        body -= Pos(x, y, -1) * extrude(
            Circle((hole_d + P.print_clearance) / 2), amount=30)
    body += _emboss(label, 6.0, 0, -(disc_r - 9), 6)
    body += _emboss(f"BC {bc:.1f}", 6.0, 0, disc_r - 9, 6)
    return body.clean()


# ===========================================================================
# J3 / J4  post jigs -- used 12 and 12 times, so they earn their print time
# ===========================================================================
def _post_jig_square(leg_len, hole_d, label, scribe_d=None, pad_t=26.0,
                     oriented=True):
    """CORNER-CHANNEL jig for SQUARE PTR posts.

    An L-section that registers on two adjacent faces of the post.  Two flat
    faces locate a square section completely -- one plane sets height and
    rotation, the perpendicular plane sets sideways -- which a V-block cannot
    do on a square, because a vee sitting on a flat face is only touching two
    arbitrary lines and will rock and wander.

    The bushing is centred on the face it drills through.  On square PTR the
    port and vent land on a FLAT face, so the 1\" half coupling needs no saddle
    cut and the drill has nothing to skate off -- both jobs are easier than
    they were on round tube.

    Modelled in use coordinates (post axis +X, section centred on the axis),
    then rotated 135 degrees so it prints standing on its outer corner: both
    legs at 45 degrees, no overhang anywhere, and no supports.
    """
    S, t, Lb = P.post_side, 12.0, 48.0
    zc = S / 2 + CLEAR                      # register plane on the top face
    yc = S / 2 + CLEAR                      # register plane on the side face
    bx = 45.0                               # body half-length along the post
    y_out = -(S / 2 + 10.0)

    def Lsec(x0, x1, th=t):
        """L cross-section swept from x0 to x1."""
        a = Pos((x0 + x1) / 2, (y_out + yc + th) / 2, zc + th / 2) * Box(
            x1 - x0, (yc + th) - y_out, th)
        b = Pos((x0 + x1) / 2, yc + th / 2, (zc + th + zc - Lb) / 2) * Box(
            x1 - x0, th, (zc + th) - (zc - Lb))
        return a + b

    body = Lsec(-bx, bx)
    body += Lsec(-leg_len, -bx)                      # datum leg to the post end

    # solid end stop: an L-band across the post END face.  Two perpendicular
    # strips of contact -- a square butt, not a point.
    band = 22.0
    foot_env = Pos(-leg_len - 7, (y_out + yc + t) / 2, (zc + t + zc - Lb) / 2) * Box(
        14, (yc + t) - y_out, (zc + t) - (zc - Lb))
    keep_top = Pos(-leg_len - 7, 0, (zc + t + zc - band) / 2) * Box(
        14, 400, (zc + t) - (zc - band))
    keep_side = Pos(-leg_len - 7, (yc + t + yc - band) / 2, 0) * Box(
        14, (yc + t) - (yc - band), 400)
    body += foot_env & (keep_top + keep_side)

    # bushing pad, centred on the face
    body += Pos(0, 0, zc + pad_t / 2) * Box(70, 46, pad_t)
    body -= Pos(0, 0, zc - 10) * extrude(
        Circle((hole_d + P.print_clearance) / 2), amount=pad_t + 20)
    if scribe_d:
        body -= Pos(0, 0, zc + pad_t - 1.2) * (
            extrude(Circle(scribe_d / 2 + 0.6), amount=2)
            - extrude(Circle(scribe_d / 2 - 0.6), amount=2))

    # strap slots: a nylon strap through leg A and leg B wraps the other two faces
    for sx in (-1, 1):
        body -= Pos(sx * 30, y_out + 13, zc - 1) * Box(STRAP_W, 6.0, t + 2)
        body -= Pos(sx * 30, yc + t / 2, zc - Lb + 13) * Box(STRAP_W, t + 2, 6.0)

    body += _emboss(label, 5.0, 0, -(S / 2 - 4), zc + t)
    body += _emboss(f"{P.post_side:.1f} SQ PTR", 4.5, 0, -(S / 2 - 4) - 11, zc + t)

    if not oriented:
        return (body.clean(),)      # USE coordinates, for the fit check
    # print orientation: stand it on the outer corner, both legs at 45 deg
    body = Rot(-135, 0, 0) * body
    bb = body.bounding_box()
    body = Pos(0, 0, -bb.min.Z) * body
    # small flat at the knife-edge corner so it sticks to the bed
    body -= Pos(0, 0, -1) * Box(1000, 1000, 1.6,
                                align=(Align.CENTER, Align.CENTER, Align.MIN))
    body = Pos(0, 0, -0.6) * body
    return (body.clean(),)


def _post_jig_round(datum, hole_d, label, scribe_d=None, boss_h=20.0):
    """Strapped V-saddle, for the round-tube case (post_shape == \"round\").

    Same convention as the square version: the foot's contact face sits at
    x = -datum and the bushing at x = 0, so the datum distance IS
    post_port_height / post_vent_from_top with no arithmetic in between."""
    L = 90.0
    S = Saddle(P.post_od, L, label=label)
    up = S.upper
    leg_h = 16.0
    up += Pos(-datum, 0, 0) * Box(datum - L / 2 + 8, S.w - 2 * EAR, leg_h,
                                  align=(Align.MIN, Align.CENTER, Align.MIN))
    up += Pos(-datum - 14, 0, 0) * Box(14, S.w - 2 * EAR, S.R + S.d + 6,
                                       align=(Align.MIN, Align.CENTER, Align.MIN))
    up += Pos(0, 0, S.hu - 1) * extrude(Circle(hole_d / 2 + 6), amount=boss_h + 1)
    up -= Pos(0, 0, S.axis_upper + S.R - 8) * extrude(
        Circle((hole_d + P.print_clearance) / 2), amount=boss_h + 60)
    if scribe_d:
        up -= Pos(0, 0, S.hu + boss_h - 1.2) * (
            extrude(Circle(scribe_d / 2 + 0.6), amount=2)
            - extrude(Circle(scribe_d / 2 - 0.6), amount=2))
    return (up.clean(),)


def _post_jig(*a, **kw):
    """Dispatch on the MEASURED post shape.  Square PTR gets a corner channel;
    round tube gets a V-saddle.  Setting post_shape switches both jigs."""
    if P.post_shape == "square":
        return _post_jig_square(*a, **kw)
    kw.pop("pad_t", None)
    return _post_jig_round(*a, **kw)


def jig_post_port():
    """1\" NPT port, centre at post_port_height above the BASE.  The bushing
    guides the hole saw's 6 mm pilot; the scribed ring on top is the finished
    hole diameter to check against.

    The datum leg runs to the post BASE, so all twelve ports land at the same
    height without anyone reading a tape twelve times."""
    return _post_jig(P.post_port_height, 6.4,
                     f"PORT {P.post_port_height:.0f} FROM BASE",
                     scribe_d=P.post_port_hole)


def jig_post_vent():
    """Vent below the post TOP.  Same saddle, shorter leg, and you drill the
    12 mm straight through the bushing -- no pilot."""
    return _post_jig(P.post_vent_from_top, P.post_vent_dia,
                     f"VENT {P.post_vent_from_top:.0f} FROM TOP")


# ===========================================================================
# J5  1:1 flange drill templates
# ===========================================================================
def _template(size, holes, name, t=4.0, bush=9.0):
    """holes: list of (x, y, dia).  Outline doubles as the cut mark."""
    body = extrude(Rectangle(size, size), amount=t)
    for x, y, d in holes:
        body += Pos(x, y, t) * extrude(Circle(d / 2 + 4.5), amount=bush)
        body -= Pos(x, y, -1) * extrude(
            Circle((d + P.print_clearance) / 2), amount=t + bush + 4)
    body += _emboss(name, 6.0, 0, -size / 2 + 9, t)
    return body.clean()


def template_adapter_plate():
    h = [(0, 0, P.adapter_bore)] + [(x, y, P.tie_rod_hole)
                                    for x, y in [(sx * P.tie_xy, sy * P.tie_xy)
                                                 for sx in (-1, 1) for sy in (-1, 1)]]
    return _template(P.plate_size, h, "ADAPTER PLATE")


def template_discharge_rear():
    h = [(0, 0, P.disch_rear_bore)] + [(x, y, P.tie_rod_hole)
                                       for x, y in [(sx * P.tie_xy, sy * P.tie_xy)
                                                    for sx in (-1, 1) for sy in (-1, 1)]]
    return _template(P.plate_size, h, "DISCHARGE FLANGE")


def template_barrel_flange():
    off = P.barrel_bolt_bc / 2 * 0.70710678
    h = [(0, 0, P.barrel_id)] + [(sx * off, sy * off, P.barrel_bolt_m + 1)
                                 for sx in (-1, 1) for sy in (-1, 1)]
    return _template(P.barrel_flange, h, "BARREL REAR FLANGE")


# ===========================================================================
# J6  PTR tack-weld fixtures -- SACRIFICIAL
# ===========================================================================
def fixture_ptr_corner():
    """Holds two PTR ends at a true 90 while you tack.  Both pockets start
    22 mm clear of the joint line so the arc cannot reach the plastic.

    SACRIFICIAL.  Tack, remove, THEN weld out.  Weld out with this fitted and
    you will melt it into the joint."""
    s = P.ptr_size + P.print_clearance
    wall, arm, off = 9.0, 120.0, 22.0
    H = s + wall
    W = s + 2 * wall

    heel = Box(off + H, W, off + H, align=(Align.MIN, Align.CENTER, Align.MIN))
    limb_x = Pos(off, 0, 0) * Box(arm, W, H, align=(Align.MIN, Align.CENTER, Align.MIN))
    limb_z = Pos(0, 0, off) * Box(H, W, arm, align=(Align.MIN, Align.CENTER, Align.MIN))
    body = heel + limb_x + limb_z
    # pockets: open on the outer faces, stopping short of the joint
    body -= Pos(off + 2, 0, wall) * Box(arm + 40, s, s,
                                        align=(Align.MIN, Align.CENTER, Align.MIN))
    body -= Pos(wall, 0, off + 2) * Box(s, s, arm + 40,
                                        align=(Align.MIN, Align.CENTER, Align.MIN))
    # labels go on the solid outer WALL: the top of each limb is an open
    # pocket, and text embossed over a pocket is 20 loose letters in the STL.
    yf = -(s + 2 * wall) / 2
    body += _emboss_side("SACRIFICIAL", 7.0, off + arm / 2, H * 0.62, yf)
    body += _emboss_side("REMOVE BEFORE WELD OUT", 4.8, off + arm / 2, H * 0.30, yf)
    return body.clean()


def fixture_ptr_tee():
    """Squares a cross member to a rail.  Same rules.  SACRIFICIAL."""
    s = P.ptr_size + P.print_clearance
    wall, L = 9.0, 140.0
    H = s + wall
    W = s + 2 * wall
    body = Box(L, W, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body += Pos(0, -(L / 2 - W / 2 + 1), 0) * Box(
        W, L, H, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body -= Pos(0, 0, wall) * Box(L + 4, s, s,
                                  align=(Align.CENTER, Align.CENTER, Align.MIN))
    body -= Pos(0, -(L / 2 + 1), wall) * Box(
        s, L, s, align=(Align.CENTER, Align.CENTER, Align.MIN))
    # A label ledge, because every flat face on this part is either a pocket
    # floor or a pocket wall, and text on a pocket floor fouls the PTR.
    ledge = 26.0
    body += Pos(0, W / 2 + ledge / 2, 0) * Box(
        L, ledge, wall, align=(Align.CENTER, Align.CENTER, Align.MIN))
    body += _emboss("SACRIFICIAL - REMOVE BEFORE WELD OUT", 5.6, 0,
                    W / 2 + ledge / 2, wall)
    return body.clean()


# ===========================================================================
# J7  tie-rod / spacer length gauge
# ===========================================================================
def gauge_tie_rod():
    """Two lanes, both derived from the MEASURED stator length:

        SERVICE   = stator_len - stator_crush   (normal running)
        BREAK-IN  = stator_len - 0.5            (bedding a new stator, and the
                                                 first lever if the drill will
                                                 not carry the friction)

    Drop a cut spacer in a lane.  It must touch both stops.  All four spacers
    must gauge identically: they ARE the hard stop that stops you crushing the
    stator, and a stator crushed 1 mm too far can cost more torque than the
    whole drill has."""
    svc, brk = P.spacer_len, P.stator_len - 0.5
    L = max(svc, brk) + 46
    w, base, stop_h, stop_t = 104.0, 9.0, 15.0, 12.0
    body = Box(L, w, base, align=(Align.MIN, Align.CENTER, Align.MIN))
    for i, (nm, ln) in enumerate((("SERVICE", svc), ("BREAK-IN", brk))):
        y = (1 if i == 0 else -1) * w / 4
        for xs in (20 - stop_t, 20 + ln):
            body += Pos(xs, y, base) * Box(stop_t, 34, stop_h,
                                           align=(Align.MIN, Align.CENTER, Align.MIN))
        for sy in (-1, 1):                       # lane guides
            body += Pos(20, y + sy * (P.spacer_od / 2 + 3.5), base) * Box(
                ln, 4, 7, align=(Align.MIN, Align.CENTER, Align.MIN))
    body += _emboss(f"SERVICE {svc:.1f}", 7.0, L / 2, w / 2 - 9, base)
    body += _emboss(f"BREAK-IN {brk:.1f}", 7.0, L / 2, -w / 2 + 9, base)
    body += _emboss("ALL FOUR SPACERS MUST GAUGE THE SAME", 5.0, L / 2, 0, base)
    return body.clean()
