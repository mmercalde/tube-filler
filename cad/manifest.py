"""The print registry.  One list, used for BOTH the STL export and
print_manifest.md, so the manifest cannot drift from what was exported.

Columns: stl name, factory, qty, group, material, walls, infill %,
         print orientation, life, note
"""
from _common import *
import printed, jigs, ops, coupons

RHO = {"PETG": 1.27, "ASA": 1.07}          # g/cm3
V, J, O, C = "WETTED", "FAB JIG", "OPERATIONAL", "FIT COUPON"

# Models that are legitimately more than one solid.  None = any count.
EXPECT_SOLIDS = {"joint_boot_clamp": 2, "fit_coupons": None}


def _reg():
    R = []
    a = R.append
    # ---------------- fit coupons: PRINT THESE FIRST -----------------------
    a(("fit_coupons", coupons.plate, 1, C, "PETG", 3, 30,
       "as laid out -- each coupon is already in its parent part's orientation",
       "print first, then discard",
       "20 coupons on one plate: 5 rungs each of the auger bore, the post "
       "corner channel, a template drill bushing and the dust-cap barb. "
       "Try every rung on real stock, then set print_clearance."))
    # ---------------- wetted / machine parts (unchanged rules) --------------
    a((f"auger_segment_p{P.auger_pitch:.0f}", printed.auger_segment, P.n_auger_full,
       V, "PETG", 4, 100, "axis vertical, flat face down",
       "consumable", "flight self-supports: 97% layer overlap. No supports."))
    if P.auger_tail_len > 1:
        a((f"auger_scavenger_p{P.auger_pitch:.0f}_L{P.auger_tail_len:.0f}",
           lambda: printed.auger_segment(seg_len=P.auger_tail_len), 1,
           V, "PETG", 4, 100, "axis vertical", "consumable",
           "sweeps the annulus in front of the gland"))
    a((f"auger_segment_p{P.auger_pitch_alt:.0f}_SPARE",
       lambda: printed.auger_segment(pitch=P.auger_pitch_alt), P.n_auger_full,
       V, "PETG", 4, 100, "axis vertical", "spare",
       "coarser pitch. Print only if the primary auger starves."))
    a(("gland_follower", printed.gland_follower, 3, V, "PETG", 4, 100,
       "shoulder down", "consumable", "compression only, fully supported in the bore"))
    a(("lantern_ring", printed.lantern_ring, 3, V, "PETG", 4, 100,
       "flat", "consumable", "grease distribution; not a seal"))
    a(("stator_cradle", printed.stator_cradle, 1, V, "ASA", 4, 40,
       "saddle up, flat base down", "permanent", "non-structural alignment only"))
    a(("stator_strap", printed.stator_strap, 1, V, "ASA", 4, 40,
       "arch up as modelled", "permanent", "finger tight only"))
    a(("joint_boot_clamp", printed.joint_boot_clamp, 2, V, "PETG", 3, 40,
       "flat", "permanent", "retains an inner-tube boot over the pin joint"))

    # ---------------- fab jigs: one-time shop tools ------------------------
    a(("jig_barrel_hopper_slot", lambda: jigs.jig_barrel_hopper_slot()[0], 1,
       J, "PETG", 3, 15, "vee mouth down, as modelled", "one-time jig",
       "strapped V-saddle. Chain-drill 6.4 through every bushing."))
    a(("jig_barrel_rear_flange",
       lambda: jigs.jig_barrel_end_ring(P.barrel_bolt_bc, P.barrel_bolt_m + 1,
                                        "REAR FLANGE"), 1,
       J, "PETG", 3, 20, "flat disc down", "one-time jig",
       "registers on the barrel OD; bolt circle concentric with the tube"))
    a(("jig_barrel_tie_rods",
       lambda: jigs.jig_barrel_end_ring(P.tie_bc, P.tie_rod_hole, "TIE RODS"), 1,
       J, "PETG", 3, 20, "flat disc down", "one-time jig",
       "same, for the adapter-plate tie-rod circle"))
    _sq = P.post_shape == "square"
    _po = ("outer corner down, both legs at 45 deg" if _sq else "vee mouth down")
    _pk = ("corner channel on two adjacent faces of the square PTR"
           if _sq else "V-saddle on the round tube")
    a(("jig_post_port", lambda: jigs.jig_post_port()[0], 1, J, "PETG", 3, 15,
       _po, "one-time jig",
       f"{_pk}. Used 12 times. Foot butts the post BASE; port centred on the "
       f"face at {P.post_port_height:.0f} mm."))
    a(("jig_post_vent", lambda: jigs.jig_post_vent()[0], 1, J, "PETG", 3, 15,
       _po, "one-time jig",
       f"{_pk}. Used 12 times. Foot butts the post TOP; vent "
       f"{P.post_vent_from_top:.0f} mm down."))
    a(("template_adapter_plate", jigs.template_adapter_plate, 1, J, "PETG", 3, 20,
       "flat, bushings up", "one-time jig", "1:1. Outline is also the cut mark."))
    a(("template_discharge_flange", jigs.template_discharge_rear, 1, J, "PETG", 3, 20,
       "flat, bushings up", "one-time jig", "1:1"))
    a(("template_barrel_rear_flange", jigs.template_barrel_flange, 1, J, "PETG", 3, 20,
       "flat, bushings up", "one-time jig", "1:1"))
    a(("fixture_ptr_corner_SACRIFICIAL", jigs.fixture_ptr_corner, 2, J, "PETG", 3, 20,
       "heel down as modelled", "SACRIFICIAL",
       "TACK ONLY. Remove before weld-out or you melt it into the joint."))
    a(("fixture_ptr_tee_SACRIFICIAL", jigs.fixture_ptr_tee, 2, J, "PETG", 3, 20,
       "flat, pockets up", "SACRIFICIAL", "TACK ONLY. Remove before weld-out."))
    a(("gauge_tie_rod_spacers", jigs.gauge_tie_rod, 1, J, "PETG", 3, 20,
       "flat", "one-time jig",
       "two lanes: SERVICE and BREAK-IN. All four spacers must gauge the same."))

    # ---------------- operational parts ------------------------------------
    a(("drill_cradle_saddle", ops.drill_cradle_saddle, 1, O, "ASA", 5, 60,
       "foot down, cradle up", "permanent",
       "CLAMPING LOAD ONLY. Torque goes through the steel lug and upright."))
    a(("drill_cradle_strap", ops.drill_cradle_strap, 1, O, "ASA", 5, 60,
       "as modelled, teardrop bore down", "permanent",
       "line it with inner tube; you are clamping a plastic gearcase"))
    a(("hopper_guard_tile", ops.hopper_guard_tile, 4, O, "ASA", 4, 30,
       "flat", "permanent",
       "drops into the welded steel rim; the STEEL bars carry the load"))
    half = not ops.screen_fits()
    sfx = "_HALF" if half else ""
    nq = 2 if half else 1
    a((f"sand_screen_frame{sfx}", ops.sand_screen_frame, nq, O, "ASA", 4, 30,
       "lip down", "permanent",
       "1/8in hardware cloth. THIS is the <=3 mm sieve."
       + (" Splits in two: your bucket is wider than the bed. The cloth is one "
          "piece, so the seam leaks nothing." if half else "")))
    a((f"sand_screen_retainer{sfx}", ops.sand_screen_retainer, nq, O, "ASA", 4, 30,
       "flat", "permanent", "8 x M4 traps the cloth"
       + (" (plus 2 x M4 at each seam)" if half else "")))
    a(("hopper_funnel", ops.hopper_funnel, 1, O, "ASA", 3, 15,
       "small end down", "permanent", "walls lean ~14 deg from vertical; no supports"))
    a(("npt_dust_cap", ops.npt_dust_cap, 12, O, "PETG", 3, 30,
       "flange down", "consumable", "debris cap, NOT a pressure cap"))
    a(("packing_cone", ops.packing_cone, 1, O, "PETG", 4, 40,
       "spigot down", "permanent", "seats each ring square in the box"))
    a(("packing_drift", ops.packing_drift, 2, O, "PETG", 4, 60,
       "flange up, split face down", "permanent", "half-shell; two make a tube"))
    return R


