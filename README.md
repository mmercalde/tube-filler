# TUBE-FILLER

A small progressive-cavity grout pump built around a purchased German **D6-3**
rotor/stator set, to fill twelve **3 x 3 square PTR** posts, 6 m tall, with
sand/cement grout through a 1" hose and a 1" NPT port at each post base.

> The posts are **square PTR**. The pump barrel is **round tube**. They are two
> separate purchases that happen to share a nominal 3", and `params.py` keeps
> them in separate blocks with no cross-reference. Measure both.

Buildable with a chop saw, a drill press, a stick or MIG welder, hand tools and
a Bambu H2C. **No lathe, no mill** — every hole in this design is drilled,
hole-sawn or plasma/oxy cut, and every round part is a standard pipe or bar
size used as it comes.

---

## 0. Read this first

Four things decide whether this machine works, and only one of them is a design
choice:

| | |
|---|---|
| **The drive is now the binding constraint.** | A 900 W spade drill gives ~15 N·m continuous / 25 N·m burst at 250 rpm. At the *assumed* stator friction the duty needs 28.6 N·m and the drill is short. It works if — and only if — the stator's real running friction comes in at or below about **9 N·m**. Nobody has measured it. See §3 and `calcs` section 4. |
| **The pump is not the limit.** | The D6-3 is rated ≥ 30 bar; our duty is ~3 bar. Everything is sized for the *frame and joints* at **6 bar**, 3× duty, because that is what actually fails. |
| **The hose is the pressure limit.** | Grout is a Bingham fluid: loss is dominated by yield stress, not velocity. 8 m of 1" hose with a stiff mix costs more pressure than the whole 6 m of static head. `calcs` section 3. |
| **Nothing electrical protects this machine.** | A drill has no overload relay and no earthed frame. It does, however, stall far sooner than the 1.5 kW motor it replaced — which is the one way this conversion made the machine *safer*. §7. |

**RULES the design obeys, and that any modification must keep obeying:**

- Printed parts may **guide, feed, align and seal-assist**. They may **not**
  carry pressure or structural load. Steel contains pressure; rubber and rope
  seal it.
- Every wetted cavity opens for washout in under 5 minutes with two wrenches.
- All hardware metric where possible, from generic suppliers.
- Weld callouts suit a 3 mm wall. No full-penetration fantasies.

---

## 1. Repo layout

```
tube-filler/
  params.py            SINGLE SOURCE OF TRUTH.  All MEASURED INPUTS live here.
  bom.py               generates BOM.md from params.py
  calcs/pump_calcs.py  standalone; prints the one-page design summary + asserts
  cad/                 build123d models, all parametric on params.py
    build_all.py         <-- run this
    manifest.py          the print registry: drives BOTH the STL export and
                         out/print_manifest.md, so they cannot disagree
    coupons.py           the fit-coupon ladders (print these first)
    verify.py            geometry self-checks; nothing exports if one fails
    assembly.py          places every component at its params station; emits the
                         STEP assembly and the iso view, and runs the clash check
    jigs.py              printed fab templates (drill saddles, weld fixtures)
    ops.py               printed operational parts (cradle, screens, caps)
    _common.py  plates.py  printed.py  conrod.py  hopper.py  frame_drawing.py
  out/                 EVERYTHING GENERATED: STEP, STL, DXF, SVG, PDF
    machine_assembly.step  the whole machine, one named body per component
    assembly_iso.png       hidden-line isometric of the same
    fit_coupons.stl      20 fit coupons on one plate -- print before batching
    print_manifest.md    29 models / 53 parts: material, walls, infill,
                         orientation, consumable vs one-time jig
  BOM.md               generated
  test_plan.md         water -> cement milk -> grout, with abort criteria
  README.md            this file
```

To regenerate everything after changing a measured input:

```bash
make                  # everything
make calcs            # design summary + acceptance asserts
make assembly         # machine_assembly.step + assembly_iso.svg only
make clash            # interpenetration report, nothing exported
```

or just `make`. `cad/build_all.py` also re-runs the calcs into
`out/design_summary.txt` and rewrites `BOM.md`, so the drawings, the STLs and
the shopping list can never disagree with each other. Anywhere this README
quotes a number, `out/design_summary.txt` and `BOM.md` are the authority — they
are regenerated, this file is not.

