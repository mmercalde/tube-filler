"""
TUBE-FILLER -- D6-3 rotor/stator grout pump.
SINGLE SOURCE OF TRUTH.  Every calc, every CAD model, every drawing and the
BOM cut lengths are derived from this file.  Change a MEASURED INPUT here and
re-run `python cad/build_all.py` -- nothing else needs editing.

Units: millimetres and degrees everywhere in this file (CAD-native).
calcs/pump_calcs.py converts to SI internally.
"""
from math import pi, sqrt, atan2, degrees, ceil

# =============================================================================
# BLOCK A -- MEASURED INPUTS
# Owner fills these in when the parts arrive.  Anything marked TBD is a
# PLACEHOLDER: the geometry is correct in form but the number is a guess.
# Measure, edit, re-run.  Nothing else in the project hard-codes these.
# =============================================================================

# --- D6-3 stator (vendor spec, verify with calipers) -------------------------
stator_od            = 89.0    # mm  vendor: 89.0 (3.50")           VERIFY
stator_len           = 270.0   # mm  vendor: 270.0 (10.63")         VERIFY
stator_shore_a       = 73.0    #     vendor: 73 Shore A
stator_max_grain     = 3.0     # mm  vendor
pump_disp_cc         = 50.0    # cm3/rev  vendor: 20 L/min @ 400 rpm.  FIXED FACT.
stator_inlet_bore    = 50.0    # mm  TBD  bore visible at the stator end face
stator_has_steel_jacket = False #    TBD  True if the rubber is bonded inside a
                               #          steel tube (changes the clamp calc)
stator_end_style     = "plain" #     TBD  "plain" (flat rubber face) or "collar"
stator_end_collar_od = 89.0    # mm  TBD  only used if stator_end_style=="collar"
stator_end_collar_len= 0.0     # mm  TBD
stator_crush         = 2.0     # mm  axial squeeze designed into the spacers.
                               #     Rubber-face stators: 2.0.  Steel-jacketed
                               #     stators: set to 0.0 (jacket is the stop).

# --- D6-3 rotor -------------------------------------------------------------
rotor_joint          = "pin_head"  # TBD  "pin_head" or "drill_hex"
rotor_pin_dia        = 12.0    # mm  TBD  cross-pin diameter at the rotor head
rotor_pin_eye_width  = 22.0    # mm  TBD  width of the rotor's eye/tongue
rotor_hex_af         = 19.0    # mm  TBD  across-flats, only if "drill_hex"
rotor_free_len       = 90.0    # mm  TBD  rotor sticking out of the stator, drive end
rotor_eccentricity   = 4.5     # mm  TBD  = (stator minor bore - rotor dia)/2 ... see
                               #          README "measuring eccentricity"

# --- Owner's steel stock ----------------------------------------------------
barrel_od            = 76.2    # mm  TBD  3" tubular, nominal 76.2             MEASURE
barrel_wall          = 3.05    # mm  TBD  cal-11 = 3.05                        MEASURE
ptr_size             = 50.8    # mm  2" square PTR
ptr_wall             = 3.05    # mm  cal-11

# --- PRIMARY DRIVE: 1/2" spade-handle paddle drill ---------------------------
# The drill drives the pump directly through the rear hex stub.  There is no
# motor, no reducer and no coupling on this machine.
drive_kind           = "drill"
drill_power_w        = 900.0   # W   nameplate input
drill_rpm            = 250.0   # rpm chosen operating speed in LOW range
drill_rpm_low_max    = 550.0   # rpm top of the low range
drill_T_cont         = 15.0    # N.m continuous, at drill_rpm            MEASURED INPUT
drill_T_burst        = 25.0    # N.m short burst / breakaway             MEASURED INPUT
drill_chuck          = 12.7    # mm  1/2" chuck capacity
drill_body_dia       = 57.0    # mm  TBD  BARREL/GEARCASE DIA at the cradle station.
                               #     Calipers on the drill, just behind the chuck
                               #     collar, at the widest round section.   MEASURE
drill_body_len       = 110.0   # mm  TBD  length of that round section     MEASURE
drill_aux_handle_dia = 43.0    # mm  TBD  auxiliary-handle collar dia (the Euro
                               #     43 mm collar is common).  The steel torque
                               #     lug bears here.                       MEASURE
drill_chuck_depth    = 40.0    # mm  TBD  how deep the jaws grip           MEASURE
drill_chuck_body_len = 85.0    # mm  TBD  chuck front face to gearcase nose  MEASURE
drill_aux_offset     = 60.0    # mm  TBD  gearcase nose to aux-handle collar MEASURE

