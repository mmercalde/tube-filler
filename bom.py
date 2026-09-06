#!/usr/bin/env python3
"""Generates BOM.md from params.py.  Run by cad/build_all.py.

Prices are 2026 order-of-magnitude estimates in USD for one machine, from
generic import/hardware-store sources.  They are for budgeting, not quoting.
The owner shops both sides of the US/MX border, so each line carries a US
(McMaster / Grainger / big-box) and an MX (ferreteria / tornillo y aceros)
equivalent where the two differ.
"""
import os, sys
from math import pi
import params as P

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "calcs"))
import pump_calcs as C          # quantities come from the calcs, never retyped

ROOT = os.path.dirname(os.path.abspath(__file__))

# name, qty, spec, US source, MX equivalent, unit price USD
PURCHASED = [
 ("D6-3 rotor + stator set", 1, f"stator {P.stator_od:.0f} OD x {P.stator_len:.0f}, "
  f"{P.stator_shore_a:.0f} ShA, {P.stator_max_grain:.0f} mm max grain",
  "German pump supplier (owner-sourced)", "same", 320),
 ("Paddle drill (PRIMARY DRIVE)", 1, f"{P.drill_power_w:.0f} W spade-handle, "
  f"1/2\" chuck, low range 0-{P.drill_rpm_low_max:.0f} rpm, variable trigger",
  "owner already has", "owner already has", 0),
 ("Pillow blocks", 2, f"{P.pillow_block}, {P.shaft_dia:.0f} mm bore, cast, set-screw",
  "any import UCP207", "chumacera de piso UCP207", 17),
 ("Hardware cloth", 1, "1/8\" (3.2 mm) galvanised, 350 x 350 -- the sand sieve",
  "hardware store", "malla mosquitero/gallinero 1/8\"", 12),
 ("Printed-part hardware", 1, "M8 x 40 x 8 + nuts/washers (drill cradle), M6 x 60 x 8 "
  "(jigs), M4 x 20 x 8 (sand screen), 8 x 300 mm nylon straps or 4 x 100 mm hose clamps",
  "hardware store", "ferreteria", 26),
 ("Ball valve, discharge", 1, "1\" NPT full port, lever, steel or brass",
  "owner already has", "owner already has", 0),
 ("Ball valve, bypass", 1, "1\" NPT full port -- the relief path, see README",
  "hardware store", "ferreteria", 19),
 ("Pressure gauge", 1, "0-16 bar (0-230 psi) glycerin-filled, 1/4\" NPT bottom",
  "Winters PFQ / Grainger", "manometro glicerina 0-16 bar", 26),
 ("Gauge isolator", 1, "1/4\" NPT diaphragm gauge saver, grease-filled",
  "McMaster 4045K", "sello diafragma 1/4\"", 24),
 ("Grout hose", 1, f"1\" ID x {P.hose_len/1000:.0f} m concrete placement hose, "
  ">= 40 bar WP, crimped ends", "Gates / JGB", "manguera para concreto 1\"", 130),
 ("Whip checks", 2, "hose-to-hose safety cable, 1\" hose",
  "Dixon WS2", "cable de seguridad para manguera", 9),
 ("Half coupling, discharge", 1, "1\" NPT 3000# forged steel", "hardware store", "media copla 1\" cedula 80", 8),
 ("Half couplings, POST PORTS", P.n_posts, "1\" NPT 3000# forged steel, one per post. "
  "Welds to a FLAT face of the square PTR -- no saddle cut, no fish-mouth.",
  "hardware store", "media copla 1\" cedula 80", 8),
 ("Half coupling, gauge", 1, "1/4\" NPT 3000# forged steel", "hardware store", "media copla 1/4\"", 4),
 ("Half coupling, grease", 1, "1/8\" NPT 3000# forged steel", "hardware store", "media copla 1/8\"", 4),
 ("Grease nipple", 1, "1/8\" NPT straight zerk", "hardware store", "grasera 1/8\"", 3),
 ("Gland packing", 1, f"{P.packing_sq:.0f} mm square graphited PTFE/flax, 1 m coil",
  "McMaster 9911K / Chesterton 1730", "empaquetadura de grafito 10 mm", 26),
 ("Threaded rod", 1, f"M{P.tie_rod_m:.0f} x 1 m, class 8.8 (or 3/8-16 grade 5)",
  "hardware store", "varilla roscada M10 grado 8.8", 9),
 ("Nuts + washers", 1, f"M{P.tie_rod_m:.0f}: 16 nyloc + 16 flat, 8.8",
  "hardware store", "ferreteria", 11),
 ("Dowel pins, joint", 2, f"{P.rotor_pin_dia:.0f} mm x 60 hardened dowel, ground",
  "McMaster 98381A", "perno endurecido 12 mm", 7),
 ("Roll pins, auger", 6, f"{P.xpin_dia:.0f} x 45 spring/roll pin",
  "hardware store", "pasador elastico 6 x 45", 1),
 ("Fastener kit", 1, "M12 x 8 (pillow blocks), M10 x 12 (flange/gland), "
  "M8 x 8, M6 x 6, all with nuts + washers", "hardware store", "ferreteria", 38),
 ("Nitrile sheet", 1, "3 mm x 300 x 300, 60-70 Shore A (stator + flange gaskets)",
  "McMaster 8635K", "hule nitrilo 3 mm", 16),
 ("Electrical kit", 1, "IP55 enclosure, on/off with thermal overload set 1.15 x FLA, "
  "20 A breaker, 30 mA RCD, 2.5 mm2 cable, plug",
  "hardware store", "arrancador con relevador termico", 98),
 ("Filament", 1, "see out/print_manifest.md for the exact split and totals "
  "(~8 kg across 56 parts). ASA for anything that lives outdoors or against a "
  "warm drill; PETG for the rest.", "any", "any", 155),
 ("Paint", 1, "etch primer + enamel", "hardware store", "ferreteria", 26),
 ("Anti-seize + grease", 1, "copper anti-seize for the tie rods; EP2 for the gland",
  "hardware store", "ferreteria", 18),
]