> **CAD toolchain note.** The brief asked for CadQuery. CadQuery is installed
> on this machine but its OCP build is broken (`IVtkOCC` import error, missing
> VTK). The models are therefore written in **build123d 0.11**, which is the
> same OCP/OpenCascade kernel and the same lineage, and exports STEP, STL, DXF
> and SVG natively. Everything runs under `cadenv`:
> `~/cadenv/bin/python cad/build_all.py`.

---

## 2. MEASURED INPUTS — do this before you cut anything

Open `params.py`, Block A. Everything marked **TBD** is a placeholder: the
geometry around it is right, the number is a guess. Measure, edit, re-run.

| Input | How to get it |
|---|---|
| `stator_od`, `stator_len` | Calipers and a tape. Verify the vendor's 89.0 / 270.0. |
| `stator_inlet_bore` | The bore you can see at the stator's end face. Sets `adapter_bore` — get this right or you build a step for grout to hang on. |
| `stator_has_steel_jacket` | Is the rubber bonded inside a steel tube? If yes, set `stator_crush = 0.0`: the jacket is its own hard stop and the spacers must match the stator length exactly. |
| `stator_end_style` | Flat rubber face, or a moulded collar. Photograph both ends before you cut plate. |
| `rotor_joint`, `rotor_pin_dia`, `rotor_pin_eye_width` | Calipers on the rotor's drive head. If it is a *drill* head (a hex stub) rather than a *pin* head, see §5.3. |
| `rotor_free_len` | How far the rotor protrudes from the stator at the drive end. Sets how far into the barrel the con-rod reaches. |
| **`rotor_eccentricity`** | Two ways, both hand-tool: **(a)** lay the rotor in a V-block (two lengths of angle iron work), put a dial indicator on top, turn one full revolution: **TIR = 2e**, so `e = TIR/2`. **(b)** Caliper the stator bore at an end: it is a slot of width *d* and length *d + 4e*, so `e = (long axis − short axis)/4`. Do both; they should agree within 0.3 mm. |
| `barrel_od`, `barrel_wall` | Calipers on the owner's actual round tube for the **pump barrel**. Sets the barrel bore, the auger, the hopper slot and the barrel jigs. **Nothing about the posts depends on it.** |
| **`post_shape`, `post_side`, `post_wall`** | The twelve **posts**: square PTR, measured across the flats. **This is what sets the post volume and therefore the cement order** — see §3a. Separate stock from the barrel; do not assume they measure the same. |
| **`drill_body_dia`** | Calipers on the round gearcase section just behind the chuck collar, at its widest. Sets the printed cradle. |
| `drill_body_len`, `drill_chuck_depth`, `drill_chuck_body_len`, `drill_aux_offset` | Tape and calipers on the drill. These four place the cradle and the torque lug along the machine axis; get them wrong and the chuck is not coaxial with the stub. `verify.py` checks the result lands on the pump axis. |
| `drill_aux_handle_dia` | The auxiliary-handle collar. The steel torque lug is cut half-round to it. |
| `drill_T_cont`, `drill_T_burst` | The drill's continuous and burst torque at 250 rpm. Nameplate figures are optimistic; if you can, measure. |
| `post_port_height`, `post_vent_from_top` | Where the 1" port and the vent go on each post. The printed post jigs are built from these, so 24 holes come off two prints. |
| `post_side` (or `post_od` if round) | The post jigs parametrize on this. Stock that measures 75.4 instead of 76.2 costs one reprint, not a scrapped hole. Setting `post_shape` switches both post jigs between a corner channel and a V-saddle. |
| `bucket_rim_od` | Your 5-gal bucket. Sets the sand-screen frame. |
| `printer_x/y/z` | Your H2C build volume. `verify.py` refuses to emit a part that will not fit. |
| **`print_clearance`** | **Measured, not guessed — from `out/fit_coupons.stl`.** One number (0.25 mm diametral by default) governs every printed feature that has to fit real steel. Print the coupon ladder, find the rung that fits, put it here. See §5.0. |
| `print_interference` | Same idea, opposite direction: the oversize on the NPT dust-cap barbs, which must grip. Its own coupon rung. |

---

## 3a. Square posts, and what that does to the cement order

The posts are 3 x 3 square PTR, not round tube. A square bore of the same
nominal size holds **27% more**:

