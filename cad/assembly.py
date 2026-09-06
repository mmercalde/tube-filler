"""Assembly export.

Places every on-machine component at its params.py station and emits

    out/machine_assembly.step   -- one named body per component
    out/assembly_iso.png        -- hidden-line isometric

Nothing here remodels a part.  Real components come from the existing builders
in plates / printed / conrod / jigs / ops and are only MOVED.  Things that have
no solid model because they are bought or are raw stock -- the barrel tube, the
stator, the rotor, the pillow blocks, the packing, the frame members, the drill
-- appear as simple envelopes derived from params, named with an `_ENV` suffix
so nobody mistakes one for a drawing.

Machine coordinates, same as the weldment drawing:
    x  along the barrel, 0 = FRONT FACE of the adapter plate, +x to the discharge
    y  across, +y = operator side
    z  up from the ground; the pump axis is at z = barrel_cl_h
"""
from _common import *
import plates, printed, conrod, ops, frame_drawing as fd

AX = P.barrel_cl_h                      # pump axis height


# --------------------------------------------------------------- placement
def on_axis(part, x0, flip=False):
    """Put a part whose local +Z is its own axis onto the pump axis.

    flip=False: local z=0 lands at x0 and +z runs toward the discharge.
    flip=True : local z=0 lands at x0 and +z runs toward the drive.
    """
    return Pos(x0, 0, AX) * (Rot(0, -90, 0) if flip else Rot(0, 90, 0)) * part


def tube(x0, x1, od, idd=0.0):
    t = Pos(x0, 0, AX) * Rot(0, 90, 0) * extrude(Circle(od / 2), amount=x1 - x0)
    if idd:
        t -= Pos(x0 - 1, 0, AX) * Rot(0, 90, 0) * extrude(
            Circle(idd / 2), amount=x1 - x0 + 2)
    return t


def named(shape, label):
    shape.label = label
    return shape