def _pipe(nom, od, idd, L, n=1):
    return f"{nom} ({od:.1f} OD x {idd:.1f} ID) x {L:.0f} mm" + (f" x{n}" if n > 1 else "")


def fabricated():
    F = []
    A = F.append
    A(("Barrel (ROUND tube -- not post stock)", 1,
       f"owner's round tube {P.barrel_od:.1f} OD x {P.barrel_wall:.2f} wall",
       f"cut {P.barrel_len:.0f} mm. Slot {P.barrel_slot_l:.0f} x {P.barrel_slot_w:.0f} in the "
       f"top (developed width 54.5 -- use barrel_slot_wrap_template.dxf)"))
    A(("Adapter plate", 1, f"{P.plate_t:.0f} mm plate",
       f"{P.plate_size:.0f} x {P.plate_size:.0f}; bore {P.adapter_bore:.0f}; "
       f"4 x {P.tie_rod_hole:.0f} on {P.tie_bc:.1f} BC (diagonals). adapter_plate.dxf"))
    A(("Discharge rear plate", 1, f"{P.plate_t:.0f} mm plate",
       f"{P.plate_size:.0f} x {P.plate_size:.0f}; bore {P.disch_rear_bore:.0f}; "
       f"same 4 tie holes. discharge_rear_plate.dxf"))
    A(("Discharge chamber ring", 1, "2\" sch40 pipe",
       _pipe("2\" sch40", P.disch_ring_od, P.disch_ring_id, P.disch_ring_len)))
    A(("Discharge cap", 1, f"{P.disch_cap_t:.0f} mm plate",
       f"{P.disch_cap_size:.0f} x {P.disch_cap_size:.0f}; bore {P.disch_cap_bore:.0f}. "
       f"discharge_cap.dxf"))
    A(("Tie-rod spacers", P.n_tie_rods, "3/4\" sch40 pipe",
       _pipe("3/4\" sch40", P.spacer_od, P.spacer_id, P.spacer_len, P.n_tie_rods)
       + "  <-- CUT ALL FOUR TOGETHER, +/-0.2 mm. These are the hard stop."))
    A(("Tie rods", P.n_tie_rods, f"M{P.tie_rod_m:.0f} rod 8.8",
       f"cut {P.spacer_len + 2*P.plate_t + 40:.0f} mm each"))
    A(("Barrel rear flange", 1, f"{P.barrel_flange_t:.0f} mm plate",
       f"{P.barrel_flange:.0f} sq; bore {P.barrel_id:.1f}; 4 x {P.barrel_bolt_m+1:.0f} on "
       f"{P.barrel_bolt_bc:.0f} BC. barrel_rear_flange.dxf"))
    A(("Barrel rear cover", 1, f"{P.barrel_flange_t:.0f} mm plate",
       f"{P.barrel_flange:.0f} sq; bore {P.gland_box_od:.0f} (2-7/8\" hole saw); same bolt "
       f"pattern + 2 x M10 gland studs at {P.gland_stud_span:.0f} centres. barrel_rear_cover.dxf"))
    A(("Stuffing box", 1, "2-1/2\" sch40 pipe",
       _pipe("2-1/2\" sch40", P.gland_box_od, P.gland_box_id, P.gland_box_len)
       + f"; 8 mm grease hole at {P.packing_sq*2 + P.lantern_len/2:.0f} mm from the inner end"))
    A(("Shaft sleeve (sacrificial)", 2, "1-1/4\" sch40 pipe",
       _pipe("1-1/4\" sch40", P.sleeve_od, P.sleeve_id, P.sleeve_len, 2)
       + "  <-- make two; it is a consumable"))
    A(("Gland plate", 1, f"{P.gland_plate_t:.0f} mm plate",
       f"{P.gland_stud_span+40:.0f} x 60; bore {P.sleeve_od+2:.0f}; "
       f"2 x {P.gland_stud_m+1:.0f} at {P.gland_stud_span:.0f}. gland_plate.dxf"))
    A(("Gland studs", 2, f"M{P.gland_stud_m:.0f} rod", "cut 90 mm, weld into the rear cover"))
    A(("Drive shaft", 1, f"{P.shaft_dia:.0f} mm cold-rolled bar (1045 preferred)",
       f"cut {abs(P.x_shaft_rear - P.x_auger_front):.0f} mm; {P.n_auger_full} x {P.xpin_dia:.0f} cross holes at "
       f"{P.auger_seg_len:.0f} pitch (use the printed jig); 1 x 8 mm cross hole at the rear "
       f"for the drill stub; {P.shaft_key:.0f} x 8 keyway at the coupling (file it, or buy a "
       f"keyed shaft)"))
    A(("Shaft tongue", 1, f"{P.tongue_t:.0f} mm flat bar",
       f"{P.conrod_bar:.0f} wide x 70 long; {P.conrod_pin_dia+0.5:.1f} pin hole. Slot the shaft "
       f"nose {P.tongue_t:.0f} mm wide x 55 deep, insert, fillet both sides. shaft_tongue.dxf"))
    A(("Con-rod bar", 1, f"{P.conrod_bar:.0f} mm round bar", "cut 91 mm"))
    A(("Con-rod ears", 4, f"{P.conrod_fork_t:.0f} mm plate",
       f"{P.conrod_bar:.0f} x 45; {P.conrod_pin_dia+0.5:.1f} pin hole 14 from the end. "
       f"THE TWO FORKS ARE AT 90 DEG TO EACH OTHER -- see cad/conrod.py"))
    A(("Hex stub -- PRIMARY INPUT", 1, "1-1/4\" sch40 pipe + 1/2\" A/F hex bar",
       f"60 mm pipe + {P.hex_free_len:.0f} mm hex free length, plug-welded; "
       f"{P.hex_pin_dia:.0f} mm cross hole. The drill chucks straight onto this."))
    A(("Drill torque lug", 1, "10 mm plate",
       f"90 x 70, half-round R{P.drill_aux_handle_dia/2:.1f} to the MEASURED aux-handle "
       f"collar; welded to the upright. THE ONLY TORQUE PATH."))
    A(("Drill cradle plate", 1, f"{P.cradle_plate_t:.0f} mm plate",
       f"{P.cradle_plate_l:.0f} x 180; 4 x M8 tapped or clearance for the printed saddle"))
    A(("Break-in spacer set", P.n_tie_rods, "3/4\" sch40 pipe",
       f"cut {P.stator_len - 0.5:.1f} mm x{P.n_tie_rods} -- 0.5 mm crush instead of "
       f"{P.stator_crush:.1f}. Gauge them on the printed tie-rod gauge. This set is the "
       f"first thing to try if the drill will not carry the stator friction."))
    A(("Hopper walls", 2, "3 mm sheet",
       f"trapezoid {P.hop_top_l:.0f}/{P.hop_bot_l:.0f} x {P.hop_slant_long:.0f} slant, "
       f"+{P.hop_lap:.0f} lap. hopper_wall_long_x2.dxf"))
    A(("Hopper walls", 2, "3 mm sheet",
       f"trapezoid {P.hop_top_w:.0f}/{P.hop_bot_w:.0f} x {P.hop_slant_short:.0f} slant. "
       f"hopper_wall_short_x2.dxf"))
    A(("Hopper rim", 1, "1\" x 1/8\" flat bar", f"~{2*(P.hop_top_l+P.hop_top_w)/1000:.1f} m, "
       f"welded round the top edge"))
    A(("Throat collar sides", 2, "3 mm sheet",
       f"{P.hop_bot_l:.0f} x 60. hopper_collar_side_x2.dxf"))
    A(("Throat collar ends", 2, "3 mm sheet",
       f"{P.hop_bot_w:.0f} x 60 with an R{P.barrel_od/2:.1f} saddle cut. hopper_collar_end_x2.dxf"))
    A(("Grate", 1, "3 mm sheet + 6 mm bar",
       f"frame {P.hop_top_l+60:.0f} x {P.hop_top_w+60:.0f}, bars at {P.grate_pitch:.0f} pitch. "
       f"TRAMP GUARD, NOT A SIEVE -- see README. hopper_grate.dxf"))
    A(("Barrel saddles", 2, "6 mm plate", f"120 x 80 with an R{P.barrel_od/2:.1f} notch"))
    A(("Pillow-block sub-plate", 1, "10 mm plate",
       "260 x 160; 4 x 14 x 40 slots along x so the drive train withdraws"))
    A(("Lifting eyes", 4, "12 mm plate", "80 x 60 with a 30 mm hole"))
    A(("Frame", 1, f"PTR {P.ptr_size:.0f} x {P.ptr_size:.0f} x {P.ptr_wall:.2f}",
       "see out/frame_weldment.svg for the full cut list (~19 m)"))
    return F