| | bore area | per post | x 12 |
|---|--:|--:|--:|
| square PTR, 76.2 across flats, 3.05 wall | 70.1 x 70.1 = 4914 mm² | **29.5 L** | **354 L** |
| round tube, 76.2 OD, 3.05 wall | ø70.1 = 3859 mm² | 23.2 L | 278 L |
| the brief's assumption | — | ~27 L | 324 L |

So the job is **354 L**, not the brief's 324 and certainly not the 278 you would
get by assuming round tube — a 76 L swing, which is about a sack and a half of
cement. `calcs` section 1 prints the correct figure from `post_shape`,
`post_side` and `post_wall`, flags the difference against the brief, and
section 10 sizes the cement, sand and water from it.

**Measure the wall before you order cement.** Under-ordering stops you
mid-post, and a post you stopped filling is a post you have to chase with a
hand pump.

Two things square PTR makes *easier*, worth knowing before you cut:

- the 1" NPT half coupling welds to a **flat face** — no saddle cut, no
  fish-mouth, and a hole saw that will not skate;
- two adjacent flat faces locate a jig completely, which is why the post jigs
  are now L-section corner channels rather than V-blocks (§5.0).

---

## 3b. The drill question, answered honestly

`calcs/pump_calcs.py` section 4 prints this in full. The short version:

| stator friction | total at duty | 900 W drill |
|--:|--:|---|
| 5 N·m | 11.0 N·m | runs, with margin |
| 6.5 N·m | 12.5 N·m | runs, no margin |
| 9 N·m | 15.0 N·m | at the continuous limit |
| 15 N·m | 21.0 N·m | breakaway only, will overheat |
| 22.6 N·m (assumed) | 28.6 N·m | **will not turn it** |

The 22.6 N·m in `params.py` is a placeholder inherited from sizing a 1.5 kW
motor, where it barely mattered. It has never been measured. Two things say the
real number may be much lower:

- the vendor sells a **drill-head rotor variant** of this very set, which means
  the manufacturer expects a drill to drive it;
- interference torque on a PC stator falls substantially once the rubber has
  bedded in and is wetted.

So the answer is not "yes" and it is not "no". It is: **measure it on water
before you mix a single bag of cement** — `test_plan.md` W-4 — and put the
measured number into `params.py`. The three levers, in order of effect:

1. **Break-in spacers.** A second set of tie-rod spacers cut to
   `stator_len − 0.5` instead of `stator_len − 2.0`. Run cement milk for 30
   minutes on those, then swap to the service set. This is the big one and it
   costs four pipe offcuts. See §6.1.
2. **Run the gland weeping**, not dry. Worth ~2.5 N·m — a sixth of the drill's
   whole continuous budget.
3. Shorten the hose, thin the mix. Worth ~1 N·m. Least effect, because
   friction, not pressure, dominates this budget.

If the measured friction still will not fit, the motor and reducer go on the
**same hex stub** with no change to the pump. See §11.

---

## 4. How the machine works

Hopper → barrel → feed auger → adapter plate → stator → discharge head → valve
→ hose → post.

- **Hopper** (44 L, wall angles 69° and 71°) feeds down through a
  200 × 50 slot into the top of the barrel. One hopper load is 1.5 posts.
- **Barrel**: 600 mm of the owner's 3" tube. The drive shaft enters the rear
  through a **packed gland** — greased graphite rope in a steel stuffing box,
  with a lantern ring fed by a grease nipple. Not a lip seal. Lip seals die in
  minutes on grout.
- **Feed auger**: printed segments, cross-pinned to the shaft, sized to deliver
  **1.33x** the stator's swallow rate. A PC pump must never starve.
  Its OD, hub, pitch and segment length are *solved* in `params.py` from the
  barrel bore, the shaft diameter and the overfeed target — change the barrel
  and the auger follows. The pitch is snapped so a whole number of pitches
  exactly spans the barrel, which is what keeps every cross-pin hole on the
  same clock angle and every segment interchangeable.
- **Adapter plate**, welded to the barrel front. Washout face #1.
- **Stator** hangs off the front, compressed lengthwise between the adapter
  plate and the discharge head by 4 x M10 tie rods. **No radial crushing.**
- **Discharge head**: rear plate + chamber ring + cap + 1" NPT half coupling.
  Washout face #2. Carries the pressure gauge boss.
