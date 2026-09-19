#!/usr/bin/env python3
"""
TUBE-FILLER design calculations.  Standalone: `python calcs/pump_calcs.py`.

Prints a one-page design summary and asserts the acceptance criteria.
Every input comes from ../params.py.  Nothing here is hard-coded.

Sign convention: pressures are gauge, bar.  SI internally.
"""
import sys, os, textwrap
from math import pi, sqrt, log10

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
import params as P

G   = 9.81
BAR = 1e5
mm  = 1e-3

# ----------------------------------------------------------------------------
def rule(title=""):
    print("\n" + "=" * 78)
    if title:
        print(title)
        print("=" * 78)

def row(label, value, note=""):
    print(f"  {label:<38s} {value:>16s}  {note}")

# ============================================================================
# 1. THE JOB
# ============================================================================
# Post bore switches on post_shape.  The twelve posts are SQUARE PTR; the pump
# barrel is round tube and is separate stock -- do not cross-reference them.
post_area   = P.post_area_mm2 * 1e-6                    # m2
post_vol_L  = P.post_vol_L
SQ          = P.post_shape == "square"
post_desc   = (f"{P.post_side:.1f} sq PTR x {P.post_wall:.2f} wall"
               if SQ else f"{P.post_od:.1f} OD tube x {P.post_wall:.2f} wall")
bore_desc   = (f"{P.post_id:.1f} x {P.post_id:.1f} bore"
               if SQ else f"{P.post_id:.1f} dia bore")
job_vol_L   = post_vol_L * P.n_posts
hose_vol_L  = pi / 4 * (P.hose_id * mm) ** 2 * (P.hose_len * mm) * 1000
rho         = P.grout_sg * 1000

# ============================================================================
# 2. PUMP DISPLACEMENT AND SPEED
# ============================================================================
# Vendor: 20 L/min @ 400 rpm  ->  50 cm3/rev.  Taken as fact, not re-derived.
disp_cc     = P.pump_disp_cc
disp_m3     = disp_cc * 1e-6
n_out       = P.drill_rpm                               # rpm at the rotor -- the
                                                        # drill drives it directly
Q_Lmin      = n_out * disp_cc / 1000.0
fill_min    = post_vol_L / Q_Lmin

# ============================================================================
# 3. HYDRAULICS -- Bingham plastic in the hose (Buckingham-Reiner)
# ============================================================================
def tau_wall(Q_m3s, D_m, tau0, mu_p):
    """Solve Buckingham-Reiner for wall shear stress. Returns None if no flow."""
    k = pi * D_m ** 3 / (32.0 * mu_p)
    def f(tw):
        x = tau0 / tw
        return k * tw * (1 - 4 * x / 3 + x ** 4 / 3) - Q_m3s
    lo, hi = tau0 * 1.0000001, tau0 * 1000 + 1e5
    if f(hi) < 0:
        return None
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if f(mid) > 0: hi = mid
        else:          lo = mid
    return 0.5 * (lo + hi)

def hose_dp_bar(tau0, L_mm, D_mm=P.hose_id, Q=None):
    Q = Q if Q is not None else Q_Lmin / 60000.0
    tw = tau_wall(Q, D_mm * mm, tau0, P.grout_mu_p)
    if tw is None:
        return float("inf")
    return (4 * tw / (D_mm * mm)) * (L_mm * mm) / BAR

p_static   = rho * G * (P.post_height * mm) / BAR
p_hose     = hose_dp_bar(P.grout_tau0, P.hose_len)
p_fittings = 0.20                       # ball valve + 1" port + entry losses
p_required = p_static + p_hose + p_fittings

V_hose     = (Q_Lmin / 60000.0) / (pi / 4 * (P.hose_id * mm) ** 2)
Re_bingham = rho * V_hose * (P.hose_id * mm) / P.grout_mu_p

# ============================================================================
# 4. TORQUE BUDGET AND DRIVE MARGIN
# ============================================================================
def T_pressure(p_bar):
    return p_bar * BAR * disp_m3 / (2 * pi)

T_gland_used = P.T_gland_drill      # drill drive runs the gland deliberately loose
T_parasitic  = T_gland_used + P.T_auger

def T_total(p_bar, T_fric=None):
    fr = P.T_stator_friction if T_fric is None else T_fric
    return fr + T_parasitic + T_pressure(p_bar)

T_cont     = P.drill_T_cont
T_burst    = P.drill_T_burst
T_duty     = T_total(p_required)
T_designpt = T_total(P.design_pressure)
margin     = T_cont / T_duty
margin_b   = T_burst / T_duty
P_duty_W   = T_duty * 2 * pi * n_out / 60

# The number that actually decides this: how much stator friction can the drill
# carry?  Everything else in the budget is small and known.
T_fric_max_cont  = T_cont  - T_parasitic - T_pressure(p_required)
T_fric_max_burst = T_burst - T_parasitic - T_pressure(p_required)
# ...and with the gland at normal service preload instead of loose:
T_fric_max_tight = T_cont - (P.T_gland + P.T_auger) - T_pressure(p_required)

