# TUBE-FILLER — commissioning and test plan

Three stages, in order, no skipping: **water → cement milk → grout**. Each
stage has pass criteria you must meet before the next, and abort criteria that
stop the test immediately.

Nothing in stage 1 or 2 can hurt the stator. Stage 3 can. That is the whole
reason for the order.

**Kit for every stage:** clamp ammeter (true-RMS, 0–20 A), tachometer or a
phone slow-mo of a paint mark on the coupling, the 0–16 bar gauge already
fitted, a stopwatch, a 20 L graduated bucket, a wheelbarrow, two 17 mm
wrenches, a grease gun, PPE.

**Before any stage:** wet the stator, turn the pump two full revolutions by
hand at the coupling. If it will not turn by hand, stop — see abort A-1.

---

## Stage 0 — Dry checks (no fluid, no power)

| # | Check | Pass |
|---|---|---|
| D-1 | Turn the pump by hand at the hex stub, two revolutions | Turns with a firm but steady pull. No tight spot. |
| D-1b | **Measure the hand torque** with a torque wrench on the hex stub, slowly, one revolution | Record the peak. This is your first estimate of stator friction and it costs nothing. Over ~20 N.m: fit the break-in spacers before you go any further. |
| D-2 | Con-rod forks | The two pin axes are **90° apart**. Each joint rocks freely by hand in its own plane. |
| D-3 | Tie-rod spacers | All four within 0.2 mm of each other, and equal to `stator_len − stator_crush`. |
| D-4 | Tie-rod nuts | 20 N·m, even, in a cross pattern. Plates parallel within 0.5 mm across the diagonal. |
| D-5 | Shaft alignment | Straightedge across the coupling hubs, ≤ 0.2 mm step. |
| D-6 | Pillow-block collars | Both locked. Shaft will not move axially by hand. |
| D-7 | Auger clearance | Rotate the shaft one turn with the rear cover off; no rub anywhere in the barrel. |
| D-8 | Electrical | RCD trips on its test button. Overload set to 1.15 × FLA. Earth bonded to the frame, measured < 1 Ω. |
| D-9 | Gauge | Reads zero. Isolator diaphragm clean and screwed home. |
| D-10 | Guards | Coupling guard on. Grate bolted down. |

**Abort A-1:** the pump cannot be turned by hand → the spacers are too short
(over-crushed stator) or the rotor/stator pair is mismatched. Do not power it.
Re-cut the spacers 1 mm longer and retry.

---

## Stage W — Water test

Purpose: prove the drive, the gland, the bearings and the flow, and **measure
the stator friction torque** — the number the whole drive margin rests on.

Run first on the **drill stub** with a paddle mixer if the motor is not yet
fitted; then repeat on the motor.

| # | Step | Pass criteria |
|---|---|---|
| W-1 | Hopper full of clean water, discharge valve open, hose to the barrow. Start. | Pumps within 10 s. Steady stream, no large surging. |
| W-2 | Measure rotor speed | 185–200 rpm (design 193). Below 180 → check the ratio and the nameplate rpm. |
| W-3 | Measure flow: time filling the 20 L bucket | 8.5–10.5 L/min. Design 9.67. **Below 8 L/min on water = the stator is passing back; check crush and rotor fit.** |
| W-4 | **Measure the current, unloaded and running** | Record both. Compute the torque: `T_out = (I_run − I_noload)/(I_FLA − I_noload) × T_motor × ratio × 0.86`. Subtract the gland and auger allowances. **Put the result into `T_stator_friction` in `params.py` and re-run `calcs/pump_calcs.py`.** |
| W-5 | Gland | Weeps 1–3 drops per minute when running. Nip a flat at a time until it does. **A bone-dry gland is over-tight and will cook the sleeve.** |
| W-6 | Run 20 minutes continuously | Stuffing box warm, not hot — under 60 °C, i.e. you can hold your hand on it. Pillow blocks under 50 °C. Reducer under 70 °C. |
| W-7 | Deadhead test — **carefully** | With one hand on the bypass valve, slowly close the discharge valve while watching the gauge. **Stop at 6 bar and open the bypass.** Confirm: the machine reaches 6 bar with no leak at any joint, and the bypass drops it to zero in under 2 s. |
| W-8 | Leak check at 6 bar | No weep at either stator face, the adapter plate weld, the rear cover gasket, the chamber ring welds, or the gauge boss. |
| W-9 | Thrust | Shaft has not migrated. Mark it with a pen before and after. |