- **Drive**: 1/2" spade-handle paddle drill → **rear hex stub** → 35 mm shaft on
  two UCP207 pillow blocks → shaft tongue → **con-rod with two forks at 90°** →
  rotor. No motor, no reducer, no coupling.
  The drill is *captured, not held*: its aux-handle collar bears on a **steel
  torque lug** welded to a braced steel upright, and a printed saddle clamps the
  body down. The operator's only job is the trigger.

### 4.1 The two ideas that make this design work

**Hard-stop spacers.** The four tie rods do not clamp the rubber. They clamp
four lengths of 3/4" sch40 pipe cut to `stator_len − stator_crush`. The rubber
sits inside that steel sandwich and is squeezed exactly `stator_crush` mm, no
matter how hard you pull the nuts. **Cut all four spacers together, in one
setup, to ±0.2 mm.** Over-crushing a PC stator closes its bore, spikes the
interference torque, and burns the rubber in one shift. This design makes that
failure mechanically impossible.

**Two forks at 90°.** The rotor of a 1:2 progressive-cavity pump does not just
orbit — its axis precesses on a cone. A single cross pin is a one-degree-of-
freedom hinge and cannot follow that. The con-rod therefore carries a fork at
each end with the pin axes **perpendicular to one another** (a Cardan pair),
and both pin bores are drilled 0.5 mm oversize so each joint is deliberately
sloppy. Grease it and put a bicycle inner-tube boot over it. If you build the
forks parallel, the joint binds and tears the rotor head off.

---

## 5. Build order

Nothing here needs a machine tool. Rough times are for one person.

### 5.0 Print the fit coupons first (before you print anything else)

`out/fit_coupons.stl` is one plate, about an hour: **twenty coupons, four
ladders of five rungs**, each rung embossed with its own value.

| tag | coupon | try it on | want |
|---|---|---|---|
| `A` | auger hub bore + cross-pin hole | the real 35 mm shaft and a 6 mm pin | slides on by hand, no rock |
| `P` | post-jig corner channel | a real square PTR corner | both faces touch, no rock, comes off by hand |
| `B` | template drill bushing | the real 11 mm bit | spins freely, no perceptible wobble |
| `C` | dust-cap barb | a real 1" NPT half coupling | firm thumb to seat, stays put upside down |

Put the values that fit into `print_clearance` and `print_interference` in
`params.py`, re-run `make`, and only then batch. **Every printed mating feature
in the project is derived from those two numbers**, so one measurement retunes
all 53 parts — the auger bore, the jig register faces on tube and on square
post, the drill bushings, the cradle on the stator, the saddle on the drill
body, the gland follower, the PTR weld fixtures.

`B` is the tightest use in the project: if one rung is snug there and loose
everywhere else, that rung is the one that decides.

Each coupon prints in the same orientation as the part it stands for — the
auger bore vertical, the corner channel on its 45° corner, the bushing flat. A
fit measured in one orientation does not transfer to another; first-layer
squish and seam placement are not the same on a 45° face as on a flat one.

A wrong clearance found on part 40 of 53 costs several kilos of filament and a
weekend. This plate costs an hour.

> **Not everything printed is a "fit".** `running_clearance` (0.80 mm) is the
> gap in the gland follower and lantern ring around the *rotating* shaft
> sleeve. That is a gap, not a fit, and it is deliberately kept out of the
> coupon loop — do not tune it from a coupon result.

### 5.1 Print the jigs next (before you cut any steel)
`out/print_manifest.md` lists all 28 models with material, walls, infill,
orientation and whether each is a consumable or a one-time jig. Print order is
in that file. In particular:

- `gauge_tie_rod_spacers` **before** you cut the spacers.
- `jig_barrel_hopper_slot`, `jig_barrel_rear_flange`, `jig_barrel_tie_rods` and
  the three 1:1 flange templates before you touch the barrel or the plate.
- `jig_post_port` / `jig_post_vent` before you touch the twelve posts — two
  prints, 24 holes, all at the same height without reading a tape 24 times.
  On square PTR these are **L-section corner channels**: they register on two
  adjacent faces, which locates a square section completely. A V-block cannot —
  a vee on a flat face touches two arbitrary lines and rocks. Each jig has the
  bushing centred on the face it drills and a datum leg to the post end, so the
  distance from the end to the hole is the jig, not a tape measure.
- `fixture_ptr_corner` / `fixture_ptr_tee` before frame day. **Both are
  sacrificial**: they tack, then they come off. Weld out with one fitted and
  you melt it into the joint.