# --- Rear hex stub: the primary input ---------------------------------------
hex_af               = 12.7    # mm  1/2" A/F.  13 mm also fits a 1/2" chuck.
hex_free_len         = 70.0    # mm  chuck grip + standoff to the stub sleeve
hex_pin_dia          = 8.0     # mm  cross pin, stub sleeve to drive shaft

# --- UPGRADE PATH -- documented, NOT fitted, NOT in the BOM total -----------
# The motor + reducer bolt to the same hex stub via a bored coupling half.
# calcs prints the upgrade line so the comparison stays honest.
up_motor_kw          = 1.5
up_motor_rpm         = 1450.0
up_motor_frame       = "90L"
up_motor_shaft_dia   = 24.0
up_motor_flange      = "B14 FT130"
up_gearbox_model     = "NMRV-050"
up_gearbox_ratio     = 7.5
up_gearbox_eff       = 0.86
up_gearbox_out_shaft = 25.0

# --- Duty -------------------------------------------------------------------
post_od              = 76.2    # mm  the 12 posts are the same 3" stock
post_wall            = 3.05    # mm
post_height          = 6000.0  # mm
n_posts              = 12
grout_sg             = 2.1
post_port_height     = 150.0   # mm  1" NPT port centre above the post base
post_port_hole       = 33.0    # mm  hole saw for a 1" NPT half coupling
post_vent_dia        = 12.0    # mm  vent hole at the top of each post
post_vent_from_top   = 100.0   # mm  vent centre below the post top
hose_id              = 25.4    # mm  1" hose
hose_len             = 8000.0  # mm  DESIGN VALUE -- see calcs, keep it short
grout_tau0           = 100.0   # Pa  Bingham yield stress. 50=soupy 300=stiff.
grout_mu_p           = 0.10    # Pa.s Bingham plastic viscosity
design_pressure      = 6.0     # bar  every wetted steel joint is designed here
                               #      (3x the ~2 bar duty), per the brief

# --- Torque budget (see calcs for the breakdown) ----------------------------
# T_stator_friction is the single number the whole drive question turns on and
# it is a GUESS until the water test measures it (test_plan W-4).  On the
# 1.5 kW motor it barely mattered.  On a 900 W drill it decides whether the
# machine runs at all.  MEASURE IT FIRST.
T_stator_friction    = 22.6    # N.m  dry-ish rubber drag, RPM-independent.
T_gland              = 5.0     # N.m  packed gland, normal service preload
T_gland_drill        = 2.5     # N.m  gland run deliberately loose (weeping) for
                               #      drill drive -- see README break-in
T_auger              = 1.0     # N.m  screw + churning
drive_margin_min     = 1.30    # x    on CONTINUOUS torque.  Not 2.0: a hand
                               #      drill is not a 2x-margin drive and
                               #      pretending otherwise helps nobody.


# =============================================================================
# BLOCK B -- DERIVED GEOMETRY.  Do not edit; edit Block A.
# =============================================================================

barrel_id   = barrel_od - 2 * barrel_wall          # 70.1
post_id     = post_od - 2 * post_wall

# --- tie-rod / clamp circle -------------------------------------------------
tie_rod_m       = 10.0                              # M10 threaded rod
tie_rod_hole    = 11.0                              # 11 mm drill
n_tie_rods      = 4
spacer_od       = 26.7                              # 3/4" sch40 pipe OD
spacer_id       = 20.9                              # 3/4" sch40 pipe ID (M10 passes)
tie_gap         = 5.0                               # clearance stator OD -> spacer
tie_bc_r        = stator_od/2 + tie_gap + spacer_od/2
tie_bc          = 2 * tie_bc_r                      # ~125.7 bolt circle dia
# rods sit on the plate diagonals so the plate stays small
tie_xy          = tie_bc_r * sqrt(0.5)              # +/- offset in x and y
plate_edge      = 8.0
plate_size      = 5 * ceil((2*(tie_xy + spacer_od/2 + plate_edge))/5)   # 135
plate_t         = 10.0
spacer_len      = stator_len - stator_crush         # HARD STOP -- see README

# --- adapter plate ----------------------------------------------------------
adapter_bore    = stator_inlet_bore                 # no step into the stator