**Abort criteria — stop and fix before continuing:**
- **A-2** Running current above 1.15 × FLA → torque budget is wrong. Re-run the
  calcs with the measured friction; if the margin drops below 2.0, fit a 10:1
  reducer (and accept ~7.2 L/min) rather than pushing the motor.
- **A-3** Any leak at the stator faces at 6 bar → gaskets, or the plates are not
  parallel. Do not "just tighten it more" — the spacers stop you anyway, which
  is the point.
- **A-4** Stuffing box too hot to touch after 20 min → gland over-tight, or the
  sleeve is scored. Back off; if it persists, repack.
- **A-5** Gauge cannot reach 6 bar with the discharge shut → internal bypass in
  the stator. New stator or more crush (1 mm at a time).
- **A-6** Knocking, or flow that surges by more than ±20% → starving. Raise the
  hopper level; if it persists on water it will be far worse on grout.

**Only proceed when W-1 through W-9 all pass and `params.py` has the measured
friction torque in it.** If the drive verdict is anything but PASS, do stage B
first.

---

## Stage B -- Stator break-in  (only if W-4 came in over ~9 N.m)

Purpose: get the stator's interference torque down to something the drill can
carry, without touching anything else.

| # | Step | Pass criteria |
|---|---|---|
| B-1 | Fit the **break-in spacer set** (4 off, `stator_len - 0.5`, gauged on `gauge_tie_rod_spacers`). Nuts to 20 N.m. | All four spacers gauge identically. |
| B-2 | Re-measure hand torque at the stub (as D-1b) | Should already have dropped. |
| B-3 | Mix ~40 L of cement milk. Run 30 min, discharge open, recirculating into the barrow and back to the hopper. | Drill stays warm, not hot. Flow steady. |
| B-4 | Re-measure the friction (W-4) | Record. This is the number that decides the job. |
| B-5 | Swap to the **service spacer set**, re-measure | If the service set puts you back over the drill's continuous rating, **run the machine on the break-in set.** 0.5 mm of crush is ample for 3 bar and you can always go back. Note which set is fitted, in paint, on the frame. |
| B-6 | Flush completely (README section 8) before the milk sets | Nothing set anywhere. |

**Abort criteria:**
- **B-A1** Friction still over ~15 N.m after break-in on both spacer sets ->
  the drill is not going to drive this pump. Stop and fit the motor upgrade
  (README section 11). This is a real outcome, not a failure of the build; it
  is exactly why the hex stub was designed to take both.
- **B-A2** Flow falls below 10 L/min on the break-in spacers -> too little
  crush; the stator is slipping internally. Go back to the service set and
  accept the torque, or accept the lower flow and a longer fill.

---

## Stage M — Cement milk test

Cement and water only, **no sand**, roughly 1:1 by volume. About 40 L — one
hopper. Purpose: prove the machine against something that sets, at a viscosity
above water, without abrasive.

| # | Step | Pass criteria |
|---|---|---|
| M-1 | Prime and run into the barrow, discharge open | Flow within 8.0–10.5 L/min. |
| M-2 | Gauge, free discharge | 0.3–1.0 bar. |
| M-3 | Connect the full hose run and pump into the barrow through it | Gauge rises to 1–2 bar and holds steady. A *climbing* reading means the hose is packing. |
| M-4 | Drill load | No more than ~1 N.m (or ~1 A) above the water figure. Gearcase still only warm. |
| M-5 | Gland | Still weeping, still clean. Give it 2 strokes of grease and confirm clean grease appears at the follower. |
| M-5b | **Valve-before-trigger drill.** With the hose connected to a test tube, close the discharge valve, THEN release the trigger. Repeat five times. | It has to be automatic before there is grout in the machine. A drill freewheels: release first and the column drains back. |
| M-6 | Run the hopper down to the top of the barrel slot, then stop | Confirm you can see the level cue clearly from the operating position. This is the level you must never go below. |
| M-7 | **Full flush drill, timed** | Run README §8 steps 1–10 literally, with a stopwatch. Target: the stator and discharge head are off within **5 minutes** of the pump stopping. |
| M-8 | Inspect after the flush | Strip the drive train (§8 step 11). **No set material anywhere**: stator bore, adapter bore, barrel, auger flights, the annulus in front of the gland, the packing stack. |