No printed jig stays on the machine and none is in the pressure path.

### 5.2 Frame (one day)
Cut list and weld notes are on `out/frame_weldment.svg` (also .png/.pdf).
Tack the whole skid, check the diagonals equal within 2 mm, then weld out.
**Weld the top rails last, with the barrel clamped in its saddles** — the
barrel, not the frame, is the alignment datum for the whole machine.

### 5.3 Barrel and plates (one day)
1. Cut the barrel to 600 mm, square both ends.
2. Wrap `barrel_slot_wrap_template.dxf` around it, centre-punch, chain-drill
   and grind the 200 × 50 slot. The template's width is the **developed arc**
   (54.5 mm), not the 50 mm chord — cut to the template, not to a tape.
3. Cut and drill the plates from the DXFs. `adapter_plate.dxf` carries a
   dashed **SCRIBE** layer showing the barrel OD circle — scribe it, don't cut
   it.
4. Weld the adapter plate to the barrel front and the rear flange to the back.
   Check both faces square to the bore with a square and a straightedge before
   the weld cools. **Everything else is shimmed to these two faces.**
5. Weld the throat collar over the slot, then the hopper on top of the collar,
   then the rim bar.
6. Weld the discharge head as a stack: rear plate, chamber ring, cap, half
   coupling, gauge boss. Keep the bores concentric — a 20 mm bolt through them
   while tacking works.

### 5.4 Drive train (one day)
1. Cut the 35 mm shaft. Drill the auger cross holes at the spacing given in
   `BOM.md` (with the shipped defaults: five holes at 130/130/130/130/65) using `auger_pin_drill_jig.stl` — the jig clamps to
   the shaft and puts every hole on the same clock angle. Drill the 8 mm
   drill-stub hole at the rear.
2. Slot the shaft nose 12 mm wide × 55 deep with a cutting disc, insert the
   shaft tongue, fillet weld both sides.
3. Con-rod: cut the 32 mm bar to 91 mm, weld two 8 mm ears on each end.
   **Rotate the second pair 90° from the first.** Drill both pin holes 0.5 mm
   over the pin diameter, on the drill press, with the bar in a V-block.
4. Stuffing box: weld the 2-1/2" pipe into the rear cover, drill the 8 mm
   grease hole, weld the 1/8" half coupling over it, fit the zerk. Weld the two
   M10 gland studs.
5. Bolt the rear cover on with a 3 mm nitrile gasket. Slide on the shaft
   sleeve, then pack: **2 rings — lantern ring — 2 rings — printed follower —
   gland plate.** Stagger every ring joint 90°. Nip the nuts finger tight plus
   a flat; the gland is meant to weep slightly when running.
6. Mount the pillow blocks on the slotted sub-plate. Lock both collars; the
   **rear** one takes the rearward thrust.
7. Hex stub: cross-pin the 1-1/4" pipe sleeve to the shaft rear, plug-weld the
   1/2" hex bar. Check it runs true — spin the shaft and watch the hex.
8. Drill station: weld the braced upright, then **one 10 mm bracket** on top of
   it — a half-round torque lug at its front edge, cut to the *measured*
   aux-handle collar, and a flat behind it for the printed saddle. One plate,
   two jobs; the lug is the only torque path. Bolt the printed saddle down
   through its slots, sit the drill in, chuck it on the stub, and shim until
   the drill runs with no side load on the stub. **Weld both drill braces** —
   unbraced, the upright sags 2.4 mm under the 1160 N torque reaction and the
   drill cocks off the stub axis.

   The saddle is only as long as the drill body behind the collar
   (`drill_body_len − drill_aux_offset`), which on a typical spade drill is
   about 46 mm. Sizing it at 130 put it straight through the torque lug — the
   assembly clash check caught that, and `cradle_plate_l` now follows the
   measured drill.

**If your rotor has a *drill* head (hex) instead of a pin head:** you still
need the 2-DOF articulation. Do not chuck a hex socket straight to the shaft.
Build the same con-rod, and make the front end a hex socket by welding a
standard nut of the measured across-flats size inside a short tube — then the
*rear* fork alone provides only 1 DOF, so add a second cross pin at 90° in the
socket tube. Set `rotor_joint = "drill_hex"` and `rotor_hex_af` in `params.py`.

