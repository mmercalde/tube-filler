"""Frame weldment drawing.

Members are defined once, in 3D machine coordinates, and projected into three
orthographic views.  The cut list is generated from the same list, so the
drawing and the BOM can never disagree.

Machine coordinates (mm):
    x  along the barrel.  x = 0 is the FRONT FACE of the adapter plate.
       Forward (toward the discharge) is +x.
    y  across.  +y = operator's side (right, looking forward), -y = motor side.
    z  up from the ground.
"""
import os
from _common import P, ROOT, OUT

PTR = P.ptr_size
SKID_F = 150.0
SKID_R = SKID_F - P.skid_len
RAIL_Y = P.skid_w / 2 - PTR / 2
TOP_Z = P.barrel_cl_h - P.barrel_od / 2 - PTR          # top rail underside
# printed saddle wall + steel cradle plate sit between the upright and the drill
DRILL_TOP = (P.barrel_cl_h - P.drill_body_dia / 2 - P.cradle_wall
             - P.cradle_foot_t - P.cradle_plate_t)
LEG_X = (100.0, -450.0, -1050.0)
XM = tuple(sorted((134.0, -50.0, -450.0, -800.0, -1050.0, SKID_R + 30)))

# name, stock, (x0,y0,z0), (x1,y1,z1)
MEMBERS = []
def M(name, stock, a, b):
    MEMBERS.append((name, stock, a, b))

PT = f"PTR {PTR:.0f}x{PTR:.0f}x{P.ptr_wall:.2f}".replace(".05", "")
for s in (+1, -1):
    M("skid rail", PT, (SKID_R, s * RAIL_Y, PTR / 2), (SKID_F, s * RAIL_Y, PTR / 2))
    M("top rail", PT, (SKID_R + 150, s * RAIL_Y, TOP_Z + PTR / 2), (SKID_F, s * RAIL_Y, TOP_Z + PTR / 2))
for x in XM:
    M("skid cross", PT, (x, -RAIL_Y, PTR / 2), (x, RAIL_Y, PTR / 2))
for x in (XM[1], XM[3], XM[5]):
    M("top cross", PT, (x, -RAIL_Y, TOP_Z + PTR / 2), (x, RAIL_Y, TOP_Z + PTR / 2))
for x in LEG_X:
    for s in (+1, -1):
        M("leg", PT, (x, s * RAIL_Y, PTR), (x, s * RAIL_Y, TOP_Z))
for x, dx in ((-450.0, +250.0), (-1050.0, +250.0)):
    for s in (+1, -1):
        M("knee brace", PT, (x, s * RAIL_Y, PTR), (x + dx, s * RAIL_Y, TOP_Z))

# ----- DRILL DRIVE STATION -------------------------------------------------
# The drill is captured, not held.  Reaction torque goes:
#   drill aux-handle collar -> STEEL torque lug -> STEEL upright -> braces -> skid.
# The printed saddle only holds the drill down and locates it.  It is never in
# the torque path.
M("drill rail", PT, (XM[0], 0, PTR / 2), (-1050.0, 0, PTR / 2))
M("drill upright", PT, (P.x_drill_upright, 0, PTR), (P.x_drill_upright, 0, DRILL_TOP))
M("cradle outrigger", PT, (P.x_drill_upright, 0, DRILL_TOP - PTR / 2),
  (P.x_drill_upright - P.cradle_plate_l, 0, DRILL_TOP - PTR / 2))
for s in (+1, -1):
    M("drill brace", PT, (P.x_drill_upright, s * RAIL_Y, PTR),
      (P.x_drill_upright, 0, DRILL_TOP))

def cut_list():
    from math import dist
    agg = {}
    for name, stock, a, b in MEMBERS:
        L = round(dist(a, b))
        key = (name, stock, L)
        agg[key] = agg.get(key, 0) + 1
    rows = sorted(agg.items(), key=lambda kv: (-kv[0][2], kv[0][0]))
    return [(n, s, L, q) for (n, s, L), q in rows]