**Abort criteria:**
- **A-7** M-8 finds set material in any cavity → the flush procedure is wrong for
  this build, not the operator. Find the cavity, fix the *machine* (or add the
  step), and repeat M-1 to M-8. **Do not go to grout with a cavity you cannot
  clean.** This is the single test that protects the stator.
- **A-8** Gauge climbing steadily at constant flow → hose is packing. Thin the
  mix or shorten the hose *now*, at zero cost, before there is sand in it.

---

## Stage G — Grout test

Full mix: 1:2 cement:sand, w/c ~0.50, sand **sieved to ≤ 3 mm at the pile**.
Mix one hopper (about 44 L, ~1.9 posts' worth).

Do this on a **13th post, or a length of offcut tube standing in the yard** —
not on one of the twelve. If it goes wrong you want the mistake in a scrap
tube.

| # | Step | Pass criteria |
|---|---|---|
| G-1 | Prime the hose with 5 L of cement milk first | Grout follows without a bridge. |
| G-2 | Pump into the barrow, free discharge | 8.5–10.5 L/min. Confirm against the bucket. |
| G-3 | Connect to the test post's 1" port. Pump. | Gauge settles in the **2–4 bar** band and stays there. |
| G-4 | Watch the vent at the top | Grout appears at the top in **2.0–3.0 min**. Stop when it does. |
| G-5 | Drill load | Within ~1.5 N.m of the water figure, and the gearcase still only warm after a full post. If it is hot after one post, plan a cooling break between posts and say so out loud to whoever is mixing. |
| G-6 | Compare the gauge to prediction | Compare to `calcs` section 3. If the real pressure is far above the τ₀=100 Pa row, set `grout_tau0` in `params.py` to match and re-run — you now know your actual mix. |
| G-7 | Flush, timed, per README §8 | Under 5 minutes to open. Nothing set at inspection. |
| G-8 | Next day: cut the test post open, or sound it | Solid fill, no voids, no segregation, no water pocket at the top. |

**Abort criteria:**
- **A-9** Gauge exceeds 6 bar → **open the bypass, stop.** Thin the mix, shorten
  the hose, or both. Never raise the pressure limit to suit the mix.
- **A-10** Flow drops while the current rises → the stator is packing or the
  auger is starving. Stop, open the bypass, flush immediately.
- **A-11** Grout appears at the gland → the packing has lost the fight. Stop,
  flush, repack, and increase the grease purge interval.
- **A-12** G-8 finds voids → the fill rate is too fast for the air to escape, or
  the vent is undersized. Slow down (a 10:1 reducer, or throttle at the
  discharge valve) and re-test. **Find this on the test post, not on post 9.**

---

## Production go/no-go

Go to the twelve posts only when:

- every Stage G criterion passed on the test post,
- `params.py` holds the **measured** `T_stator_friction` and `grout_tau0`,
- the drive verdict in `calcs` is PASS or MARGINAL, and if MARGINAL the day is
  planned around cooling breaks,
- which spacer set is fitted is painted on the frame,
- `python calcs/pump_calcs.py` still prints **all acceptance checks PASS** with
  those measured numbers,
- a full spare set of printed auger segments, a spare sleeve, spare packing and
  spare gaskets are in the box,
- and the flush drill has been done twice, timed, under 5 minutes.

Then plan the day as: **12 posts ≈ 29 min of pumping, 7 hopper loads, and a
flush at every break longer than 20 minutes.** The pumping is the short part.