### 5.5 Printing
Everything: material, walls, infill, orientation, quantity and print order is
in **`out/print_manifest.md`** — 29 models, 53 parts, roughly 7 kg of filament
across coupons, jigs, wetted parts and operational parts.

Three rules hold across all of them:

- **Coupons before batch.** §5.0. Two numbers in `params.py` drive every
  printed fit; measure them once.

- **No supports on anything.** Every model is emitted in its print orientation
  and every overhang is at 45° or steeper. The auger flight self-supports (97%
  layer-to-layer overlap); the clamp jigs are 90° V-blocks; the funnel leans
  14° from vertical; horizontal bores are teardropped.
- **Printed parts guide, feed, align, screen, cover and seal-assist. They never
  contain pressure and never carry structural load.** The drill cradle is the
  case to be explicit about: it clamps, and the torque goes drill collar →
  steel lug → steel upright → braces → skid.

Print the spare auger set and the spare gland parts *now*. They are consumables
and you will want them on a Saturday.

---

## 6. Operating procedure

### 6.1 Before the first powered start of a NEW stator — do not skip this
A dry PC stator has enormous breakaway friction and will burn in seconds.

1. Wet the stator bore with soapy water or cement milk. Pour some in and swill it.
2. Put a wrench on the coupling (or the drill stub) and **turn the pump through
   two full revolutions by hand.** If you cannot turn it by hand, the stator is
   over-crushed or the rotor is wrong — stop and check the spacer length.
3. Only then pull the trigger, and start in the drill's LOW range at part
   throttle. If the drill bogs immediately, stop: you are on the wrong spacers
   or the stator is over-crushed.

Repeat step 1 and 2 after every wash-out, every time.

### 6.2 Running
1. Hose connected, whip checks on, discharge valve **open**, bypass valve closed.
2. Prime with 5 L of cement milk (cement + water, no sand) — it lubricates the
   hose wall and stops the first grout from bridging.
3. Start the pump. Load the hopper. **Never let the hopper level drop below
   the top of the barrel slot** — a starved PC pump cavitates, knocks and eats
   its stator.
4. Watch the gauge. Normal running is 2–4 bar. **6 bar is the red line.**
5. Pump until grout runs from the vent at the top of the post.

   > ### VALVE BEFORE TRIGGER
   > **Close the discharge ball valve first. Then release the trigger.**
   > In that order, every single time.
   >
   > A drill freewheels the instant you let go — there is no gearbox, no brake
   > and nothing holding the rotor. The 1.24 bar column of grout standing in
   > the post will drive the rotor backwards and drain itself into the hopper,
   > and you will not see it happen: the vent simply stops weeping and the top
   > of the post is hollow. On the motor version a 7.5:1 worm at least slowed
   > this down. On a drill there is nothing at all between the column and the
   > hopper except that ball valve.
6. Fill time is ~2.4 min per post; twelve posts is ~29 min of pumping.

### 6.3 If it stalls or the pressure climbs
1. **Open the bypass valve.** That is the relief valve. Do it first.
2. Release the trigger.
3. Flick the drill into reverse and give it a second or two — a paddle drill
   reverses on a switch, which is one thing this drive does better than the
   motor version. A few seconds in reverse clears most bridges.
4. Never "help" it by closing the discharge and squeezing harder. A drill will
   happily push the pump to 15 bar before it stalls, and the joints are built
   for 6.

---

## 7. Safety

- **The drill is the machine's best overpressure protection, and it is still
  not enough.** At low measured friction the drill stalls somewhere around
  15-20 bar; the 1.5 kW motor it replaced did not stall until ~140 bar. That is
  a genuine improvement. It is not a relief valve. The gauge and the bypass
  valve are still the safety system.
- **A drill has no overload relay and no earthed metal frame of its own.** The
  30 mA RCD is the only electrical protection on this build. Do not omit it,
  and test it with its own button before every session.
- **Never wedge or zip-tie the trigger.** The trigger is the emergency stop and
  the only thing standing between a blockage and a burst hose.
- The drill is captured in the cradle for exactly one reason: so nobody is
  holding 25 N·m of reaction torque by hand when the pump snatches.
  - 0–16 bar glycerin gauge, **flush-diaphragm** isolator, mounted in the
    operator's eyeline. Paint a red band at 6 bar.
  - 1" manual bypass ball valve, discharge head back to the hopper, short line.
  - Hose rated ≥ 40 bar working. **Crimped ends only. Never a worm-drive hose
    clamp on grout.** Whip checks at every coupling.
  - 30 mA RCD on the supply. There is no overload relay on this build --
    a drill has none, and its own thermal cutout protects the drill, not
    the pump.