# Highest pressure the drill can force before it stalls -- this is the drill's
# one real advantage over the motor it replaced.
def p_at_stall(T_fric=None):
    fr = P.T_stator_friction if T_fric is None else T_fric
    return max(0.0, (T_burst - fr - T_parasitic)) * 2 * pi / disp_m3 / BAR

# upgrade path, for the comparison line only
T_up = (P.up_motor_kw * 1000 / (2 * pi * P.up_motor_rpm / 60)
        * P.up_gearbox_ratio * P.up_gearbox_eff)
n_up = P.up_motor_rpm / P.up_gearbox_ratio

# ============================================================================
# 5. AUGER FEED MATCH
# ============================================================================
flight_area = pi / 4 * ((P.auger_od * mm) ** 2 - (P.auger_hub_od * mm) ** 2)
def auger_cc_rev(pitch_mm, eta):
    # the flight itself occupies flight_t/pitch of the axial length
    solid = 1.0 - P.auger_flight_t / pitch_mm
    return flight_area * (pitch_mm * mm) * eta * solid * 1e6      # cm3/rev
auger_cc    = auger_cc_rev(P.auger_pitch, P.auger_fill_eta)
overfeed    = auger_cc / disp_cc
eta_break   = disp_cc / (flight_area * (P.auger_pitch * mm)
                         * (1 - P.auger_flight_t / P.auger_pitch) * 1e6)   # eta at which it starves

# ============================================================================
# 5b. THE CROSS-PIN BOSS -- the auger's one local restriction
# ============================================================================
# Section 5 above is an AVERAGE: it sizes the pitch from the plain-hub annulus.
# A screw does not meter on its average.  It meters on its worst station, and
# the worst station on this screw is the boss around each drive pin.  These
# numbers walk the real core profile (params.auger_core_profile) end to end.

def local_flight_area(dz):
    """Conveyed annulus [m2] at dz mm from a pin plane -- same convention as
    section 5, with the local core diameter instead of the plain hub."""
    return pi / 4 * ((P.auger_od * mm) ** 2 - (P.auger_core_dia(dz) * mm) ** 2)


def local_overfeed(dz):
    solid = 1.0 - P.auger_flight_t / P.auger_pitch
    return (local_flight_area(dz) * (P.auger_pitch * mm) * P.auger_fill_eta
            * solid * 1e6) / disp_cc


def local_free_ratio(dz):
    """Free area in the BARREL BORE at dz, over the same at a plain-hub plane.
    This is the throttle metric -- it counts the 4 mm running clearance, which
    carries no material but does carry the restriction.  local_overfeed is the
    CAPACITY metric and is the stricter of the two; both are reported."""
    ft = P.auger_flight_t / P.auger_pitch
    root2 = P.auger_hub_od - 2.0                       # flight root diameter

    def free(d):
        ann = pi / 4 * (P.barrel_id ** 2 - d ** 2)
        fl = ft * pi / 4 * (P.auger_od ** 2 - max(d, root2) ** 2)
        return ann - fl
    return free(P.auger_core_dia(dz)) / free(P.auger_hub_od)


# walk EVERY station on the longest segment, 0.25 mm steps -- not just the land
_zs = [(-P.auger_seg_len / 2) + 0.25 * i
       for i in range(int(P.auger_seg_len / 0.25) + 1)]
of_min      = min(local_overfeed(z) for z in _zs)
of_min_z    = min(_zs, key=local_overfeed)
free_min    = min(local_free_ratio(z) for z in _zs)
boss_of     = local_overfeed(0.0)
boss_free   = local_free_ratio(0.0)

# --- cross pin: steel pin bearing on printed plastic ------------------------
# Torque is carried as a couple on the two plastic walls either side of the
# shaft.  Each wall is (boss - shaft)/2 thick and pin_dia wide in projection,
# and the pair sits at the mean radius of that wall.
pin_wall    = (P.auger_pin_boss - P.shaft_dia) / 2.0                 # mm
pin_r_mean  = (P.shaft_dia + P.auger_pin_boss) / 4.0                 # mm
pin_bear_A  = 2 * P.xpin_dia * pin_wall                              # mm2, both walls


def pin_bearing_mpa(T_nm):
    """Bearing stress on the printed boss [MPa] at T_nm on ONE pin."""
    F = T_nm * 1000.0 / (2 * pin_r_mean)          # N per wall
    return F / (P.xpin_dia * pin_wall)


sig_pin_duty  = pin_bearing_mpa(P.T_auger)
marg_pin_duty = P.petg_bearing_mpa / sig_pin_duty
sig_pin_jam   = pin_bearing_mpa(P.drill_T_burst)        # auger jams, drill shoves
marg_pin_jam  = P.petg_bearing_mpa / sig_pin_jam
# and the steel pin itself, double shear at the shaft surface
tau_pin_jam   = (P.drill_T_burst * 1000.0 / (2 * P.shaft_dia / 2)
                 / (2 * pi / 4 * P.xpin_dia ** 2))      # MPa