# ------------------------------------------------------------------ bodies
def bodies():
    """[(label, group, solid)].  group drives the clash allow-list."""
    B = []
    def add(label, group, shape):
        B.append((label, group, shape))

    # ---------- wetted steel, from the real part builders ----------
    add("adapter_plate", "weld_barrel", on_axis(plates.adapter_plate()[0],
                                                P.x_adapter_back))
    add("discharge_head", "clamp", on_axis(plates.discharge_head(), P.spacer_len))
    add("barrel_rear_flange", "weld_barrel",
        on_axis(plates.barrel_rear_flange()[0], P.x_flange_back))
    add("barrel_rear_cover", "gland",
        on_axis(plates.barrel_rear_cover()[0], P.x_cover_back))
    add("gland_plate", "gland", on_axis(plates.gland_plate()[0], P.x_gland_plate))

    # ---------- drive train ----------
    add("drive_shaft", "shaft", on_axis(conrod.drive_shaft(), P.x_shaft_nose))
    add("hex_stub", "shaft", on_axis(conrod.hex_stub(),
                                     P.x_shaft_rear + P.hex_sleeve_len, flip=True))
    add("conrod", "joint", on_axis(conrod.conrod(),
                                   (P.x_rotor_pin + P.x_shaft_pin) / 2))
    # tongue: local Y -> machine X, local Z (its 12 mm thickness) -> machine Y,
    # and centred on the axis -- it was hanging 6 mm off it, which put its
    # corners outside the auger bore.
    tg = Rot(0, 0, -90) * (Rot(0, 90, 0) * conrod.shaft_tongue()[0])
    add("shaft_tongue", "joint",
        Pos(P.x_shaft_nose - P.tongue_slot, P.tongue_t / 2, AX) * tg)

    # ---------- printed, wetted ----------
    s0 = 0.0
    for i in range(P.n_auger_full):
        add(f"auger_segment_{i+1}", "auger",
            on_axis(printed.auger_segment(), P.x_auger_front - s0, flip=True))
        s0 += P.auger_seg_len
    if P.auger_tail_len > 1:
        add("auger_scavenger", "auger",
            on_axis(printed.auger_segment(seg_len=P.auger_tail_len),
                    P.x_auger_front - s0, flip=True))
    add("gland_follower", "gland",
        on_axis(printed.gland_follower(), P.x_follower_deep, flip=True))
    add("lantern_ring", "gland",
        on_axis(printed.lantern_ring(), P.x_lantern_deep, flip=True))
    add("stator_cradle", "cradle",
        Pos(P.x_stator_cradle, 0, P.top_rail_top) * Rot(0, 0, 90)
        * printed.stator_cradle())
    # the strap is modelled valley-up for printing; in use it is inverted
    strap_h = P.stator_od / 2 + 0.5 + 16.0
    add("stator_strap", "cradle",
        Pos(P.x_stator_cradle, 0, AX + strap_h) * Rot(180, 0, 0)
        * Rot(0, 0, 90) * printed.stator_strap())

    # ---------- printed, drive station ----------
    z_plate = fd.DRILL_TOP + P.cradle_plate_t
    add("drill_cradle_saddle", "drill",
        Pos(P.x_drill_cradle, 0, z_plate) * ops.drill_cradle_saddle())
    add("drill_cradle_strap", "drill",
        Pos(P.x_drill_cradle, 0, AX) * ops.drill_cradle_strap())

    # ---------- printed, hopper ----------
    xh = P.x_hop_bot_front - P.hop_bot_l / 2
    zt = AX + P.collar_top_z + P.hop_depth
    for sx in (-1, 1):
        for sy in (-1, 1):
            add(f"hopper_guard_tile_{'FR'[sx>0]}{'LR'[sy>0]}", "hopper",
                Pos(xh + sx * P.hop_top_l / 4, sy * P.hop_top_w / 4, zt)
                * ops.hopper_guard_tile())

    # ---------- envelopes: bought or raw stock ----------
    slot = Pos(P.x_hop_bot_front - P.hop_bot_l / 2, 0, AX + P.barrel_od / 2) * Box(
        P.barrel_slot_l, P.barrel_slot_w, P.barrel_od,
        align=(Align.CENTER, Align.CENTER, Align.MIN))
    add("barrel_tube_ENV", "weld_barrel",
        tube(P.x_barrel_back, P.x_barrel_front, P.barrel_od, P.barrel_id) - slot)
    add("stator_ENV", "clamp",
        tube(0.0, P.spacer_len, P.stator_od, P.stator_inlet_bore))
    add("rotor_ENV", "joint",
        tube(P.x_rotor_tip, P.spacer_len - 20, P.stator_inlet_bore - 8))
    add("shaft_sleeve_ENV", "gland",
        tube(P.x_sleeve_back, P.x_sleeve_front, P.sleeve_od, P.sleeve_id))
    add("stuffing_box_ENV", "gland",
        tube(P.x_gland_back, P.x_cover_back, P.gland_box_od, P.gland_box_id))
    for i in range(P.packing_rings):
        z0 = P.x_cover_back - i * P.packing_sq - (P.lantern_len if i >= 2 else 0)
        add(f"packing_ring_{i+1}_ENV", "gland",
            tube(z0 - P.packing_sq, z0, P.gland_box_id, P.sleeve_od))
    for i, (sx, sy) in enumerate([(a, b) for a in (-1, 1) for b in (-1, 1)]):
        y, z = sx * P.tie_xy, sy * P.tie_xy
        rod = Pos(P.x_adapter_back - 18, y, AX + z) * Rot(0, 90, 0) * extrude(
            Circle(P.tie_rod_m / 2), amount=P.spacer_len + 2 * P.plate_t + 36)
        sp = Pos(0, y, AX + z) * Rot(0, 90, 0) * (
            extrude(Circle(P.spacer_od / 2), amount=P.spacer_len)
            - extrude(Circle(P.spacer_id / 2), amount=P.spacer_len))
        add(f"tie_rod_{i+1}_ENV", "clamp", rod)
        add(f"tie_spacer_{i+1}_ENV", "clamp", sp)
    for nm, x in (("front", P.x_pb_front), ("rear", P.x_pb_rear)):
        pb = Pos(x, 0, AX - 42.9) * Box(50, 160, 130,
                                        align=(Align.CENTER, Align.CENTER, Align.MIN))
        pb -= Pos(x - 30, 0, AX) * Rot(0, 90, 0) * extrude(
            Circle(P.shaft_dia / 2), amount=60)
        add(f"pillow_block_{nm}_ENV", "bearing", pb)
    add("pb_subplate_ENV", "bearing",
        Pos((P.x_pb_front + P.x_pb_rear) / 2, 0, AX - 42.9 - 10)
        * Box(abs(P.x_pb_front - P.x_pb_rear) + 80, 160, 10,
              align=(Align.CENTER, Align.CENTER, Align.MIN)))
    for i, x in enumerate((-100.0, -520.0)):
        sd = Pos(x, 0, P.top_rail_top) * Box(
            6, 120, P.barrel_saddle_h + P.barrel_od / 2,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
        sd -= tube(x - 5, x + 5, P.barrel_od)
        add(f"barrel_saddle_{i+1}_ENV", "weld_barrel", sd)

    # hopper shell + throat
    zb = AX + P.collar_top_z
    add("hopper_ENV", "hopper", (
        loft([Plane.XY.offset(zb) * Rectangle(P.hop_bot_l, P.hop_bot_w),
              Plane.XY.offset(zt) * Rectangle(P.hop_top_l, P.hop_top_w)])
        - loft([Plane.XY.offset(zb - 1) * Rectangle(P.hop_bot_l - 6, P.hop_bot_w - 6),
                Plane.XY.offset(zt + 1) * Rectangle(P.hop_top_l - 6, P.hop_top_w - 6)])
    ).moved(Location((xh, 0, 0))))

    # drive station steel
    # ONE steel bracket: half-round torque lug at the front edge, flat behind
    # it for the printed saddle.  Both welded to the same upright.
    lug = Pos(P.x_torque_lug, 0, fd.DRILL_TOP) * Box(
        10, 90, AX - fd.DRILL_TOP - 4, align=(Align.CENTER, Align.CENTER, Align.MIN))
    lug -= tube(P.x_torque_lug - 8, P.x_torque_lug + 8, P.drill_aux_handle_dia + 1.0)
    add("drill_torque_lug_ENV", "drill", lug)
    add("drill_cradle_plate_ENV", "drill",
        Pos(P.x_drill_cradle, 0, fd.DRILL_TOP) * Box(
            P.cradle_plate_l, 180, P.cradle_plate_t,
            align=(Align.CENTER, Align.CENTER, Align.MIN)))
    add("throat_collar_ENV", "hopper",
        (Pos(P.x_hop_bot_front - P.hop_bot_l / 2, 0, AX) * Box(
            P.hop_bot_l, P.hop_bot_w, P.collar_top_z,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
         - Pos(P.x_hop_bot_front - P.hop_bot_l / 2, 0, AX) * Box(
            P.hop_bot_l - 6, P.hop_bot_w - 6, P.collar_top_z,
            align=(Align.CENTER, Align.CENTER, Align.MIN))
         - tube(P.x_barrel_back, P.x_barrel_front, P.barrel_od)))

    # the drill itself -- envelope only, straight off the measured dimensions,
    # so the clearances in this model are the real ones
    add("DRILL_ENV", "drill",
        tube(P.x_chuck_back, P.x_chuck_front, 52.0)
        + tube(P.x_chuck_back - P.drill_body_len, P.x_chuck_back, P.drill_body_dia)
        + tube(P.x_torque_lug - 12, P.x_torque_lug + 12, P.drill_aux_handle_dia))

    # frame, straight from the weldment member list
    for i, (nm, stock, a, b) in enumerate(fd.MEMBERS):
        d = Vector(b) - Vector(a)
        L = d.length
        if L < 1:
            continue
        add(f"frame_{i+1:02d}_{nm.replace(' ', '_')}_ENV", "frame",
            Plane(origin=a, z_dir=d.normalized()) * Box(
                P.ptr_size, P.ptr_size, L,
                align=(Align.CENTER, Align.CENTER, Align.MIN)))
    return B


def assembly():
    parts = [named(s, n) for n, g, s in bodies()]
    asm = Compound(children=parts)
    asm.label = "TUBE-FILLER"
    return asm


# ---------------------------------------------------------------- clashes
# Bodies inside these groups are welded or press-fitted stacks: they are
# MODELLED overlapping on purpose, because that is what a weld prep is.
WELDED_GROUPS = {"frame", "gland", "weld_barrel"}

# Everything else that is allowed to interpenetrate, named explicitly.
# fnmatch patterns, unordered.  If a pair is not on this list and the solids
# share volume, it is a mistake.
INTENDED_FITS = [
    ("drive_shaft", "auger_segment_*"),      # auger keyed on the shaft
    ("drive_shaft", "auger_scavenger"),
    ("drive_shaft", "shaft_sleeve_ENV"),     # sacrificial sleeve over the shaft
    ("drive_shaft", "hex_stub"),             # stub sleeve over the shaft rear
    ("drive_shaft", "shaft_tongue"),         # tongue plug-welded into the nose
    ("drive_shaft", "pillow_block_*"),       # bearing bore
    ("shaft_tongue", "conrod"),              # rear fork straddles the tongue
    ("conrod", "rotor_ENV"),                 # front fork straddles the rotor eye
    ("stator_ENV", "stator_cradle"),         # stator sits in the cradle
    ("stator_ENV", "stator_strap"),
    ("stator_ENV", "adapter_plate"),         # clamped face to face
    ("stator_ENV", "discharge_head"),
    ("DRILL_ENV", "hex_stub"),               # the chuck grips the stub
    ("DRILL_ENV", "drill_cradle_saddle"),
    ("DRILL_ENV", "drill_cradle_strap"),
    ("DRILL_ENV", "drill_torque_lug_ENV"),
    ("drill_cradle_saddle", "drill_cradle_plate_ENV"),
    ("barrel_tube_ENV", "hopper_ENV"),       # throat welded through the slot
    ("barrel_tube_ENV", "barrel_saddle_*"),
    ("barrel_tube_ENV", "conrod"),           # con-rod runs inside the barrel
    ("barrel_tube_ENV", "auger_segment_*"),
    ("barrel_tube_ENV", "auger_scavenger"),
    ("barrel_tube_ENV", "drive_shaft"),
    ("barrel_tube_ENV", "shaft_tongue"),
    ("barrel_tube_ENV", "rotor_ENV"),
    ("barrel_tube_ENV", "shaft_sleeve_ENV"),
    ("adapter_plate", "rotor_ENV"),          # rotor passes the adapter bore
    ("adapter_plate", "tie_rod_*"),          # rods through their clearance holes
    ("adapter_plate", "tie_spacer_*"),       # spacers land on the plate face
    ("discharge_head", "tie_rod_*"),
    ("discharge_head", "tie_spacer_*"),
    ("discharge_head", "rotor_ENV"),
    ("tie_rod_*", "tie_spacer_*"),           # rod runs down the spacer bore
    ("pb_subplate_ENV", "pillow_block_*"),
    ("frame_*", "pb_subplate_ENV"),
    ("frame_*", "drill_cradle_plate_ENV"),
    ("frame_*", "drill_torque_lug_ENV"),
    ("frame_*", "barrel_saddle_*"),
    ("frame_*", "stator_cradle"),
    ("frame_*", "hopper_ENV"),
    ("hopper_ENV", "hopper_guard_tile_*"),
    ("hopper_guard_tile_*", "hopper_guard_tile_*"),   # tiles lap on two edges
    ("hopper_ENV", "throat_collar_ENV"),
    ("throat_collar_ENV", "barrel_tube_ENV"),
    ("drill_torque_lug_ENV", "drill_cradle_plate_ENV"),   # one welded bracket
    ("drill_cradle_saddle", "drill_torque_lug_ENV"),
]


def _allowed(n1, g1, n2, g2):
    from fnmatch import fnmatch
    if g1 == g2 and g1 in WELDED_GROUPS:
        return True
    for a, b in INTENDED_FITS:
        if (fnmatch(n1, a) and fnmatch(n2, b)) or (fnmatch(n1, b) and fnmatch(n2, a)):
            return True
    return False


def clashes(tol=25.0):
    """Every unordered pair, bounding-box pre-filtered.  Returns the ones that
    share more than `tol` mm3 and are not on the intended-fit list."""
    B = bodies()
    boxes = [(n, g, s, s.bounding_box()) for n, g, s in B]
    out = []
    for i in range(len(boxes)):
        n1, g1, s1, b1 = boxes[i]
        for j in range(i + 1, len(boxes)):
            n2, g2, s2, b2 = boxes[j]
            if (b1.max.X < b2.min.X or b2.max.X < b1.min.X or
                    b1.max.Y < b2.min.Y or b2.max.Y < b1.min.Y or
                    b1.max.Z < b2.min.Z or b2.max.Z < b1.min.Z):
                continue
            if _allowed(n1, g1, n2, g2):
                continue
            hit = s1 & s2
            v = hit.volume if hit is not None else 0.0
            if v > tol:
                out.append((n1, n2, v))
    return sorted(out, key=lambda t: -t[2])


# ----------------------------------------------------------------- export
def export(out_dir=OUT):
    """STEP with one named body per component, plus a hidden-line iso SVG.
    build_all rasterises the SVG to assembly_iso.png if a browser is present."""
    import os
    asm = assembly()
    step = os.path.join(out_dir, "machine_assembly.step")
    export_step(asm, step)

    svg = os.path.join(out_dir, "assembly_iso.svg")
    # Eye well back so the perspective stays gentle; hidden lines dropped --
    # with 76 bodies they are noise, not information.
    vis, _hid = asm.project_to_viewport(
        viewport_origin=(7000, -8500, 6000),
        viewport_up=(0, 0, 1),
        look_at=(-450, 0, 830))
    ex = ExportSVG(unit=Unit.MM, margin=10, fit_to_stroke=True)
    ex.add_layer("visible", line_color=(0, 0, 0), line_weight=0.26)
    ex.add_shape(list(vis), layer="visible")
    ex.write(svg)
    _px(svg, 1600)
    return step, svg


def _px(path, width_px):
    """Force a pixel size on the SVG so a headless browser renders all of it
    instead of the top-left corner of a 3 m-wide page."""
    import re
    t = open(path).read()
    m = re.search(r'viewBox="([-\d. ]+)"', t)
    if not m:
        return
    _, _, w, h = [float(v) for v in m.group(1).split()]
    hp = int(round(width_px * h / w))
    t = re.sub(r'width="[^"]+"', f'width="{width_px}"', t, count=1)
    t = re.sub(r'height="[^"]+"', f'height="{hp}"', t, count=1)
    open(path, "w").write(t)
    return width_px, hp
