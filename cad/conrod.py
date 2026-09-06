"""Rotor articulation and drive-end hardware.

The rotor of a 1:2 progressive-cavity pump does not just orbit, it precesses:
its axis sweeps a cone.  A single cross pin is a 1-DOF hinge and cannot follow
that.  So the coupling rod carries a fork at EACH end with the two pin axes at
90 degrees to one another -- a Cardan pair -- and both pin bores are drilled
0.5 mm oversize so each joint is deliberately sloppy.  Grease it, boot it.
That is exactly what small commercial mortar pumps do.
"""
from _common import *


def conrod():
    """Weldment: 32 mm bar + 4 ears.  Chop saw, drill press, welder.  No mill."""
    L = P.conrod_len
    ear_t, ear_w = P.conrod_fork_t, P.conrod_bar
    gap_rotor = P.rotor_pin_eye_width + 1.5      # front fork straddles the rotor eye
    gap_shaft = P.tongue_t + 1.5                 # rear fork straddles the shaft tongue
    ear_l = P.conrod_ear_len
    bar_l = L - 2 * ear_l * 0.55
    bar = Pos(0, 0, -bar_l / 2) * extrude(Circle(P.conrod_bar / 2), amount=bar_l)

    def fork(z0, sign, rot, gap):
        ears = None
        for s in (-1, 1):
            e = Pos(s * (gap / 2 + ear_t / 2), 0, z0) * extrude(
                Rectangle(ear_t, ear_w), amount=sign * ear_l)
            ears = e if ears is None else ears + e
        hole = Pos(0, 0, z0 + sign * (ear_l - P.conrod_pin_end)) * Rot(0, 90, 0) * extrude(
            Circle((P.conrod_pin_dia + 0.5) / 2), amount=120, both=True)
        return (Rot(0, 0, rot) * (ears - hole))

    return (bar + fork(bar_l / 2 - 6, +1, 0, gap_rotor)
                + fork(-bar_l / 2 + 6, -1, 90, gap_shaft)).clean()


def shaft_tongue():
    """Plug-welded into a slot in the front end of the drive shaft; the rear
    fork of the con-rod straddles it.  12 mm plate, 32 wide."""
    sk = (Rectangle(P.conrod_bar, P.tongue_len, align=(Align.CENTER, Align.MIN))
          - Pos(0, P.tongue_len - P.tongue_pin_end)
          * Circle((P.conrod_pin_dia + 0.5) / 2))
    return extrude(sk, amount=P.tongue_t), sk


def hex_stub():
    """THE PRIMARY INPUT.  A 1/2\" spade-handle paddle drill chucks straight onto
    this; there is no motor, reducer or coupling on the machine.

    1-1/4\" sch40 pipe (ID 35.05 -- a slip fit on the 35 mm shaft), cross-pinned,
    plug-welded to a 1/2\" A/F hex bar.  Chop saw, drill press, welder.

    It is also the upgrade path: bore a coupling half to 12.7 A/F (or just clamp
    a 12.7 mm round adapter) and the motor + NMRV reducer bolt to the same stub
    with no change to the pump.

    Torsion check at burst: a 12.7 A/F hex has Wt ~ 400 mm3, so 25 N.m gives
    ~62 MPa -- trivial for any steel bar."""
    sl = 60.0
    tube = extrude(Circle(P.sleeve_od / 2) - Circle(P.sleeve_id / 2), amount=sl)
    plug = Pos(0, 0, sl) * extrude(Circle(P.sleeve_od / 2), amount=10)
    hexb = Pos(0, 0, sl + 10) * extrude(
        RegularPolygon(P.hex_af / 2 / 0.8660254, 6), amount=P.hex_free_len)
    body = tube + plug + hexb
    body -= (Rot(90, 0, 0) * Pos(0, sl / 2, -60)
             * extrude(Circle((P.hex_pin_dia + 0.3) / 2), amount=120))
    return body.clean()


def drive_shaft():
    """35 mm cold-rolled bar.  Reference model only -- it is a sawn length with
    four 6 mm cross holes, one 8 mm cross hole and one keyway."""
    L = abs(P.x_shaft_rear - P.x_shaft_nose)
    s = Pos(0, 0, -L) * extrude(Circle(P.shaft_dia / 2), amount=L)
    stations = [P.auger_seg_len * i for i in range(P.n_auger_full)]
    if P.auger_tail_len > 1:
        stations.append(P.auger_seg_len * P.n_auger_full)
    for i, s0 in enumerate(stations):
        seg = P.auger_seg_len if i < P.n_auger_full else P.auger_tail_len
        z = -(abs(P.x_shaft_nose - P.x_auger_front) + s0
              + (seg - P.auger_boss_len) / 2 + P.auger_boss_len / 2)
        s -= Rot(90, 0, 0) * Pos(0, z, -40) * extrude(Circle(P.xpin_dia / 2), amount=80)
    # cross hole for the hex stub, in the last 60 mm
    s -= (Rot(90, 0, 0) * Pos(0, -(L - 30), -40)
          * extrude(Circle(P.hex_pin_dia / 2), amount=80))
    return s.clean()