# --- discharge head ---------------------------------------------------------
disch_ring_od   = 60.3          # 2" sch40 pipe
disch_ring_id   = 52.5
disch_ring_len  = 35.0
disch_rear_bore = 54.0          # hole saw, clears the ring bore
disch_cap_size  = 90.0
disch_cap_t     = 10.0
disch_cap_bore  = 27.0          # 1" NPT half-coupling minor
disch_gauge_hole= 12.0          # 1/4" NPT half-coupling boss on the ring

# --- drive shaft ------------------------------------------------------------
shaft_dia       = 35.0          # UCP207 bore; set by the deflection check, not torque
shaft_key       = 10.0          # 10x8 key at the coupling end
xpin_dia        = 6.0           # auger drive cross-pins (drill press)

# --- feed auger -------------------------------------------------------------
# Design intent, not geometry: the geometry below is SOLVED from these so the
# auger always tracks the barrel and the shaft.
auger_radial_clear = 4.0        # mm, set by the shaft-deflection check
auger_hub_wall     = 4.5        # mm of printed plastic over the shaft
auger_flight_t     = 6.0        # mm axial, constant root to tip
auger_fill_eta     = 0.75       # flooded hopper, dense fluid
auger_overfeed     = 1.35       # x the stator swallow rate.  A PC pump must
                                # never starve; brief calls for ~1.3.
auger_pin_boss  = 56.0          # local boss around the cross-pin
auger_boss_len  = 22.0

# --- barrel / layout.  x = 0 at the FRONT FACE of the adapter plate. --------
barrel_len      = 600.0
x_adapter_front = 0.0
x_adapter_back  = -plate_t
x_barrel_front  = x_adapter_back
x_barrel_back   = x_barrel_front - barrel_len       # -610
barrel_flange   = 140.0                             # square, bolted rear closure
barrel_flange_t = 10.0
barrel_bolt_m   = 10.0
barrel_bolt_bc  = 118.0                             # 4 off, on the diagonals
x_flange_back   = x_barrel_back - barrel_flange_t   # -620
x_cover_back    = x_flange_back - barrel_flange_t   # -630

# --- stuffing box -----------------------------------------------------------
gland_box_od    = 73.0          # 2-1/2" sch40 pipe
gland_box_id    = 62.7
gland_box_len   = 95.0
sleeve_od       = 42.2          # 1-1/4" sch40 pipe, ID 35.05 -> slides on the shaft
sleeve_id       = 35.05         # SACRIFICIAL: the packing wears this, not the shaft
sleeve_len      = 130.0
packing_sq      = 10.0          # (62.7-42.2)/2 = 10.25 -> 10 mm square packing
packing_rings   = 4
lantern_len     = 12.0
follower_len    = 20.0
gland_plate_t   = 12.0
gland_stud_m    = 10.0
gland_stud_span = 96.0
x_gland_back    = x_cover_back - gland_box_len      # -725

# --- hopper -----------------------------------------------------------------
hop_top_l       = 520.0         # along the barrel axis
hop_top_w       = 420.0
hop_bot_l       = 210.0
hop_bot_w       = 70.0
hop_depth       = 460.0
hop_wall_t      = 3.0
barrel_slot_l   = 200.0         # cutout in the top of the barrel
barrel_slot_w   = 50.0
x_hop_bot_front = -350.0        # slot spans -550 .. -350
grate_pitch     = 25.0          # tramp grate bar spacing (NOT a 3 mm sieve)
collar_top_z    = 75.0          # hopper throat top, above the barrel axis
hop_lap         = 20.0          # lap on one sloping edge of each long wall

def hopper_volume_L():
    """Rectangular frustum, top and bottom rectangles concentric."""
    a1 = hop_top_l * hop_top_w
    a2 = hop_bot_l * hop_bot_w
    return hop_depth / 3.0 * (a1 + a2 + sqrt(a1 * a2)) / 1e6

hop_vol_L       = hopper_volume_L()
hop_slant_long  = sqrt(hop_depth**2 + ((hop_top_w - hop_bot_w) / 2)**2)
hop_slant_short = sqrt(hop_depth**2 + ((hop_top_l - hop_bot_l) / 2)**2)
hop_ang_long    = degrees(atan2(hop_depth, (hop_top_w - hop_bot_w) / 2))
hop_ang_short   = degrees(atan2(hop_depth, (hop_top_l - hop_bot_l) / 2))

# --- auger station layout ---------------------------------------------------
x_auger_front   = -30.0
x_auger_back    = -615.0        # right up to the rear cover: a dead annulus at the
                                # gland is a cavity the flush procedure cannot reach
auger_len       = x_auger_front - x_auger_back