PRINTED = [
 (f"auger_segment_p{P.auger_pitch:.0f}", P.n_auger_full,
  f"pitch {P.auger_pitch:.0f}, OD {P.auger_od:.0f}, {P.auger_seg_len:.0f} long"),
 (f"auger_scavenger_p{P.auger_pitch:.0f}_L{P.auger_tail_len:.0f}", 1,
  "sweeps the annulus in front of the gland -- without it that 65 mm is a cavity "
  "the flush cannot reach"),
 (f"auger_segment_p{P.auger_pitch_alt:.0f} (spare set)", P.n_auger_full,
  "only if the primary auger starves -- see calcs section 5"),
 ("gland_follower", 3, "consumable; print spares now, not later"),
 ("lantern_ring", 3, "consumable"),
 ("stator_cradle", 1, "non-structural"),
 ("stator_strap", 1, "non-structural; finger tight"),
 ("auger_pin_drill_jig", 1, "shop tool, prints once"),
 ("joint_boot_clamp", 2, "retains a bicycle inner-tube boot over the pin joint"),
]


def render():
    L = []
    w = L.append
    w("# BOM -- TUBE-FILLER\n")
    w("<!-- GENERATED by bom.py from params.py.  Do not edit by hand: "
      "run `python cad/build_all.py`. -->\n")
    w("Prices are 2026 order-of-magnitude estimates in USD for **one machine**, for "
      "budgeting only.\nQuantities and every dimension below come straight from "
      "`params.py`, so they cannot drift\nfrom the CAD.\n")

    w("\n## 1. Purchased\n")
    w("| Item | Qty | Spec | US source | MX equivalent | Unit | Ext |")
    w("|---|--:|---|---|---|--:|--:|")
    tot = 0
    for n, q, spec, us, mx, pr in PURCHASED:
        tot += q * pr
        w(f"| {n} | {q} | {spec} | {us} | {mx} | ${pr} | ${q*pr} |")
    w(f"| | | | | | **TOTAL** | **${tot}** |")
    w(f"\nWithout the rotor/stator set (owner already bought it): "
      f"**${tot - 320}**.\n")

    w(f"\n> **Two different 3\" stocks.**  The pump barrel is ROUND tube "
      f"({P.barrel_od:.1f} OD x {P.barrel_wall:.2f}).  The twelve posts are "
      f"SQUARE PTR\n> ({P.post_side:.1f} across flats x {P.post_wall:.2f}).  "
      f"Measure both; they are separate purchases and `params.py` keeps them in\n"
      f"> separate blocks with no cross-reference.  The square bore holds "
      f"{C.post_vol_L:.1f} L per post,\n> 27% more than round tube of the same "
      f"nominal size, and the cement order follows from it.\n")
    w("\n## 2. Fabricated -- steel\n")
    w("Every DXF named here is in `out/`.  Cut lengths are square cuts unless stated.\n")
    w("| Item | Qty | Stock | Cut / operations |")
    w("|---|--:|---|---|")
    for n, q, stock, cut in fabricated():
        w(f"| {n} | {q} | {stock} | {cut} |")

    w("\n### Plate nesting\n")
    w(f"- 10 mm plate: adapter plate + discharge rear plate + discharge cap + sub-plate "
      f"fit inside one **350 x 350** offcut.\n"
      f"- 12 mm plate: gland plate + shaft tongue + lifting eyes, one **250 x 200** offcut.\n"
      f"- 3 mm sheet: the hopper develops into four flat trapezoids; nest them "
      f"head-to-tail inside **1200 x 900**.\n")

    w("\n## 3. Printed\n")
    w("The full print list -- 28 models, 56 parts, material, walls, infill, print")
    w("orientation and consumable-vs-one-time-jig -- is generated into")
    w("**`out/print_manifest.md`**.  It is not duplicated here, because a BOM and a")
    w("manifest that disagree are worse than either alone.\n")
    w("Summary: about 8 kg of filament across 56 parts, in three groups --\n")
    w("- **WETTED** augers, gland follower, lantern ring, stator cradle and strap;")
    w("- **FAB JIGS** barrel and post drill saddles, 1:1 flange templates, PTR tack")
    w("  fixtures (sacrificial), tie-rod spacer gauge -- none of these is on the")
    w("  finished machine;")
    w("- **OPERATIONAL** drill cradle, hopper guard tiles, sand screen, funnel, twelve")
    w("  port dust caps, packing tools.\n")
    w("**Rule:** printed parts guide, feed, align, screen, cover and assist the seal.")
    w("They never contain pressure and never carry structural load.  The jigs never")
    w("stay in the pressure path, and the two PTR weld fixtures are sacrificial.\n")

    w("\n## 3b. NOT PURCHASED -- motor upgrade path\n")
    w("Deleted from the BOM above and **excluded from the total**.  Kept here because")
    w("the machine is built to accept it without modification: the motor + reducer")
    w("drive the SAME hex stub through a coupling half bored to 12.7 A/F, and nothing")
    w("on the pump changes.  Fit it if the measured stator friction turns out to be")
    w("more than the drill can carry -- `calcs/pump_calcs.py` section 4 prints the")
    w("break-even number.\n")
    w("| Item | Spec | Est. |\n|---|---|--:|")
    for n, s, pr in [
        ("1-phase motor", f"{P.up_motor_kw} kW 220 V 4-pole, frame {P.up_motor_frame}, "
         f"{P.up_motor_flange}, {P.up_motor_shaft_dia:.0f} mm shaft", 210),
        ("Worm reducer", f"{P.up_gearbox_model} {P.up_gearbox_ratio:.1f}:1, 90B14 input, "
         f"{P.up_gearbox_out_shaft:.0f} mm output", 135),
        ("Jaw coupling", "L-110 / ROTEX-38, one half bored 12.7 A/F hex, one 25 mm", 48),
        ("Motor outrigger + shelf", "~1.2 m more PTR, plus the brace", 12),
        ("Electrical kit", "IP55 starter with overload at 1.15 x FLA, 20 A, 30 mA RCD", 98)]:
        w(f"| {n} | {s} | ${pr} |")
    w("| | **UPGRADE TOTAL (not in the BOM)** | **$503** |")
    w("\nNote the frame drawing has no motor mount.  Adding one is a 1.2 m outrigger")
    w("welded to the left skid rail -- the worm input sits at 90 degrees to its output,")
    w("so the motor lies crosswise.\n")

    w("\n## 4. Consumables to stock before the pour\n")
    w("| Item | Qty |\n|---|--:|")
    for n, q in [("Auger segments (a set is a wear item)", "1 spare set"),
                 ("Shaft sleeve, 1-1/4\" sch40 x 130", "1 spare"),
                 ("Gland packing", "1 m spare"),
                 ("Gland follower + lantern ring", "2 spare each"),
                 ("3 mm nitrile gaskets", "4 spare"),
                 ("Printed auger set", "1 spare set (see print manifest)"),
                 (f"Cement -- {P.n_posts} x {P.post_shape} posts, "
                  f"{C.post_vol_L:.1f} L each",
                  f"{C.cement_kg:.0f} kg = {C.sacks:.1f} sacks of 50 kg"),
                 ("Sand, sieved <= 3 mm through the printed screen",
                  f"~{C.sand_kg:.0f} kg"),
                 ("Water", f"~{C.water_L:.0f} L, plus 200 L for flushing")]:
        w(f"| {n} | {q} |")
    w("")
    return "\n".join(L)


if __name__ == "__main__":
    open(os.path.join(ROOT, "BOM.md"), "w").write(render())
    print("BOM.md written")
