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
stator_end_collar_len= 0.0     # mm  TBD  collar length, if there is one
stator_crush         = 2.0     # mm  axial squeeze designed into the spacers.
                               #     Rubber-face stators: 2.0.  Steel-jacketed
                               #     stators: set to 0.0 (jacket is the stop).

# --- D6-3 rotor -------------------------------------------------------------
rotor_joint          = "pin_head"  # TBD  "pin_head" or "drill_hex"
rotor_pin_dia        = 12.0    # mm  TBD  cross-pin diameter at the rotor head
rotor_pin_eye_width  = 22.0    # mm  TBD  width of the rotor's eye/tongue
rotor_hex_af         = 19.0    # mm  TBD  across-flats, only if "drill_hex"
rotor_free_len       = 90.0    # mm  TBD  rotor sticking out of the stator, drive end
rotor_pin_inset      = 20.0    # mm  TBD  pin centre back from the rotor's rear tip
rotor_eccentricity   = 4.5     # mm  TBD  = (stator minor bore - rotor dia)/2 ... see
                               #          README "measuring eccentricity"

# --- Steel stock ------------------------------------------------------------
# BARREL: CONFIRMED.  Purchased and certified, no longer measure-first.
#   McMaster 6045N87 -- Multipurpose Low-Carbon Steel Round Tube,
#   3" OD x 0.120" wall, 2.76" ID, ERW ASTM A513 Type 1, 3 ft length, $42.13.
#   76.2 / 3.05 / 70.1 mm, which is exactly what this file already carried --
#   the numbers below did NOT change, only their status did.
#   ERW means an internal weld-seam ridge running the length of the bore.  It is
#   harmless at 4 mm auger clearance; see BOM section 2 and README section 5.3.
#   Still caliper it on arrival (README section 2a) -- certified is not measured.
barrel_od            = 76.2    # mm  CONFIRMED  McMaster 6045N87, 3" OD
barrel_wall          = 3.05    # mm  CONFIRMED  McMaster 6045N87, 0.120" wall
barrel_stock_len     = 914.4   # mm  CONFIRMED  3 ft as purchased.  The barrel is
                               #     cut from this; the rest is stock.
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
hex_free_len         = 70.0    # mm  chuck grip + standoff to the plug
hex_plug_t           = 10.0    # mm  weld plug between the sleeve and the hex bar
hex_sleeve_len       = 60.0    # mm  1-1/4" pipe sleeve gripping the shaft
hex_pin_dia          = 8.0     # mm  cross pin, stub sleeve to drive shaft

# --- PRINTED FITS -- tune these from out/fit_coupons.stl --------------------
# ONE number governs every printed feature that has to fit real stock: the
# auger cross-pin holes, the jig register faces on the tube and on the square
# post, the drill bushings on the bit, the cradle on the stator, the drill
# saddle on the drill body, the gland follower in its box.  Print the coupon
# ladder, find the step that fits, put that number here, reprint.  One edit
# retunes every part.
print_clearance      = 0.25    # mm DIAMETRAL, printed feature over real stock.
                               # Applied as /2 where it is a face or a radius.
print_clearance_step = 0.10    # mm  rung spacing on the coupon ladder

# STL meshing.  A chordal tolerance t makes an inscribed polygon, so a meshed
# BORE comes out up to 2t small on diameter -- at the old 0.05 that was 0.10 mm,
# forty percent of one ladder rung.  It cancels out (coupons and parts mesh
# identically, so a coupon measures the faceting along with everything else),
# but only while this number is the same for both.  CHANGING IT INVALIDATES A
# MEASURED print_clearance.  Coarser angular tolerance costs nothing
# dimensionally and cuts the facet count 5x -- it only affects text and fillets.
stl_tolerance        = 0.02    # mm chordal  -> 0.04 mm on a meshed diameter
stl_angular          = 0.35    # rad