auger_od        = barrel_id - 2 * auger_radial_clear
auger_hub_od    = shaft_dia + 2 * auger_hub_wall
_flight_area    = pi / 4 * (auger_od**2 - auger_hub_od**2)          # mm2
# swept volume per rev = A * (pitch - flight_t) * fill.  Solve for pitch:
_pitch_ideal    = (auger_overfeed * pump_disp_cc * 1000.0
                   / (_flight_area * auger_fill_eta) + auger_flight_t)
# then snap it so a whole number of pitches exactly fills the auger span --
# that is what keeps every cross-pin hole on the same clock angle.
n_auger_pitch   = max(1, int(round(auger_len / _pitch_ideal)))
auger_pitch     = auger_len / n_auger_pitch
auger_pitch_alt = auger_len / max(1, n_auger_pitch - 2)   # coarser spare set
auger_seg_len   = 2 * auger_pitch
n_auger_full    = int(auger_len // auger_seg_len)
auger_tail_len  = auger_len - n_auger_full * auger_seg_len
auger_clear     = auger_radial_clear
auger_swept_cc  = (_flight_area * (auger_pitch - auger_flight_t)
                   * auger_fill_eta / 1000.0)            # cm3/rev, actual

# --- con-rod (rotor articulation) -------------------------------------------
conrod_len      = 140.0
conrod_bar      = 32.0
conrod_fork_t   = 8.0
tongue_t        = 12.0          # flat bar plug-welded into the shaft nose
conrod_pin_dia  = rotor_pin_dia

# --- frame ------------------------------------------------------------------
barrel_cl_h     = 750.0         # barrel centreline above the ground
skid_len        = 1400.0
skid_w          = 600.0

# --- bearings ---------------------------------------------------------------
pillow_block    = "UCP207"      # 35 mm bore
x_pb_front      = -800.0
x_pb_rear       = -920.0

# --- drill drive station ----------------------------------------------------
x_shaft_rear    = -960.0        # end of the 35 mm shaft
x_hex_back      = x_shaft_rear - hex_free_len          # -1030, chuck lives here
# stations derived from the MEASURED drill dimensions, not guessed:
x_chuck_front   = x_hex_back + drill_chuck_depth       # jaws close here
x_chuck_back    = x_chuck_front - drill_chuck_body_len # gearcase nose
x_drill_upright = x_chuck_back - drill_aux_offset      # ONE steel upright
x_torque_lug    = x_drill_upright                      # steel lug: TORQUE PATH
x_drill_cradle  = x_drill_upright - 55                 # printed saddle: CLAMP ONLY
cradle_plate_t  = 10.0
cradle_plate_l  = 130.0
cradle_wall     = 8.0           # printed saddle wall under the drill
cradle_foot_t   = 12.0          # printed saddle foot onto the steel plate
cradle_strap_t  = 10.0

# --- 3D printer -------------------------------------------------------------
printer_x       = 350.0         # mm  TBD  confirm against the H2C spec  VERIFY
printer_y       = 320.0         # mm  TBD
printer_z       = 325.0         # mm  TBD
nozzle          = 0.4

# --- misc measured inputs for the printed jigs ------------------------------
bucket_rim_od   = 295.0         # mm  TBD  5-gal bucket outside rim dia   MEASURE
hardware_cloth  = 3.175         # mm  1/8" mesh -- this IS the <=3 mm sand screen


def summary_lines():
    """Rows used by the README/BOM generators so nothing is transcribed by hand."""
    return [
        ("barrel ID",            f"{barrel_id:.1f} mm"),
        ("tie-rod bolt circle",  f"{tie_bc:.1f} mm ({n_tie_rods} x M{tie_rod_m:.0f})"),
        ("clamp plate",          f"{plate_size:.0f} x {plate_size:.0f} x {plate_t:.0f} mm"),
        ("spacer tube length",   f"{spacer_len:.1f} mm  (HARD STOP)"),
        ("auger",                f"OD {auger_od:.0f}, pitch {auger_pitch:.0f}, "
                                 f"{n_auger_full} x {auger_seg_len:.0f} mm segments"
                                 + (f" + 1 x {auger_tail_len:.0f}" if auger_tail_len > 1 else "")),
        ("drive shaft",          f"{shaft_dia:.0f} mm on {pillow_block}"),
        ("stuffing box",         f"2-1/2\" sch40 x {gland_box_len:.0f}, "
                                 f"{packing_rings} x {packing_sq:.0f} mm square packing"),
        ("hopper",               f"{hop_top_l:.0f} x {hop_top_w:.0f} x {hop_depth:.0f} deep"),
    ]