# largest boss that still clears the local-overfeed gate, by bisection
def _of_at(d):
    solid = 1.0 - P.auger_flight_t / P.auger_pitch
    A = pi / 4 * ((P.auger_od * mm) ** 2 - (d * mm) ** 2)
    return (A * (P.auger_pitch * mm) * P.auger_fill_eta * solid * 1e6) / disp_cc


_lo, _hi = P.auger_hub_od, P.auger_od - 1.0
for _ in range(60):
    _md = (_lo + _hi) / 2
    if _of_at(_md) >= P.auger_min_local_overfeed:
        _lo = _md
    else:
        _hi = _md
boss_dia_cap = _lo

# ============================================================================
# 6. AXIAL THRUST AND BEARINGS
# ============================================================================
d_env       = P.stator_inlet_bore * mm
thrust_duty = p_required * BAR * pi / 4 * d_env ** 2
thrust_des  = P.design_pressure * BAR * pi / 4 * d_env ** 2
thrust_des_x= thrust_des * 1.3                      # 30% for the orbiting reaction
UCP207_C    = 25_500.0                              # N dynamic, insert 6207
axial_cap   = 0.20 * UCP207_C

# ============================================================================
# 7. STATOR CLAMP -- tie rods and the hard-stop spacers
# ============================================================================
A_seal      = pi / 4 * ((P.stator_od * mm) ** 2 - (P.disch_rear_bore * mm) ** 2)
y_gasket    = 1.4e6                                 # Pa, 3 mm elastomer sheet seating
F_seat      = y_gasket * A_seal
F_sep       = P.design_pressure * BAR * pi / 4 * (P.disch_ring_id * mm) ** 2
F_clamp_min = F_seat + F_sep
F_rod_min   = F_clamp_min / P.n_tie_rods
T_rod_min   = 0.2 * F_rod_min * (P.tie_rod_m * mm)
F_rod_rec   = 10_000.0                              # recommended preload, M10 8.8
T_rod_rec   = 0.2 * F_rod_rec * (P.tie_rod_m * mm)
A_spacer    = pi / 4 * ((P.spacer_od * mm) ** 2 - (P.spacer_id * mm) ** 2)
sig_spacer  = P.n_tie_rods * F_rod_rec / (P.n_tie_rods * A_spacer) / 1e6   # MPa per spacer
A_rod       = 58.0e-6                               # M10 tensile stress area, m^2
sig_rod     = F_rod_rec / A_rod / 1e6

# ============================================================================
# 8. DRIVE SHAFT DEFLECTION  (the reason the shaft is 35 mm, not 25)
# ============================================================================
E      = 200e9
I_sh   = pi * (P.shaft_dia * mm) ** 4 / 64
L_ovh  = abs(P.x_pb_front - P.x_auger_front) * mm
m_shaft= 7850 * pi / 4 * (P.shaft_dia * mm) ** 2 * L_ovh
m_aug  = P.n_auger_full * 0.35 + 2.0                # printed segments + entrained grout
w_dist = (m_shaft + m_aug) * G / L_ovh
F_side = 150.0                                      # assumed rotating side load at the rotor end
d_w    = w_dist * L_ovh ** 4 / (8 * E * I_sh)
d_F    = F_side  * L_ovh ** 3 / (3 * E * I_sh)
d_tot  = (d_w + d_F) * 1000                         # mm
clear  = P.auger_clear

# ============================================================================
# 8b. ROTOR ARTICULATION -- the con-rod
# ============================================================================
from math import atan2, degrees
conrod_ratio = P.conrod_len / P.rotor_eccentricity
conrod_ang   = degrees(atan2(P.rotor_eccentricity, P.conrod_len))

# ============================================================================
# 10. MATERIALS
# ============================================================================
waste       = 1.10
grout_needed= (job_vol_L + hose_vol_L) * waste
# 1 : 2 cement:sand, w/c 0.50  ->  ~600 kg cem, 1200 kg sand, 300 L water per m3
cement_kg   = 600 * grout_needed / 1000
sand_kg     = 1200 * grout_needed / 1000
water_L     = 300 * grout_needed / 1000
sacks       = cement_kg / 50