# Three things that are NOT fits and are deliberately kept separate:
auger_bore_clear     = 0.50    # mm DIAMETRAL, auger hub bore over the 35 mm
                               # shaft.  A LOOSE SLIDE, not a fit, and not tuned
                               # from coupon A: the 6 mm cross pin locates the
                               # auger and carries the drive, so the bore's only
                               # job is to go on and come off with a wet, gritty
                               # shaft and five segments to line up.  Tying it to
                               # print_clearance meant that dialling the jig
                               # bushings in tight also shrank this bore, which
                               # is the one place tight buys nothing.
                               # The cross-pin hole stays on print_clearance.
running_clearance    = 0.80    # mm DIAMETRAL, printed bore around a part that
                               # TURNS in it (gland follower and lantern ring
                               # on the rotating shaft sleeve).  A gap, not a
                               # fit -- do not tune it from a coupon.
print_interference   = 0.50    # mm DIAMETRAL, printed barb that must GRIP
                               # (the NPT dust caps).  Tuned by its own coupon
                               # rung, in the opposite direction.
npt1_bore            = 26.6    # mm  1" NPT female thread minor -- what the
                               # dust cap plugs into.  Not a post dimension.

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
# --- THE TWELVE POSTS.  SQUARE PTR.  Separate stock from the pump barrel. ---
# These are 3 x 3 square PTR, NOT round tube, and NOT the same stock as the
# pump barrel.  Nothing below may be derived from barrel_od / barrel_wall and
# nothing in the barrel block may be derived from these.  They are two
# different purchases that happen to share a nominal 3".
post_shape           = "square"  #   "square" (PTR) or "round" (tube)
post_side            = 76.2    # mm  TBD  square: outside across the flats  MEASURE
post_od              = 76.2    # mm  TBD  round only; ignored when square   MEASURE
post_wall            = 3.05    # mm  TBD  cal-11 nominal 3.05               MEASURE
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
T_stator_friction    = 22.6    # N.m  TBD  dry-ish rubber drag, RPM-independent.
                               #      A GUESS until the water test -- test_plan W-4.
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
# --- post bore, by shape ----------------------------------------------------
post_across = post_side if post_shape == "square" else post_od
post_id     = post_across - 2 * post_wall          # square: side; round: dia


def post_bore_area_mm2():
    """Square PTR bores are ~27% bigger than the round tube of the same nominal
    size, and the whole cement order rides on that difference."""
    if post_shape == "square":
        return post_id ** 2
    return pi / 4 * post_id ** 2


post_area_mm2 = post_bore_area_mm2()
post_vol_L    = post_area_mm2 * post_height / 1e6

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
sleeve_len      = 110.0
packing_sq      = 10.0          # (62.7-42.2)/2 = 10.25 -> 10 mm square packing
packing_rings   = 4
lantern_len     = 12.0
follower_len    = 20.0
gland_plate_t   = 12.0
gland_stud_m    = 10.0
gland_stud_span = 96.0
x_gland_back    = x_cover_back - gland_box_len      # rear mouth of the box

# --- packing stack, from the cover face rearward ----------------------------
# order out from the machine: ring, ring, LANTERN, ring, ring, follower, plate
follower_shoulder_t = 6.0
x_lantern_deep  = x_cover_back - 2 * packing_sq
x_follower_deep = x_lantern_deep - lantern_len - 2 * packing_sq
x_gland_plate   = (x_follower_deep - follower_len - follower_shoulder_t
                   - gland_plate_t)
x_sleeve_front  = x_cover_back + 10.0
x_sleeve_back   = x_sleeve_front - sleeve_len
x_stator_cradle = 134.0         # on the front top cross member

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

# --- con-rod (rotor articulation) -------------------------------------------
conrod_len      = 140.0         # PIN TO PIN
conrod_bar      = 32.0
conrod_fork_t   = 8.0
conrod_ear_len  = 45.0
conrod_pin_end  = 14.0          # pin centre to the ear tip
tongue_t        = 12.0          # flat bar plug-welded into the shaft nose
tongue_pin_end  = 16.0          # pin centre to the tongue tip
tongue_slot     = 35.0          # depth of the slot in the shaft nose
# stickout must clear the con-rod ear tip when the joint swings:
tongue_stickout = tongue_pin_end + conrod_pin_end + 8.0
tongue_len      = tongue_slot + tongue_stickout
conrod_pin_dia  = rotor_pin_dia