# --------------------------------------------------------------------- SVG
class Sheet:
    def __init__(self, w=1600, h=1150):
        self.w, self.h, self.o = w, h, []
    def add(self, s): self.o.append(s)
    def line(self, x1, y1, x2, y2, cls="thin"):
        self.add(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" class="{cls}"/>')
    def rect(self, x, y, w, h, cls="thick"):
        self.add(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" class="{cls}"/>')
    def text(self, x, y, t, cls="t", anchor="start"):
        t = t.replace("&", "&amp;").replace("<", "&lt;")
        self.add(f'<text x="{x:.1f}" y="{y:.1f}" class="{cls}" text-anchor="{anchor}">{t}</text>')
    def dim(self, x1, y1, x2, y2, label, off=0):
        self.line(x1, y1, x2, y2, "dim")
        for xx, yy in ((x1, y1), (x2, y2)):
            self.line(xx - 3, yy - 3, xx + 3, yy + 3, "dim")
        mx, my = (x1 + x2) / 2, (y1 + y2) / 2
        if abs(y2 - y1) < 1:
            self.text(mx, my - 4, label, "d", "middle")
        else:
            self.add(f'<text x="{mx-4:.1f}" y="{my:.1f}" class="d" text-anchor="middle" '
                     f'transform="rotate(-90 {mx-4:.1f} {my:.1f})">{label}</text>')
    def save(self, path):
        css = ("text{font-family:monospace}.t{font-size:13px}.h{font-size:20px;font-weight:bold}"
               ".s{font-size:15px;font-weight:bold}.d{font-size:11px;fill:#0a5}"
               ".thick{fill:none;stroke:#000;stroke-width:1.6}"
               ".thin{fill:none;stroke:#000;stroke-width:0.7}"
               ".dim{fill:none;stroke:#0a5;stroke-width:0.6}"
               ".ghost{fill:none;stroke:#888;stroke-width:0.7;stroke-dasharray:6 3}"
               ".ctr{fill:none;stroke:#c00;stroke-width:0.6;stroke-dasharray:12 3 2 3}")
        body = "\n".join(self.o)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}"><style>{css}</style>'
               f'<rect width="{self.w}" height="{self.h}" fill="#fff"/>{body}</svg>')
        open(path, "w").write(svg)
        return path


STATIONS = [
    (268.0, "stator front / discharge head"),
    (0.0, "adapter plate face -- DATUM"),
    (-610.0, "barrel rear + bolted cover"),
    (-800.0, "pillow block 1"),
    (-920.0, "pillow block 2"),
    (P.x_shaft_rear, "shaft rear / hex stub"),
    (P.x_hex_back, "hex stub free end -- CHUCK HERE"),
    (P.x_torque_lug, "steel torque lug"),
    (P.x_drill_cradle, "printed drill saddle"),
]


