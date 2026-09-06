"""Steel plates: adapter plate, discharge head, barrel rear flange + cover."""
from _common import *


def adapter_plate():
    """Welded to the barrel front.  Washout face #1: everything forward of it
    comes off when the 4 tie-rod nuts are loosened."""
    sk = clamp_plate_2d(P.adapter_bore)
    return extrude(sk, amount=P.plate_t), sk


def adapter_plate_scribe():
    """Barrel OD circle -- scribe it, do not cut it.  The barrel butts here."""
    return Circle(P.barrel_od / 2).edges()


def discharge_rear_plate():
    sk = clamp_plate_2d(P.disch_rear_bore)
    return extrude(sk, amount=P.plate_t), sk


def discharge_cap():
    sk = (Rectangle(P.disch_cap_size, P.disch_cap_size)
          - Circle(P.disch_cap_bore / 2))
    return extrude(sk, amount=P.disch_cap_t), sk


def discharge_head():
    """rear plate + 2\" sch40 chamber ring + cap plate + 1\" NPT half coupling
    + 1/4\" NPT gauge boss.  One weldment; comes off as a unit for washout."""
    rear = extrude(clamp_plate_2d(P.disch_rear_bore), amount=P.plate_t)
    z = P.plate_t
    ring = (Pos(0, 0, z) * extrude(Circle(P.disch_ring_od / 2), amount=P.disch_ring_len)
            - Pos(0, 0, z) * extrude(Circle(P.disch_ring_id / 2), amount=P.disch_ring_len))
    z += P.disch_ring_len
    cap = Pos(0, 0, z) * extrude(
        Rectangle(P.disch_cap_size, P.disch_cap_size) - Circle(P.disch_cap_bore / 2),
        amount=P.disch_cap_t)
    z += P.disch_cap_t
    # 1" NPT 3000# half coupling, 48.3 OD x 25 long
    coup = (Pos(0, 0, z) * extrude(Circle(48.3 / 2), amount=25)
            - Pos(0, 0, z) * extrude(Circle(P.disch_cap_bore / 2), amount=25))
    # 1/4" NPT gauge boss on top of the ring
    gb_z = P.plate_t + P.disch_ring_len / 2
    boss = Rot(90, 0, 0) * Pos(0, gb_z, -P.disch_ring_od / 2 - 18) * extrude(Circle(28 / 2), amount=20)
    hole = Rot(90, 0, 0) * Pos(0, gb_z, -P.disch_ring_od / 2 - 18) * extrude(Circle(P.disch_gauge_hole / 2), amount=40)
    return (rear + ring + cap + coup + boss) - hole


def barrel_rear_flange():
    """Welded to the back of the barrel.  Bolted, so the whole drive train
    (shaft + auger + gland) withdraws rearward to change the auger."""
    sk = bolt_ring_2d(P.barrel_flange, P.barrel_id, P.barrel_bolt_bc,
                      P.barrel_bolt_m + 1.0)
    return extrude(sk, amount=P.barrel_flange_t), sk


def barrel_rear_cover():
    """Same bolt pattern; carries the stuffing box.  Bore takes the 2-1/2\" pipe."""
    sk = bolt_ring_2d(P.barrel_flange, P.gland_box_od, P.barrel_bolt_bc,
                      P.barrel_bolt_m + 1.0)
    # two M10 gland studs, on the horizontal centreline
    for x in (-P.gland_stud_span / 2, P.gland_stud_span / 2):
        sk -= Pos(x, 0) * Circle((P.gland_stud_m + 1) / 2)
    return extrude(sk, amount=P.barrel_flange_t), sk


def gland_plate():
    """Follower plate.  Pushes the printed follower bushing into the box."""
    sk = (Rectangle(P.gland_stud_span + 40, 60)
          - Circle((P.sleeve_od + 2) / 2))
    for x in (-P.gland_stud_span / 2, P.gland_stud_span / 2):
        sk -= Pos(x, 0) * Circle((P.gland_stud_m + 1) / 2)
    return extrude(sk, amount=P.gland_plate_t), sk