# --- auger station layout ---------------------------------------------------
# --- ROTOR / CON-ROD / SHAFT CHAIN.  Everything downstream follows from it. --
# Worked forward from the rotor, because the rotor's position is set by the
# stator and nothing else can move.  The auger front used to be a hard-coded
# -30, which put the shaft nose 200 mm inside the space the con-rod needs.
x_rotor_tip     = -rotor_free_len                       # rotor's rear tip
x_rotor_pin     = x_rotor_tip + rotor_pin_inset
x_shaft_pin     = x_rotor_pin - conrod_len
x_shaft_nose    = x_shaft_pin - (tongue_stickout - tongue_pin_end)
x_auger_front   = x_shaft_nose - 12.0
x_auger_back    = -615.0        # right up to the rear cover: a dead annulus at the
                                # gland is a cavity the flush procedure cannot reach
auger_len       = x_auger_front - x_auger_back

auger_od        = barrel_id - 2 * auger_radial_clear
auger_hub_od    = shaft_dia + 2 * auger_hub_wall
auger_hub_bore  = shaft_dia + auger_bore_clear      # slide fit, see Block A
_flight_area    = pi / 4 * (auger_od**2 - auger_hub_od**2)          # mm2
# swept volume per rev = A * (pitch - flight_t) * fill.  Solve for pitch:
_pitch_ideal    = (auger_overfeed * pump_disp_cc * 1000.0
                   / (_flight_area * auger_fill_eta) + auger_flight_t)
# then snap it so a whole number of pitches exactly fills the auger span --
# that is what keeps every cross-pin hole on the same clock angle.
# floor, not round: snapping to a FINER pitch than the ideal cuts the swept
# volume and can drop the overfeed below target.  Coarser is always safe.
n_auger_pitch   = max(1, int(auger_len / _pitch_ideal))
auger_pitch     = auger_len / n_auger_pitch
auger_pitch_alt = auger_len / max(1, n_auger_pitch - 2)   # coarser spare set
auger_seg_len   = 2 * auger_pitch
n_auger_full    = int(auger_len / auger_seg_len + 1e-9)
auger_tail_len  = auger_len - n_auger_full * auger_seg_len
auger_clear     = auger_radial_clear
auger_swept_cc  = (_flight_area * (auger_pitch - auger_flight_t)
                   * auger_fill_eta / 1000.0)            # cm3/rev, actual

# --- frame ------------------------------------------------------------------
barrel_cl_h     = 750.0         # barrel centreline above the ground
# The top rails pass under the STATOR (89 OD), not the barrel (76.2 OD), and
# the stator cradle has to fit between the rail top and the stator.  Deriving
# the rail height from the barrel put the rails 6 mm inside the stator.
stator_cradle_base = 14.0
stator_cradle_h = stator_od / 2 + 0.5 + stator_cradle_base
top_rail_top    = barrel_cl_h - stator_cradle_h
top_rail_z      = top_rail_top - ptr_size
barrel_saddle_h = barrel_cl_h - barrel_od / 2 - top_rail_top
skid_len        = 1450.0
skid_w          = 600.0

# --- bearings ---------------------------------------------------------------
pillow_block    = "UCP207"      # 35 mm bore
x_pb_front      = -790.0
x_pb_rear       = -900.0

# --- drill drive station ----------------------------------------------------
x_shaft_rear    = -1000.0       # end of the 35 mm shaft.  Set by the rear
                                # pillow block plus the hex stub sleeve: the
                                # assembly clash check found the 42 mm sleeve
                                # sitting inside the UCP207 housing.