def draw(scale=0.30):
    S = Sheet(1740, 1440)
    S.text(30, 36, "TUBE-FILLER  --  FRAME WELDMENT", "h")
    S.text(30, 58, f"All members PTR {PTR:.0f} x {PTR:.0f} x {P.ptr_wall:.2f} "
                   f"(2\" square, cal-11).  Dimensions in mm.  BUILD TO THE NUMBERS, NOT THE PICTURE.", "t")
    S.text(30, 76, "Machine datum x=0 is the FRONT FACE of the adapter plate.  +x is toward the "
                   "discharge.  z is up from the ground.  NO MOTOR: a 1/2\" paddle drill "
                   "chucks onto the hex stub at x={:.0f}.".format(P.x_hex_back), "t")
    S.line(30, 88, S.w - 30, 88)

    def member(a, b, tx, ty, cls="thick", pt=False):
        x1, y1, x2, y2 = tx(a[0]), ty(a[1]), tx(b[0]), ty(b[1])
        if abs(x1 - x2) < 0.5 and abs(y1 - y2) < 0.5:
            if pt:
                S.rect(x1 - PTR * scale / 2, y1 - PTR * scale / 2,
                       PTR * scale, PTR * scale, cls)
            return
        dx, dy = x2 - x1, y2 - y1
        L = max((dx * dx + dy * dy) ** .5, 1e-6)
        nx, ny = -dy / L * PTR * scale / 2, dx / L * PTR * scale / 2
        S.add(f'<polygon points="{x1+nx:.1f},{y1+ny:.1f} {x2+nx:.1f},{y2+ny:.1f} '
              f'{x2-nx:.1f},{y2-ny:.1f} {x1-nx:.1f},{y1-ny:.1f}" class="{cls}"/>')

    # ================= VIEW A -- SIDE ELEVATION =================
    ox, oz = 70, 610
    sx = lambda x: ox + (x - SKID_R) * scale
    sz = lambda z: oz - z * scale
    S.text(ox, 116, "VIEW A  --  SIDE ELEVATION   (near frame + centreline drill station)", "s")
    for name, stock, a, b in MEMBERS:
        near = abs(a[1] - RAIL_Y) < 1 and abs(b[1] - RAIL_Y) < 1
        centre = abs(a[1]) < 1 and abs(b[1]) < 1
        if not (near or centre):
            continue
        member((a[0], a[2]), (b[0], b[2]), sx, sz, "thick" if near else "thin")
    for x0, x1, lbl in ((-610, -10, "BARREL 600"), (0, 268, "STATOR 270"), (268, 360, "DISCH")):
        S.rect(sx(x0), sz(P.barrel_cl_h) - P.barrel_od / 2 * scale,
               (x1 - x0) * scale, P.barrel_od * scale, "ghost")
        S.text((sx(x0) + sx(x1)) / 2, sz(P.barrel_cl_h) + 4, lbl, "d", "middle")
    S.rect(sx(-715), sz(P.barrel_cl_h + P.barrel_od / 2 + 20 + P.hop_depth),
           P.hop_top_l * scale, P.hop_depth * scale, "ghost")
    S.text(sx(-455), sz(P.barrel_cl_h + 260), f"HOPPER {P.hop_vol_L:.0f} L", "d", "middle")
    S.line(sx(SKID_R) - 40, sz(P.barrel_cl_h), sx(420), sz(P.barrel_cl_h), "ctr")
    S.text(sx(420) + 6, sz(P.barrel_cl_h) + 4, "barrel CL", "d")
    S.line(sx(SKID_R) - 40, sz(0), sx(SKID_F) + 90, sz(0), "thin")
    # station ticks along the datum
    prev = SKID_R
    for x in XM:
        S.dim(sx(prev), sz(0) + 22, sx(x), sz(0) + 22, f"{x-prev:.0f}")
        prev = x
    S.dim(sx(SKID_R), sz(0) + 48, sx(SKID_F), sz(0) + 48, f"{SKID_F-SKID_R:.0f}  SKID")
    for x, lbl in sorted(STATIONS):
        S.line(sx(x), sz(P.barrel_cl_h) + 14, sx(x), sz(0) + 68, "ghost")
        px_, py_ = sx(x) + 4, sz(0) + 74
        S.add(f'<text x="{px_:.1f}" y="{py_:.1f}" class="d" text-anchor="start" '
              f'transform="rotate(90 {px_:.1f} {py_:.1f})">x={x:.0f}   {lbl}</text>')
    S.dim(sx(SKID_R) - 24, sz(0), sx(SKID_R) - 24, sz(TOP_Z), f"{TOP_Z:.0f} top rail")
    S.dim(sx(SKID_R) - 52, sz(0), sx(SKID_R) - 52, sz(P.barrel_cl_h), f"{P.barrel_cl_h:.0f} barrel CL")

    # ================= VIEW C -- END ELEVATION =================
    ex, ez = 1420, 610
    ey = lambda y: ex - y * scale
    ezf = lambda z: ez - z * scale
    S.text(ex - 200, 116, "VIEW C  --  END ELEVATION (looking forward)", "s")
    for name, stock, a, b in MEMBERS:
        member((a[1], a[2]), (b[1], b[2]), ey, ezf, "thin", pt=True)
    S.add(f'<circle cx="{ey(0):.1f}" cy="{ezf(P.barrel_cl_h):.1f}" '
          f'r="{P.barrel_od/2*scale:.1f}" class="thick"/>')
    S.rect(ey(P.hop_top_w / 2), ezf(P.barrel_cl_h + 58 + P.hop_depth),
           P.hop_top_w * scale, P.hop_depth * scale, "ghost")
    S.line(ey(0), ezf(-60), ey(0), ezf(P.barrel_cl_h + 560), "ctr")
    S.line(ey(-560), ezf(0), ey(560), ezf(0), "thin")
    S.dim(ey(-RAIL_Y), ezf(0) + 22, ey(RAIL_Y), ezf(0) + 22, f"{2*RAIL_Y:.0f} rail centres")
    S.dim(ey(RAIL_Y) + 26, ezf(0), ey(RAIL_Y) + 26, ezf(P.barrel_cl_h), f"{P.barrel_cl_h:.0f}")
    S.add(f'<circle cx="{ey(0):.1f}" cy="{ezf(P.barrel_cl_h):.1f}" '
          f'r="{P.drill_body_dia/2*scale:.1f}" class="ghost"/>')
    S.text(ey(0), ezf(P.barrel_cl_h) - P.drill_body_dia / 2 * scale - 8,
           f"drill body {P.drill_body_dia:.0f} dia", "d", "middle")
    S.dim(ey(0) + 34, ezf(PTR), ey(0) + 34, ezf(DRILL_TOP), f"{DRILL_TOP-PTR:.0f} upright")
    S.text(ey(RAIL_Y) - 30, ezf(0) + 42, "Drill braces triangulate the upright:", "d")
    S.text(ey(RAIL_Y) - 30, ezf(0) + 56, "25 N.m on a 21 mm collar = ~1160 N", "d")
    S.text(ey(RAIL_Y) - 30, ezf(0) + 70, "sideways.  Unbraced it sags 2.4 mm.", "d")

    # ================= VIEW B -- PLAN =================
    oy = 1160
    py = lambda y: oy - y * scale
    S.text(ox + 480, 940, "VIEW B  --  PLAN   (skid heavy, top rails light)", "s")
    for name, stock, a, b in MEMBERS:
        if abs(a[0] - b[0]) < 1 and abs(a[1] - b[1]) < 1:
            continue
        cls = "thick" if abs(a[2] - PTR / 2) < 1 else "thin"
        member((a[0], a[1]), (b[0], b[1]), sx, py, cls)
    S.line(sx(SKID_R) - 40, py(0), sx(420), py(0), "ctr")
    S.dim(sx(SKID_R) - 24, py(-RAIL_Y), sx(SKID_R) - 24, py(RAIL_Y), f"{2*RAIL_Y:.0f}")
    S.dim(sx(P.x_drill_cradle), py(-RAIL_Y) + 18, sx(P.x_torque_lug), py(-RAIL_Y) + 18,
          f"{P.x_torque_lug-P.x_drill_cradle:.0f}")
    S.text(sx(SKID_R), py(-RAIL_Y) + 34,
           "NO MOTOR, NO REDUCER, NO COUPLING.  The drill chucks straight onto the hex stub.", "d")
    S.text(sx(SKID_R), py(-RAIL_Y) + 50,
           "Operator stands at +y, one hand on the trigger.  The frame holds the drill.", "d")

    # ================= CUT LIST + NOTES =================
    tx, ty = 1000, 790
    S.text(tx, ty, "CUT LIST   (square cuts unless noted)", "s")
    S.text(tx, ty + 24, f"{'QTY':<5}{'LENGTH':<10}{'MEMBER':<20}{'STOCK'}", "t")
    S.line(tx, ty + 30, tx + 560, ty + 30)
    y, total = ty + 48, 0
    for name, stock, L, q in cut_list():
        S.text(tx, y, f"{q:<5}{L:<10.0f}{name:<20}{stock}", "t")
        total += L * q
        y += 19
    S.line(tx, y - 13, tx + 560, y - 13)
    S.text(tx, y + 4, f"{'':<5}{total/1000:<10.1f}{'TOTAL PTR (m)':<20}"
                      f"+10% = order {total/1000*1.1:.0f} m", "t")
    y += 38
    for n in [
        "WELD NOTES   (3.05 mm wall -- do not chase full penetration)",
        "  1. 4 mm fillet, both sides where you can reach; elsewhere 40 mm stitch at 80 mm pitch.",
        "  2. 7018 at 80-95 A, or 0.030 wire on C25 at ~130 A.  Back the heat off if you blow",
        "     through -- the frame is nowhere near stress-limited and burn-through is the only risk.",
        "  3. Tack the whole skid first.  Check the two diagonals equal within 2 mm.  THEN weld out.",
        "  4. Weld the top rails LAST, with the barrel clamped in its saddles.  The barrel, not the",
        "     frame, is the alignment datum for the whole machine.",
        "  5. Saddles: 2 off, 6 mm plate, R38.1 notch, on the top rails at x = -100 and x = -520.",
        "  6. Pillow-block sub-plate: 10 mm, 4 x M12 in 14 x 40 SLOTS running along x, so the whole",
        "     drive train can be drawn rearward to change the auger.",
        "  7. Lifting eyes: 4 off, 12 mm plate, 30 mm hole, on the top rails above the legs.",
        "  8. DRILL STATION -- one upright, two jobs.  The 10 mm torque lug is welded to",
        "     its FRONT face, half-round to the measured aux-handle collar: that lug is the",
        "     ONLY torque path.  The 10 mm cradle plate cantilevers REARWARD on the",
        "     outrigger and carries the printed saddle, which clamps and nothing else.",
        "     Weld both drill braces.  Unbraced, that upright sags 2.4 mm under the",
        "     1160 N reaction and the drill cocks off the stub axis.",
        "  9. Paint everything.  Mask the clamp-plate faces -- they are gasket faces.",
    ]:
        S.text(tx, y, n, "t")
        y += 18
    return S.save(os.path.join(OUT, "frame_weldment.svg"))
