"""Geometry self-checks.  Run automatically by build_all.py.

These exist because five real errors got through review and were only caught by
measuring the models: a flight that tapered to 2 mm and swelled the OD past the
barrel clearance, a >360 deg helical extrude that silently dropped the hub, a
follower shoulder that fouled the box rim, a throat collar 30 mm too tall, and
a strap with no arch over the stator.  Measure the model, don't trust the code.
"""
from _common import *
import plates, printed, conrod, hopper, manifest, jigs, assembly, assembly

SPLIT = {"auger_pin_drill_jig", "joint_boot_clamp"}   # deliberately two-piece


def check():
    fails = []

    def want(cond, msg):
        if not cond:
            fails.append(msg)

    # --- printed parts: single solid, and they fit where they must fit
    parts = {
        "auger_segment": printed.auger_segment(),
        "auger_scavenger": printed.auger_segment(seg_len=P.auger_tail_len),
        "gland_follower": printed.gland_follower(),
        "lantern_ring": printed.lantern_ring(),
        "stator_cradle": printed.stator_cradle(),
        "stator_strap": printed.stator_strap(),
        "auger_pin_drill_jig": printed.auger_pin_jig(),
        "joint_boot_clamp": printed.joint_boot_clamp(),
    }
    for n, s in parts.items():
        n_expected = 2 if n in SPLIT else 1
        want(len(s.solids()) == n_expected,
             f"{n}: {len(s.solids())} solids, expected {n_expected}")

    for n in ("auger_segment", "auger_scavenger"):
        b = parts[n].bounding_box()
        want(abs(b.size.X - P.auger_od) < 0.3,
             f"{n}: swept OD {b.size.X:.2f} != auger_od {P.auger_od:.2f} "
             f"-- flight section is not a true angular wedge")
        want(b.size.X < P.barrel_id - 2 * (P.auger_radial_clear - 0.5),
             f"{n}: OD {b.size.X:.2f} fouls the barrel bore {P.barrel_id:.2f}")

    b = parts["gland_follower"].bounding_box()
    want(b.size.X < P.gland_box_od,
         f"gland_follower shoulder {b.size.X:.1f} >= box OD {P.gland_box_od:.1f}: "
         f"it would bottom on the box rim before it loads the packing")
    want(b.size.X > P.gland_box_id,
         "gland_follower shoulder would disappear into the box bore")

    b = parts["stator_strap"].bounding_box()
    want(b.size.Z > P.stator_od / 2 + 10,
         "stator_strap has no arch over the stator -- it is two loose legs")

    # --- steel plates
    ap, ap2 = plates.adapter_plate()
    want(abs(ap.bounding_box().size.X - P.plate_size) < 1e-6, "adapter plate size")
    want(P.plate_size / 2 > P.tie_xy + P.spacer_od / 2,
         "tie-rod spacers hang off the edge of the clamp plates")
    want(P.tie_bc / 2 - P.spacer_od / 2 > P.stator_od / 2,
         "tie-rod spacers foul the stator OD")
    want(P.adapter_bore <= P.barrel_id,
         "adapter bore is larger than the barrel bore -- a ledge for grout")

    # --- hopper
    ce = hopper.collar_end().bounding_box()
    cs = hopper.collar_side().bounding_box()
    want(abs(ce.size.Y - cs.size.Y) < 1.0,
         f"throat collar ends ({ce.size.Y:.1f}) and sides ({cs.size.Y:.1f}) are "
         f"different heights -- they will not weld into a box")
    want(P.hop_ang_long > 60 and P.hop_ang_short > 60,
         f"hopper walls at {P.hop_ang_short:.0f}/{P.hop_ang_long:.0f} deg -- "
         f"wet grout needs > 60 deg or it bridges")

    # --- printed parts: every model single-solid and inside the bed
    for r in manifest.rows():
        n_exp = manifest.EXPECT_SOLIDS.get(r["name"], 1)
        if n_exp is not None:
            want(r["solids"] == n_exp,
                 f"{r['name']}: {r['solids']} solids, expected {n_exp} "
                 f"(a split part means a boolean or an emboss did not fuse)")
        bx, by, bz = r["bbox"]
        want(bx <= P.printer_x and by <= P.printer_y and bz <= P.printer_z,
             f"{r['name']}: {bx:.0f} x {by:.0f} x {bz:.0f} exceeds the "
             f"{P.printer_x:.0f} x {P.printer_y:.0f} x {P.printer_z:.0f} bed")

    # --- fit coupons: every rung must be one solid and the plate must fit
    import coupons
    for nm, s in coupons.coupon_set():
        want(len(s.solids()) == 1,
             f"coupon {nm}: {len(s.solids())} solids -- a floating emboss")
    cw, cd, ch = coupons.plate_size()
    want(cw <= P.printer_x and cd <= P.printer_y and ch <= P.printer_z,
         f"fit coupon plate {cw:.0f} x {cd:.0f} x {ch:.0f} exceeds the bed")

    # --- drill drive station
    import frame_drawing as fdw
    axis = (fdw.DRILL_TOP + P.cradle_plate_t + P.cradle_foot_t
            + P.cradle_wall + P.drill_body_dia / 2)
    want(abs(axis - P.barrel_cl_h) < 0.5,
         f"drill axis lands at z={axis:.1f}, pump axis is at {P.barrel_cl_h:.1f} -- "
         f"the chuck would not be coaxial with the hex stub")
    want(P.hex_free_len >= P.drill_chuck_depth + 20,
         "hex stub too short: the chuck would bottom on the stub sleeve")
    want(P.x_torque_lug != P.x_drill_cradle,
         "torque lug and printed saddle are at the same station -- the printed "
         "part would end up in the torque path")
    want(P.x_hex_back < P.x_shaft_rear,
         "hex stub does not project rearward of the shaft")

    # --- post jigs must match the post SHAPE, and the posts are not the barrel
    want(P.post_shape in ("square", "round"),
         f"post_shape {P.post_shape!r} is neither 'square' nor 'round'")
    if P.post_shape == "square":
        want(abs(P.post_area_mm2 - P.post_id ** 2) < 1e-6,
             "square post bore area is not side^2")
    else:
        want(abs(P.post_area_mm2 - 3.141592653589793 / 4 * P.post_id ** 2) < 1e-6,
             "round post bore area is not pi/4 d^2")
    # Both shapes share one convention: foot contact face at x = -datum,
    # bushing at x = 0, body ending at x = +45.  So one check covers both.
    for nm, jf, datum in (("port", jigs.jig_post_port, P.post_port_height),
                          ("vent", jigs.jig_post_vent, P.post_vent_from_top)):
        bb = jf()[0].bounding_box()
        want(abs(bb.size.X - (datum + 14 + 45)) < 1.5,
             f"post {nm} jig is {bb.size.X:.0f} long; datum leg should make it "
             f"{datum + 59:.0f}, so the bushing is exactly {datum:.0f} from the "
             f"post end")
        want(abs(bb.min.X + datum + 14) < 1.5,
             f"post {nm} jig foot is not at x = -{datum + 14:.0f}")
        want(bb.min.Z > -0.01,
             f"post {nm} jig sits below the bed plane -- it will not slice as modelled")

    if P.post_shape == "square":
        # The jig must clear the post everywhere along the post's own length.
        # If it does not, it simply will not go on -- and you find out with a
        # 6 m post on trestles and a drill in your hand.
        S = P.post_side
        for nm, datum, hole, scr in (
                ("port", P.post_port_height, 6.4, P.post_port_hole),
                ("vent", P.post_vent_from_top, P.post_vent_dia, None)):
            u = jigs._post_jig_square(datum, hole, "FIT", scribe_d=scr,
                                      oriented=False)[0]
            post = Pos(-datum + 400, 0, 0) * Box(800, S, S)
            hit = u & post                      # None == no intersection at all
            clash = hit.volume if hit is not None else 0.0
            want(clash < 50.0,
                 f"post {nm} jig fouls the post envelope by {clash:.0f} mm3 -- "
                 f"it will not slide on")

    # --- layout sanity
    want(P.x_auger_front < P.x_adapter_back,
         f"auger front x={P.x_auger_front:.0f} is not behind the adapter plate "
         f"back face x={P.x_adapter_back:.0f} -- it would run into the plate")
    want(P.x_adapter_back - P.x_auger_front >= 15,
         "less than 15 mm between the auger and the adapter plate")
    want(abs(P.x_auger_back - P.x_cover_back) <= 20,
         "dead annulus in front of the gland that the flush cannot reach")
    want(P.conrod_len >= 20 * P.rotor_eccentricity,
         "con-rod too short for the rotor eccentricity")
    # --- THE ASSEMBLY: no two bodies may share volume unless the fit is
    # intended and named.  This is the check that found the shaft nose sitting
    # 200 mm inside the con-rod's space, the stator cradle straddling the tie
    # rods, the hex stub inside the rear pillow block, and the strap
    # duplicating the cradle's lower half.
    for n1, n2, v in assembly.clashes():
        fails.append(f"assembly: {n1} and {n2} interpenetrate by {v:.0f} mm3 "
                     f"-- not an intended fit")

    # --- THE ASSEMBLY: no two bodies may share volume unless the fit is
    # intended and named in assembly.INTENDED_FITS.  This is the check that
    # found the shaft nose sitting 200 mm inside the con-rod's space, the
    # stator cradle straddling the tie rods, the hex stub inside the rear
    # pillow block, and the strap duplicating the cradle's lower half.
    for n1, n2, v in assembly.clashes():
        fails.append(f"assembly: {n1} and {n2} interpenetrate by {v:.0f} mm3 "
                     f"-- not an intended fit")

    return fails


if __name__ == "__main__":
    f = check()
    print("\n".join("  FAIL " + x for x in f) if f else "  geometry checks: all pass")
    raise SystemExit(1 if f else 0)