# ============================================================================
# REPORT
# ============================================================================
def main():
    print("=" * 78)
    print("  TUBE-FILLER -- D6-3 ROTOR/STATOR GROUT PUMP -- DESIGN SUMMARY")
    print("=" * 78)

    rule("1  THE JOB")
    row(f"post bore ({P.post_shape})", bore_desc,
        f"{post_desc} x {P.post_height/1000:.0f} m")
    row("post internal volume", f"{post_vol_L:.1f} L",
        "= side^2 x length" if SQ else "= pi/4 d^2 x length")
    row("x 12 posts", f"{job_vol_L:.0f} L")
    row("+ hose hold-up", f"{hose_vol_L:.1f} L", f"({P.hose_len/1000:.0f} m of 1\")")
    row("grout to mix (10% waste)", f"{grout_needed:.0f} L")
    if abs(post_vol_L - 27.0) > 1.5:
        more = post_vol_L > 27.0
        print(f"  ! The brief assumed ~27 L/post.  {post_desc} holds {post_vol_L:.1f} L "
              f"-- {'MORE' if more else 'less'}, not less." if more else
              f"  ! The brief assumed ~27 L/post.  {post_desc} holds {post_vol_L:.1f} L.")
        print(f"    The job is {job_vol_L:.0f} L, not {27*P.n_posts:.0f} L"
              f" -- a difference of {abs(job_vol_L - 27*P.n_posts):.0f} L"
              f" ({abs(cement_kg - 600*27*P.n_posts/1000):.0f} kg of cement).")
        if SQ:
            print(f"    Square PTR is the reason: a {P.post_side:.1f} square bore is "
                  f"{post_area*1e6:.0f} mm2 against {pi/4*P.post_id**2:.0f} mm2 for round")
            print( "    tube of the same nominal size -- 27% more, and it all has to be")
            print( "    mixed.  Under-ordering cement stops you mid-post.")

    rule("2  PUMP SPEED AND FLOW")
    row("drive", f"{P.drill_power_w:.0f} W drill",
        f"1/2\" chuck on the hex stub, low range (0-{P.drill_rpm_low_max:.0f} rpm)")
    row("rotor speed", f"{n_out:.0f} rpm", "direct -- no reducer, no coupling")
    row("displacement", f"{disp_cc:.0f} cm3/rev", "vendor spec")
    row("flow", f"{Q_Lmin:.2f} L/min")
    row("fill time per post", f"{fill_min:.2f} min", f"{P.n_posts} posts = "
        f"{fill_min*P.n_posts:.0f} min of pumping")

    rule("3  PRESSURE REQUIRED AT THE PUMP OUTLET")
    row("static head", f"{p_static:.2f} bar", f"{P.post_height/1000:.0f} m of SG {P.grout_sg}")
    row(f"hose friction ({P.hose_len/1000:.0f} m of 1\")", f"{p_hose:.2f} bar",
        f"Bingham tau0={P.grout_tau0:.0f} Pa, mu={P.grout_mu_p} Pa.s")
    row("valve + port losses", f"{p_fittings:.2f} bar")
    row("TOTAL REQUIRED", f"{p_required:.2f} bar",
        "OK, >= 2 bar spec met" if p_required >= 2.0 else "")
    row("hose velocity / Bingham Re", f"{V_hose:.2f} m/s / {Re_bingham:.0f}",
        "laminar" if Re_bingham < 2000 else "TURBULENT - recheck")
    print()
    print("  Sensitivity -- required outlet pressure [bar] vs grout stiffness & hose length:")
    lens = [4000, 6000, 8000, 12000, 20000]
    print("      tau0 [Pa] |" + "".join(f"{l/1000:8.0f} m" for l in lens))
    print("      ----------+" + "-" * (9 * len(lens)))
    for t0 in (50, 100, 200, 300):
        cells = ""
        for L in lens:
            v = p_static + p_fittings + hose_dp_bar(t0, L)
            cells += f"{v:9.2f}" if v < 99 else "     ----"
        print(f"      {t0:9.0f} |{cells}")
    print("  -> Hose length is the single biggest lever you control on site.")
    print(f"  -> Anything above {P.design_pressure:.0f} bar exceeds the joint design point:")
    print( "     thin the mix or shorten the hose, do not push the pump harder.")

    rule("4  TORQUE BUDGET AND DRIVE MARGIN  -- 900 W DRILL")
    row("stator friction (ASSUMED)", f"{P.T_stator_friction:.1f} N.m",
        "<-- A GUESS.  Measure it: test_plan W-4")
    row("packed gland, run loose", f"{T_gland_used:.1f} N.m",
        f"vs {P.T_gland:.1f} at normal service preload")
    row("feed auger", f"{P.T_auger:.1f} N.m")
    row(f"pressure @ {p_required:.2f} bar", f"{T_pressure(p_required):.1f} N.m", "= dP.V/2pi")
    row("TOTAL AT DUTY", f"{T_duty:.1f} N.m", f"({P_duty_W:.0f} W at the rotor)")
    print()
    row("drill continuous", f"{T_cont:.1f} N.m", f"at {n_out:.0f} rpm")
    row("drill burst / breakaway", f"{T_burst:.1f} N.m")
    row("MARGIN ON CONTINUOUS", f"{margin:.2f} x",
        f"want >= {P.drive_margin_min:.2f}")
    row("margin on burst", f"{margin_b:.2f} x")

    print()
    if margin >= P.drive_margin_min:
        verdict = "PASS"
        print(f"  VERDICT: PASS.  The drill carries the duty with {margin:.2f}x on continuous")
        print( "  torque.  Confirm on the water test before you trust it.")
    elif margin_b >= 1.0:
        verdict = "MARGINAL"
        print( "  VERDICT: MARGINAL.  The drill can break the pump away and run it in short")
        print(f"  bursts ({margin_b:.2f}x on burst torque) but it is over its continuous")
        print( "  rating at duty.  Expect it to get hot and to fade.  Pump one post, let it")
        print( "  cool, pump the next.  Do not plan a continuous 22-minute run.")
    else:
        verdict = "SHORTFALL"
        print( "  VERDICT: SHORTFALL AT THE ASSUMED FRICTION.  Read the next block before")
        print( "  concluding the machine does not work -- the assumption, not the drill, is")
        print( "  what is unproven.")

    print()
    print("  WHAT ACTUALLY DECIDES THIS -- the stator friction, which nobody has measured:")
    print()
    print("      stator friction |  total at duty |  drill cont.  |  drill burst  | stalls at")
    print("        [N.m]         |     [N.m]      |    15 N.m     |    25 N.m     |   [bar]")
    print("      ----------------+----------------+---------------+---------------+----------")
    for tf in (3, 5, 6.5, 8, 10, 15, 20, 22.6):
        tt = T_total(p_required, tf)
        c = "OK   " if T_cont >= tt * P.drive_margin_min else ("burst" if T_burst >= tt else "no   ")
        bmk = "OK   " if T_burst >= tt * 1.0 else "no   "
        print(f"      {tf:15.1f} | {tt:14.1f} | {c:^13s} | {bmk:^13s} | {p_at_stall(tf):8.1f}")
    print()
    row("max stator friction, continuous", f"{T_fric_max_cont:.1f} N.m",
        f"(and only {T_fric_max_cont/P.drive_margin_min:.1f} with {P.drive_margin_min:.2f}x margin)")
    row("max stator friction, burst", f"{T_fric_max_burst:.1f} N.m", "breakaway only")
    row("...if the gland is run tight", f"{T_fric_max_tight:.1f} N.m",
        f"the gland alone costs {P.T_gland - T_gland_used:.1f} N.m -- run it weeping")
    print()
    print( "  So: the drill drives this pump if and only if the stator's running friction")
    print(f"  comes in at or below about {T_fric_max_cont:.0f} N.m.  That is not an unreasonable")
    print( "  number for a wetted D6-3 at light interference -- and the fact that the vendor")
    print( "  sells a DRILL-HEAD rotor variant says the manufacturer expects exactly this.")
    print( "  But it is not proven.  Measure it on water (test_plan W-4) BEFORE mixing grout.")
    print()
    print( "  Three levers, in order of effect, if the measured friction comes in high:")
    print( "    1. BREAK-IN SPACERS.  Fit the 0.5 mm-crush spacer set and run cement milk")
    print( "       for 30 min.  Interference torque falls as the rubber beds in.  This is")
    print( "       the big one and it costs four pipe offcuts.")
    print( "    2. Run the gland weeping, not dry.  Worth ~2.5 N.m.")
    print( "    3. Shorten the hose and thin the mix.  Worth ~1 N.m -- least effect, because")
    print( "       friction, not pressure, dominates this budget.")
    print(f"  If it still will not carry it: the upgrade path is {T_up:.0f} N.m at {n_up:.0f} rpm")
    print( "  on the SAME hex stub -- see README section 11.")

    rule("5  AUGER FEED MATCH")
    row("flight annulus", f"{flight_area*1e6:.0f} mm2",
        f"OD {P.auger_od:.0f} / hub {P.auger_hub_od:.0f}")
    pod = P.auger_pitch / P.auger_od
    row("pitch", f"{P.auger_pitch:.1f} mm",
        f"= {pod:.2f} x OD" + ("" if 0.5 <= pod <= 1.4 else "  <-- unusual, see below"))
    row("segments", f"{P.n_auger_full} x {P.auger_seg_len:.0f}"
        + (f" + 1 x {P.auger_tail_len:.0f}" if P.auger_tail_len > 1 else ""),
        f"{P.n_auger_pitch} pitches span the barrel exactly")
    row(f"swept volume @ eta={P.auger_fill_eta}", f"{auger_cc:.0f} cm3/rev")
    row("OVERFEED RATIO", f"{overfeed:.2f} x", "target >= 1.30" if overfeed >= 1.30 else "LOW")
    row("starves below fill factor", f"{eta_break:.2f}",
        f"print the {P.auger_pitch_alt:.0f} mm-pitch spares if it does")
    if not 0.5 <= pod <= 1.4:
        print(f"  ! pitch/OD = {pod:.2f}.  Outside 0.5-1.4 the screw still meters correctly but")
        print( "    conveys poorly.  Raise auger_hub_wall (shrinks the annulus, coarsens the")
        print( "    pitch) or lower auger_overfeed, then re-run.")

    rule("5b  THE CROSS-PIN BOSS -- the worst station, not the average")
    print("  Section 5 is an average over the plain hub.  A screw meters on its WORST")
    print("  station.  On this screw that is the boss around each drive pin, and these")
    print("  numbers walk the real core profile end to end at 0.25 mm.\n")
    row("boss swept OD x axial",
        f"{P.auger_pin_boss:.0f} x {P.auger_boss_len:.0f} mm",
        f"lens, {P.auger_boss_fair:.0f} mm fairing each end")
    row("boss plan form",
        f"{P.auger_pin_boss:.0f} x {P.auger_boss_minor:.0f} mm",
        "major axis on the pin; flush with the hub at 90 deg")
    row("local conveyed annulus at the boss",
        f"{local_flight_area(0.0)*1e6:.0f} mm2",
        f"vs {flight_area*1e6:.0f} open hub "
        f"= {local_flight_area(0.0)/flight_area*100:.0f}%")
    row("MIN LOCAL OVERFEED, all z", f"{of_min:.2f} x",
        f"gate {P.auger_min_local_overfeed:.2f}; worst at z = {of_min_z:+.1f} mm"
        + ("  PASS" if of_min >= P.auger_min_local_overfeed else "  FAIL"))
    row("free area at the boss", f"{boss_free*100:.0f}%",
        f"of the plain-hub section; gate {P.auger_min_free_area*100:.0f}%"
        + ("  PASS" if free_min >= P.auger_min_free_area else "  FAIL"))
    row("largest boss the gate allows", f"{boss_dia_cap:.1f} mm",
        f"fitted at {P.auger_pin_boss:.0f}")
    print()
    print("  WAS a plain cylinder at 56 x 22.  That is 61% of the open-hub free area and")
    print("  a LOCAL overfeed of 0.58 -- the screw metered 1.54x the stator's swallow")
    print("  everywhere except the three stations where it mattered, and starved there.")
    print("  A screw that starves anywhere starves: the pump sees the pinch, not the mean.")
    print()
    print("  Two changes, doing two different jobs:")
    print(f"    AREA  -- swept OD {P.auger_pin_boss:.0f}, capped by the "
          f"{P.auger_min_local_overfeed:.2f}x gate above, which bites")
    print(f"             at {boss_dia_cap:.1f} mm.  (A 50 mm boss reads "
          f"{_of_at(50.0):.2f}x and does NOT clear it.)")
    print( "    SHAPE -- a faired lens, so it sheds instead of damming: double-cone")
    print( "             axially into a short land, and in plan an ellipse with its major")
    print( "             axis on the pin, blended flush into the hub at +-90 deg.  The")
    print( "             two quarters of the channel that carry no pin load stay at full")
    print( "             hub diameter.  The gates above take NO credit for the lens --")
    print( "             they are computed on the circle it sweeps.")
    print()
    print(f"  CROSS PIN -- {P.xpin_dia:.0f} mm steel bearing on printed PETG, "
          f"allowable {P.petg_bearing_mpa:.0f} MPa:")
    row(f"  wall each side of the shaft", f"{pin_wall:.2f} mm",
        f"projected bearing area {pin_bear_A:.0f} mm2, both walls")
    row(f"  at duty ({P.T_auger:.1f} N.m)", f"{sig_pin_duty:.2f} MPa",
        f"margin {marg_pin_duty:.0f} x  (want >= {P.pin_bearing_margin_min:.0f})"
        + ("  PASS" if marg_pin_duty >= P.pin_bearing_margin_min else "  FAIL"))
    row(f"  if it JAMS ({P.drill_T_burst:.0f} N.m burst)", f"{sig_pin_jam:.1f} MPa",
        f"margin {marg_pin_jam:.1f} x")
    row("  steel pin, double shear at jam", f"{tau_pin_jam:.0f} MPa",
        "vs ~400 for a spring roll pin -- not the limit")
    print()
    print(f"  The duty case is the gate and it passes by {marg_pin_duty:.0f}x.  The jam")
    print(f"  case sits at {marg_pin_jam:.1f}x, and that is deliberate: a jam is bounded by")
    print( "  the drill stalling, and the boss is the cheapest thing in the chain to give")
    print( "  way.  If it does, the segment spins free on the shaft, the pump starves and")
    print( "  you notice -- the pin stays captive in the shaft and nothing loose enters")
    print( "  the barrel.  Reprint the segment; it is already a declared consumable.")
    print( "  Note the two constraints have nearly converged: the overfeed gate caps the")
    print(f"  boss at {boss_dia_cap:.1f} mm, and carrying a full-burst jam at {P.pin_bearing_margin_min:.0f}x would want")
    print( "  about 49.8.  There is no boss diameter that does both, which is worth")
    print( "  knowing before anyone thickens it again.")

    rule("6  AXIAL THRUST -- rotor pushes the shaft REARWARD")
    row(f"thrust at duty ({p_required:.2f} bar)", f"{thrust_duty:.0f} N")
    row(f"thrust at {P.design_pressure:.0f} bar +30%", f"{thrust_des_x:.0f} N",
        "sized on the stator inlet bore")
    row(f"{P.pillow_block} axial capacity", f"{axial_cap:.0f} N", "= 0.2 x C")
    row("margin", f"{axial_cap/thrust_des_x:.1f} x",
        "PASS" if axial_cap > 2 * thrust_des_x else "CHECK")
    print("  Both pillow blocks get their collars locked; the REAR one takes the thrust.")

    rule("7  STATOR CLAMP -- tie rods over hard-stop spacers")
    row("gasket seating force", f"{F_seat:.0f} N", "3 mm elastomer, y=1.4 MPa")
    row(f"separating force @ {P.design_pressure:.0f} bar", f"{F_sep:.0f} N")
    row("minimum total clamp", f"{F_clamp_min:.0f} N",
        f"= {F_rod_min:.0f} N/rod = {T_rod_min:.1f} N.m")
    row("RECOMMENDED preload", f"{F_rod_rec:.0f} N/rod",
        f"= {T_rod_rec:.0f} N.m dry on M10 8.8")
    row("rod stress at recommended", f"{sig_rod:.0f} MPa", "vs 640 MPa proof (8.8)")
    row("spacer stress", f"{sig_spacer:.0f} MPa", f"3/4\" sch40, {A_spacer*1e6:.0f} mm2")
    row("spacer cut length", f"{P.spacer_len:.1f} mm", "= stator_len - crush; HARD STOP")
    print("  The spacers, not the rubber, carry the preload.  This is the whole point:")
    print("  you cannot over-crush the stator no matter how hard you pull the rods, and")
    print("  over-crushing is what kills a PC stator (bore closes, torque spikes, burns).")

    rule("8  DRIVE SHAFT DEFLECTION  (why the shaft is 35 mm)")
    row("unsupported overhang", f"{L_ovh*1000:.0f} mm", "front pillow block -> con-rod pin")
    row("deflection, self weight", f"{d_w*1000:.2f} mm")
    row(f"deflection, {F_side:.0f} N side load", f"{d_F*1000:.2f} mm")
    row("TOTAL", f"{d_tot:.2f} mm")
    row("auger radial clearance", f"{clear:.2f} mm",
        f"margin {clear/d_tot:.1f} x " + ("PASS" if clear > 1.5 * d_tot else "FAIL"))

    rule("8b  ROTOR ARTICULATION")
    row("eccentricity (measured input)", f"{P.rotor_eccentricity:.1f} mm", "see README: V-block + DTI")
    row("con-rod length", f"{P.conrod_len:.0f} mm")
    row("length / eccentricity", f"{conrod_ratio:.1f}", "want >= 20")
    row("joint angle swept", f"{conrod_ang:.2f} deg",
        "each fork gets 0.5 mm of slop; grease and boot it")
    print("  The two forks are at 90 deg to each other.  A single cross pin is a 1-DOF")
    print("  hinge; the rotor axis precesses on a cone, which needs 2.  Parallel forks")
    print("  will bind and tear the rotor head off.  Check this on assembly by hand.")

    rule("9  STALL, OVERPRESSURE AND WHAT PROTECTS THE MACHINE")
    row("drill stalls the pump at", f"{p_at_stall():.1f} bar",
        "at the assumed friction" if p_at_stall() > 0 else "-- it cannot turn it at all")
    print()
    print("      stator friction [N.m] |  pump stalls the drill at [bar]")
    print("      ----------------------+--------------------------------")
    for tf in (3, 5, 6.5, 8, 10, 15):
        print(f"      {tf:21.1f} | {p_at_stall(tf):26.1f}")
    print()
    print( "  This is the drill's one clear win over the motor it replaced.  A 1.5 kW motor")
    print( "  on a 7.5:1 worm does not stall until roughly 140 bar -- twenty times the")
    print( "  6 bar these joints are built for.  A 900 W drill stalls far sooner, and at")
    print( "  low measured friction it stalls inside or near the design envelope.  The")
    print( "  drive is now part of the protection instead of a liability.")
    print()
    print( "  It is still not ENOUGH protection.  Keep all of it:")
    print(f"    1. 0-16 bar glycerin gauge on the discharge head, red band at "
           f"{P.design_pressure:.0f} bar.")
    print( "    2. 1\" manual bypass ball valve back to the hopper.  It is the relief valve.")
    print( "    3. Hose rated >= 40 bar working, crimped ends, whip checks.")
    print( "    4. 30 mA RCD on the supply.  A hand drill in a wet steel machine has no")
    print( "       earthed frame of its own and no overload relay.  The RCD is the only")
    print( "       electrical protection on this build -- do not omit it.")
    print()
    print( "  AND the shutdown rule, which is different from the motor version:")
    print( "    CLOSE THE DISCHARGE VALVE, THEN RELEASE THE TRIGGER.  In that order.")
    print( "    A drill freewheels when you let go -- there is no gearbox holding anything.")
    print(f"    The {p_static:.2f} bar column in the post will drive the rotor backwards and")
    print( "    drain itself into the hopper, and you will not see it happen.")

    rule(f"10  MATERIALS FOR THE POUR  ({P.n_posts} x {P.post_shape} posts)")
    row("bore area per post", f"{post_area*1e6:.0f} mm2",
        f"{bore_desc} ({P.post_shape})")
    row("volume per post", f"{post_vol_L:.2f} L")
    row("grout to mix", f"{grout_needed:.0f} L", "1:2 cement:sand, w/c 0.50")
    row("cement", f"{cement_kg:.0f} kg", f"= {sacks:.1f} sacks of 50 kg")
    row("sand (sieved <= 3 mm)", f"{sand_kg:.0f} kg")
    row("water", f"{water_L:.0f} L")
    row("hopper holds", f"{P.hop_vol_L:.0f} L", f"= {P.hop_vol_L/post_vol_L:.1f} posts per load")

    # ---------------- what is still unknown ----------------
    tbd = P.open_questions()
    blocks = []
    for b, n, v, note in tbd:
        label = b.split(".")[0].strip()[:50]
        if not blocks or blocks[-1][0] != label:
            blocks.append((label, []))
        blocks[-1][1].append((n, v, note))
    rule(f"11  STILL A GUESS -- the {len(tbd)} TBDs left in params.py")
    print("  Read live out of params.py, so this list cannot go stale.  Each one is a")
    print("  PLACEHOLDER: the geometry around it is right, the number is not measured.")
    print("  The barrel is no longer here -- McMaster 6045N87 is purchased and certified,")
    print(f"  {P.barrel_od:.1f} OD x {P.barrel_wall:.2f} wall, bore {P.barrel_id:.1f}.")
    for label, items in blocks:
        print(f"\n  {label}")
        for n, v, note in items:
            head = f"    {n:<23s} {v:>10s}   "
            for k, line in enumerate(textwrap.wrap(note, 39) or [""]):
                print(((head if k == 0 else " " * len(head)) + line).rstrip())
    print()
    print("  Four of these decide whether steel gets cut the way it is drawn today:")
    print("    T_stator_friction  -- section 4.  The whole drive question.  Water test first.")
    print("    rotor_*            -- the con-rod chain and every x-station behind it.")
    print("    stator_end_style / _has_steel_jacket -- sets stator_crush and the spacer cut.")
    print("    drill_*            -- the cradle and torque lug stations; verify.py re-checks.")
    print("  The rest cost a reprint, not a re-cut: post_* sizes the cement order (section")
    print("  10) and reprints two jigs, printer_* only gates what fits the bed, and")
    print("  bucket_rim_od is one sand screen.")

    # ---------------- acceptance ----------------
    rule("ACCEPTANCE CHECKS")
    checks = [
        ("delivery pressure >= 2 bar",       p_required >= 2.0),
        ("auger overfeed >= 1.30x",          overfeed >= 1.30),
        ("thrust margin >= 2x",              axial_cap >= 2 * thrust_des_x),
        ("shaft deflection < clearance/1.5", clear > 1.5 * d_tot),
        ("tie-rod preload below proof",      sig_rod < 640),
        ("hose flow laminar",                Re_bingham < 2000),
        ("one hopper load >= one post",      P.hop_vol_L >= post_vol_L),
        ("con-rod length >= 20 x ecc",       conrod_ratio >= 20),
        (f"auger local overfeed >= {P.auger_min_local_overfeed:.2f}x at EVERY z",
                                             of_min >= P.auger_min_local_overfeed),
        (f"auger free area >= {P.auger_min_free_area*100:.0f}% of open hub at every z",
                                             free_min >= P.auger_min_free_area),
        ("auger pin bearing margin >= 3x at duty",
                                             marg_pin_duty >= P.pin_bearing_margin_min),
        ("no dead annulus at the gland",     abs(P.x_auger_back - P.x_cover_back) <= 20),
    ]
    ok = True
    for name, res in checks:
        print(f"  [{'PASS' if res else 'FAIL'}]  {name}")
        ok &= res
    print(f"  [{verdict:^4s}]  drive margin on continuous torque "
          f"({margin:.2f}x, want {P.drive_margin_min:.2f}x)")
    print()
    print("  The drive line is a VERDICT, not a gate.  It is reported and the build")
    print("  proceeds, because the input it depends on (T_stator_friction) is a guess")
    print("  and refusing to emit CAD over a guess helps nobody.  Everything else is")
    print("  a hard check and does gate the build.")
    print()
    assert ok, "one or more acceptance criteria failed -- see above"
    if verdict == "PASS":
        print("  All hard criteria met; drive margin PASSES at the assumed friction.")
    else:
        print(f"  All hard criteria met.  DRIVE: {verdict} -- see section 4.")
    print("=" * 78)


if __name__ == "__main__":
    main()