REGISTRY = _reg()


def rows():
    out = []
    for name, fac, qty, grp, mat, walls, infill, orient, life, note in REGISTRY:
        s = fac()
        bb = s.bounding_box()
        vol = s.volume / 1000.0                       # cm3
        # shells + infill, not a flat fudge: big chunky jigs at 15% infill are
        # mostly air, and a flat multiplier overstates them by 2-3x.
        shell = s.area / 100.0 * (walls * 0.42) / 10.0     # cm3 of perimeter
        shell = min(shell, vol)
        mass = (shell + (vol - shell) * infill / 100.0) * RHO[mat]
        out.append(dict(name=name, shape=s, qty=qty, group=grp, mat=mat,
                        walls=walls, infill=infill, orient=orient, life=life,
                        note=note, vol=vol, mass=mass,
                        bbox=(bb.size.X, bb.size.Y, bb.size.Z),
                        solids=len(s.solids())))
    return out


def render(rws):
    L = []
    w = L.append
    w("# PRINT MANIFEST -- TUBE-FILLER\n")
    w("<!-- GENERATED by cad/manifest.py.  Do not edit: run `python cad/build_all.py`. -->\n")
    w("Bambu H2C, 0.4 mm nozzle, 0.2 mm layers.  **No supports on any part** -- every")
    w("model is emitted in its print orientation and every overhang is at 45 degrees")
    w("or steeper.  Where a part is listed as ASA, the reason is UV and heat: it lives")
    w("outdoors or against a warm drill.  Everything else is PETG.\n")
    w(f"Bed checked against {P.printer_x:.0f} x {P.printer_y:.0f} x {P.printer_z:.0f} mm "
      f"(`printer_x/y/z` in params.py -- confirm against your machine).\n")
    w("\n## Fit tuning -- do this before you batch anything\n")
    w("Every printed feature that has to fit real steel is derived from **one**")
    w("number, so one measurement retunes the whole project:\n")
    w("| parameter | now | governs |")
    w("|---|--:|---|")
    w(f"| `print_clearance` | {P.print_clearance:.2f} mm | DIAMETRAL clearance of a "
      "printed feature over real stock: auger cross-pin holes, jig register faces "
      "on the tube and on the square post, drill bushings on the bit, cradle on the "
      "stator, drill saddle on the drill body, gland follower in its box, PTR weld "
      "fixtures. Applied as half of it where the feature is a face or a radius. |")
    w(f"| `print_interference` | {P.print_interference:.2f} mm | DIAMETRAL "
      "*oversize* of a printed barb that must grip -- the NPT dust caps, and nothing "
      "else. Tuned in the opposite direction. |")
    w(f"| `running_clearance` | {P.running_clearance:.2f} mm | NOT a fit: the gap in "
      "a printed bore around something that turns in it (gland follower and lantern "
      "ring on the rotating shaft sleeve). Do not tune this from a coupon. |")
    w(f"| `auger_bore_clear` | {P.auger_bore_clear:.2f} mm | NOT a fit either: the "
      f"auger hub bore over the {P.shaft_dia:.0f} mm shaft, fixed at a loose slide. The "
      f"{P.xpin_dia:.0f} mm cross pin locates the segment and carries the drive, so the "
      "bore only has to go on and come off a wet, gritty shaft with five segments to "
      "line up. Deliberately decoupled from `print_clearance`. |")
    w(f"\n`fit_coupons.stl` is a ladder of five rungs either side of each, "
      f"{P.print_clearance_step:.2f} mm apart, every rung embossed with its own value:\n")
    w("| tag | coupon | test it on | looking for |")
    w("|---|---|---|---|")
    w(f"| `A` | auger **cross-pin hole**, in a hub ring on the shaft | the real "
      f"{P.shaft_dia:.0f} mm shaft and a {P.xpin_dia:.0f} mm pin | pin pushes through "
      f"by hand, no slop. The ring's own bore steps too, but the auger's bore is a "
      f"fixed {P.auger_bore_clear:.2f} mm slide and is not read from here. |")
    w(f"| `P` | post-jig corner channel | a real {P.post_side:.1f} square PTR corner "
      "| both faces touch, no rock, comes off by hand |")
    w(f"| `B` | template drill bushing | the real {P.tie_rod_hole:.0f} mm bit | spins "
      "freely, no perceptible wobble. **This is the tightest use in the project** -- "
      "if one rung is snug here and loose elsewhere, this is the rung that decides. |")
    w("| `C` | dust-cap barb | a real 1\" NPT half coupling | firm thumb to seat, "
      "stays put upside down |")
    w(f"\n> **Mesh tolerance is part of the fit.** Every STL here is meshed at "
      f"`stl_tolerance` = {P.stl_tolerance:.2f} mm chordal, which makes a bore an\n"
      f"> inscribed polygon up to {2*P.stl_tolerance:.2f} mm small on diameter. That "
      f"cancels -- coupons and parts\n> mesh identically, so a coupon measures the "
      f"faceting along with everything else --\n> but only while the number is the "
      f"same for both. **Changing `stl_tolerance` invalidates a\n> measured "
      f"`print_clearance`.** Re-run the coupons if you touch it.\n")
    w("Each coupon is modelled in the same print orientation as the part it stands")
    w("for -- the auger bore vertical, the corner channel on its 45-degree corner, the")
    w("bushing flat. A fit measured in one orientation does not transfer to another.\n")
    w("Then: **edit two numbers, re-run the build, and batch.**\n")
    w("\n> **The rule, unchanged:** printed parts GUIDE, FEED, ALIGN, SCREEN, COVER and")
    w("> SEAL-ASSIST.  None of them contains pressure or carries structural load.  The")
    w("> fab jigs are shop tools: none of them stays in the pressure path, and the two")
    w("> PTR weld fixtures are sacrificial and must be off the work before weld-out.\n")

    tot_mass = tot_time = 0.0
    for grp, blurb in ((C, "One plate, printed and tested BEFORE anything else. "
                           "See the fit-tuning section above."),
                       (V, "On the machine, in contact with grout. Existing parts, "
                           "unchanged by the drill conversion."),
                       (J, "One-time shop tools. None of these is on the finished "
                           "machine."),
                       (O, "On the machine, not wetted.")):
        w(f"\n## {grp}\n\n{blurb}\n")
        w("| STL | Qty | Mat | Walls | Infill | Orientation | Life | Solid cm3 | Est. g ea |")
        w("|---|--:|---|--:|--:|---|---|--:|--:|")
        for r in rws:
            if r["group"] != grp:
                continue
            tot_mass += r["mass"] * r["qty"]
            w(f"| `{r['name']}.stl` | {r['qty']} | {r['mat']} | {r['walls']} | "
              f"{r['infill']}% | {r['orient']} | {r['life']} | {r['vol']:.0f} | "
              f"{r['mass']:.0f} |")
        w("")
        for r in rws:
            if r["group"] == grp:
                w(f"- **{r['name']}** -- {r['note']}")
        w("")

    w(f"\n## Totals\n")
    w(f"- **{sum(r['qty'] for r in rws)} printed parts** in "
      f"{len(rws)} distinct models.")
    w(f"- Estimated filament: **{tot_mass/1000:.1f} kg** "
      f"(at the listed infills; 'Est. g' is density x "
      f"perimeter shell volume plus infill fraction of the remainder -- a "
      f"budgeting number, not a slicer).")
    petg = sum(r["mass"] * r["qty"] for r in rws if r["mat"] == "PETG") / 1000
    asa = sum(r["mass"] * r["qty"] for r in rws if r["mat"] == "ASA") / 1000
    w(f"- PETG **{petg:.1f} kg**, ASA **{asa:.1f} kg**.  Buy {petg+1:.0f} kg and "
      f"{asa+1:.0f} kg: the auger set alone is a consumable you will reprint, and one")
    w("  of the sacrificial weld fixtures will get too close to an arc.")
    w(f"- Of that, **{sum(r['mass']*r['qty'] for r in rws if r['group']==J)/1000:.1f} kg "
      f"is one-time fab jigs** that do not stay on the machine.  That is the price of")
    w("  drilling 24 post holes and a hopper slot right the first time.")
    w("\n## Print order\n")
    w("0. **`fit_coupons` first, before anything else.** One plate, about an hour.")
    w("   Try every rung on the real shaft, the real PTR corner, the real drill bit")
    w("   and a real 1\" coupling. Put the values that fit into `print_clearance` and")
    w("   `print_interference` in `params.py`, re-run `python cad/build_all.py`, and")
    w(f"   only then start batching. A wrong clearance found on part 40 of "
      f"{sum(r['qty'] for r in rws)} is")
    w("   several kilos of filament and a weekend.")
    w("1. **Jigs first.** `jig_barrel_hopper_slot`, both `jig_barrel_*` rings and the")
    w("   three 1:1 templates, before you cut any steel. `gauge_tie_rod_spacers` before")
    w("   you cut the spacers -- that gauge is what stops you crushing the stator.")
    w("2. **PTR fixtures** before the frame day. Print 4 of each; they are sacrificial")
    w("   and one will get too close to an arc.")
    w("3. **Post jigs** before you touch the twelve posts. One print, 24 holes.")
    w("4. **Wetted parts** during the frame build: augers, gland follower, lantern ring,")
    w("   cradle, strap. Print the spare set at the same time.")
    w("5. **Operational parts** last: drill cradle, guard tiles, sand screen, funnel,")
    w("   dust caps, packing tools.")
    w("")
    return "\n".join(L)