# the weld plug sits BEYOND the shaft end, so the chuck face is a plug
# thickness further back than hex_free_len alone suggests
x_hex_back      = x_shaft_rear - hex_plug_t - hex_free_len
# stations derived from the MEASURED drill dimensions, not guessed:
x_chuck_front   = x_hex_back + drill_chuck_depth       # jaws close here
x_chuck_back    = x_chuck_front - drill_chuck_body_len # gearcase nose
# One steel bracket does both jobs: a half-round torque lug at its front edge
# bearing on the aux-handle collar, and a flat behind it carrying the printed
# saddle.  Sizing the saddle at 130 long put it straight through the lug --
# there is only (drill_body_len - drill_aux_offset) of body behind the collar.
x_torque_lug    = x_chuck_back - drill_aux_offset      # set by the DRILL
cradle_plate_t  = 10.0
cradle_plate_l  = 46.0
x_drill_upright = x_torque_lug - 9.0 - cradle_plate_l / 2
x_drill_cradle  = x_drill_upright                      # printed saddle: CLAMP ONLY
cradle_wall     = 8.0           # printed saddle wall under the drill
cradle_clr      = print_clearance / 2   # radial, on the drill body
cradle_foot_t   = 12.0          # printed saddle foot onto the steel plate
cradle_strap_t  = 10.0
# height of the drill axis above the steel cradle plate, from the printed
# saddle's own stack.  frame_drawing and assembly both read this, so the
# strap cannot end up 0.4 mm inside the saddle again.
cradle_axis_local = cradle_foot_t + cradle_wall + drill_body_dia / 2 + cradle_clr

# --- 3D printer -------------------------------------------------------------
printer_x       = 350.0         # mm  TBD  confirm against the H2C spec  VERIFY
printer_y       = 320.0         # mm  TBD
printer_z       = 325.0         # mm  TBD
nozzle          = 0.4

# --- misc measured inputs for the printed jigs ------------------------------
bucket_rim_od   = 295.0         # mm  TBD  5-gal bucket outside rim dia   MEASURE
hardware_cloth  = 3.175         # mm  1/8" mesh -- this IS the <=3 mm sand screen


def open_questions():
    """Every input still carrying a TBD, read out of THIS FILE's own source so
    the list cannot drift from the parameters it describes.

    A TBD is not a missing feature: the geometry around it is right and the
    number is a placeholder.  This exists so the design summary can say, on one
    screen, exactly how much of the machine is still a guess -- and so that
    confirming a part (the barrel, on the McMaster order) visibly SHORTENS the
    list instead of leaving a stale sentence behind in a README.

    Returns [(block, name, value, note), ...] in file order.
    """
    import os, re
    src = open(os.path.abspath(__file__)).read().splitlines()
    hdr = re.compile(r"^#\s*-{3,}\s*(.+?)\s*-{3,}\s*$")
    asg = re.compile(r"^(\w+)\s*=\s*([^#]+?)\s*#\s*(.+)$")
    cont = re.compile(r"^\s+#\s*(.*)$")
    block, out, open_row = "(unfiled)", [], None
    for ln in src:
        h = hdr.match(ln)
        if h:
            block, open_row = h.group(1).rstrip(". "), None
            continue
        m = asg.match(ln)
        if m:
            open_row = None
            if "TBD" not in m.group(3):
                continue
            unit, _, note = m.group(3).partition("TBD")
            out.append([block, m.group(1), f"{m.group(2).strip()} {unit.strip()}".strip(),
                        note.strip()])
            open_row = out[-1]
            continue
        c = cont.match(ln)                  # wrapped comment under a TBD line
        if c and open_row is not None:
            open_row[3] += " " + c.group(1)
        elif not ln.strip().startswith("#"):
            open_row = None
    for r in out:                           # tidy: the ACTION is not the note
        n = " ".join(r[3].split()).strip(" .")
        for tail in ("MEASURE", "VERIFY"):
            if n.endswith(tail):
                n = n[: -len(tail)].strip(" .")
        r[3] = n
    return [tuple(r) for r in out]


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