- 20 A circuit, 2.5 mm² (12 AWG), **30 mA RCD**. The machine is wet and steel.
- The grate is bolted on and stays on while the machine runs. There is an auger
  under it.
- Never break a hose coupling before the gauge reads zero.
- Wet cement burns skin. Gloves, eye protection, long sleeves.
- Grate note: **the grate is a tramp guard, not a sieve.** A 3 mm grate over a
  hopper of wet grout blinds instantly. Size the sand to ≤ 3 mm **at the sand
  pile, through a real screen, before it goes in the mixer.** The grate's job is
  to keep stones, trowels and hands out of a running auger.

---

## 8. Flush procedure

**Within 20 minutes of the last post, and before any break longer than 20
minutes.** Two 17 mm wrenches, a bucket, a garden hose, a bottle brush, a
grease gun.

1. Stop the pump. **Open the bypass valve** and confirm the gauge reads zero.
2. Close the discharge ball valve. Break the hose at the machine, drop the far
   end in the wheelbarrow, and push a wet sponge ball through the hose with
   water. Recover the ~4 L of grout in it.
3. Scrape the hopper out into the barrow. Do **not** wash hopper grout down
   into the barrel — you are trying to get grout out, not in.
4. Refit the hose. Fill the hopper with 20 L of clean water, open the discharge
   valve, and run at speed into the barrow until it runs clear (~2 min).
5. Open the bypass halfway and run another 10 L to clear the bypass line and
   its return to the hopper. Close the bypass.
6. Stop. Loosen the four tie-rod nuts and slide the discharge head, stator and
   spacers forward off the adapter plate as one unit.
7. Hose out, and brush: the stator bore, the discharge chamber, the adapter
   plate bore, the barrel (through the adapter bore *and* through the open
   hopper throat).
8. Three strokes of the grease gun on the gland zerk, until clean grease shows
   at the follower. This purges the lantern ring.
9. Unscrew the gauge isolator, wipe the diaphragm, refit.
10. Reassemble wet: gaskets in, stator on, nuts to **20 N·m**. Leave a litre of
    water standing in the barrel until next use.

**End of job, or before the machine stands more than 48 h — additionally:**

11. Unbolt the four rear-cover bolts and the pillow-block sub-plate, draw the
    whole drive train rearward out of the barrel. Wash the auger segments and
    the shaft. Inspect the sleeve. Repack the gland if the follower's shoulder
    has reached the box rim.

### 8.1 Every wetted cavity, and the step that clears it

| Cavity | Cleared by |
|---|---|
| Hose, discharge valve, half coupling | 2, 4 |
| Discharge chamber | 4, 7 |
| Stator bore | 4, 7 |
| Adapter plate bore | 4, 7 |
| Barrel bore and auger flights | 4, 7 |
| Annulus in front of the gland | swept by the scavenger segment; 4, 7 |
| Hopper and throat collar | 3, 4 |
| Bypass line and its return | 5 |
| Gauge port and diaphragm | 9 |
| Packing stack and lantern ring | 8, 11 |
| Auger hub bore / shaft clearance | 11 |

If a step is skipped, the cavities in its row are the ones holding grout in the
morning.

---

## 9. Maintenance and wear

| Part | Life | Note |
|---|---|---|
| Stator | the real consumable | Never run dry, never over-crush, never starve. |
| Auger segments | a season, or one bad flush | Declared consumable. Keep a printed spare set. |
| Shaft sleeve | a season | 1-1/4" sch40 pipe, $3. It wears so the shaft doesn't. |
| Gland packing | ~40 h pumping | Repack when the follower shoulder touches the box rim. |
| Follower / lantern ring | with the packing | Reprint. |
| Coupling spider | years | Keep one spare. |
| Gaskets | every strip-down | 3 mm nitrile, cut with a hole saw and scissors. |

---

## 10. What to measure and feed back into `params.py`

The design's weakest assumption is `T_stator_friction = 22.6 N·m`. On the motor
it barely mattered. **On the drill it decides whether the machine runs at all**
(§3b). Measure it on the water test (`test_plan.md` W-4), put the real number
into `params.py`, and re-run `calcs/pump_calcs.py`. The verdict line at the
bottom will tell you PASS, MARGINAL or SHORTFALL — and the table in section 4
tells you what to do about each.

Also worth feeding back: `grout_tau0` (from the pressure the gauge actually
shows on the first post), and `auger_fill_eta` (from whether the pump surges).


---

## 10a. The assembly model, and the five things it caught

`cad/assembly.py` places every component at its `params.py` station — reusing
the same builders that produce the STLs and DXFs, never remodelling — and emits
`out/machine_assembly.step` with one named body per component plus
`out/assembly_iso.png`. The drill is in there too, as an envelope cylinder off
the measured drill dimensions, so the clearances you read are the real ones.

`verify.py` then intersects **every pair of bodies** and fails the build on any
shared volume that is not on `assembly.INTENDED_FITS` — a short, explicit list
(shaft-in-sleeve, auger-on-shaft, stator-on-cradle, fork-on-tongue, chuck-on-
stub, and the welded stacks). Run it alone with `make clash`.

Placing the parts is what proved the layout, and it was not clean:

| what the clash check found | why it mattered |
|---|---|
| The shaft nose sat 200 mm inside the space the con-rod needs. | `x_auger_front` was a hard-coded −30. The rotor position is set by the stator and nothing else can move, so the chain now runs **forwards** from the rotor: tip → pin → con-rod → tongue → shaft nose → auger. The auger is 371 mm, not 520, and the shaft got 200 mm shorter — which incidentally cut the unsupported overhang from 770 mm to 558 and the deflection from 1.90 mm to 0.68. |
| The stator cradle sat straight through two tie-rod spacers, and the strap through the other two. | Only ~3.5 mm of web fits between the stator and a spacer. Both parts now have closed circular channels at the spacer stations; the spacers slide out axially with the stator at washout, so a closed channel costs nothing. |
| The hex stub's 42 mm sleeve was inside the rear pillow block housing. | The shaft rear moved to −1000 and the blocks to −790 / −900. |
| The printed drill saddle ran straight through the steel torque lug. | There is only `drill_body_len − drill_aux_offset` of drill body behind the collar. The saddle is now sized from that, and lug and saddle share one welded bracket. |
| The stator strap duplicated the cradle's lower half. | It was modelled as a full arch from −r to +r. It now caps only the upper half, and prints valley-up so it needs no supports; the assembly flips it. |

Two smaller ones: the hex stub's weld plug sits *beyond* the shaft end, so the
chuck face is a plug thickness further back than `hex_free_len` alone implies;
and the top rails were set from the barrel OD when the **stator** is the fat
part — they were 6 mm inside it. Both are now derived.

None of these would have shown up in a part-by-part review. All five showed up
the first time the parts were put in the same coordinate system.

---

## 11. Upgrade path -- motor and reducer, same hex stub

Nothing about the pump changes. The drill drive was designed so this is a bolt-on:

| | |
|---|---|
| Motor | 1.5 kW 1-phase 220 V 4-pole, frame 90L, B14 FT130, 24 mm shaft |
| Reducer | NMRV-050, 7.5:1, 90B14 input, 25 mm output |
| Coupling | L-110 / ROTEX-38, one half bored to 12.7 mm A/F to take **the same hex stub**, the other 25 mm |
| Gives | 64 N·m at 193 rpm — a 2.1× margin even at the pessimistic 22.6 N·m friction |
| Costs | roughly $500, and about 1.2 m more PTR for the motor outrigger |

Prices and specs are in `BOM.md` §3b, deliberately kept **out** of the BOM
total. The frame drawing has no motor mount; adding one is an outrigger welded
to the left skid rail, because the NMRV's worm input sits at 90° to its output
and the motor therefore lies crosswise.

Two things to know before you spend the money:

1. **Fit the upgrade for torque, not for speed.** It runs the pump *slower*
   (193 rpm vs 250), so each post takes 2.4 min instead of 1.9.
2. **It takes the overpressure protection away again.** A 1.5 kW motor on a
   7.5:1 worm does not stall until ~140 bar — twenty times what these joints
   are built for — and no overload relay will trip first. If you fit it, the
   gauge, the red band at 6 bar and the bypass valve stop being good practice
   and start being the only thing standing between you and a burst hose.
