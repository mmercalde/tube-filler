#!/usr/bin/env python3
"""Regenerate every CAD output from ../params.py.

    python cad/build_all.py

Nothing downstream of params.py is edited by hand.  Change a MEASURED INPUT,
run this, and every plate, STL, DXF and drawing follows.
"""
import os, sys, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from _common import *          # noqa: F401,F403
import plates, printed, conrod, hopper, frame_drawing, verify, manifest

made = []
def note(p):
    made.append(p)
    print(f"  {os.path.relpath(p, ROOT)}")


def main():
    t0 = time.time()
    # out/ is generated, and STL names carry the derived pitch -- stale files
    # from a previous parameter set would otherwise sit there looking valid.
    stale = [f for f in os.listdir(OUT) if not f.startswith(".")]
    for f in stale:
        os.remove(os.path.join(OUT, f))
    if stale:
        print(f"cleared {len(stale)} file(s) from out/\n")

    print("GEOMETRY SELF-CHECKS")
    bad = verify.check()
    for x in bad:
        print("  FAIL  " + x)
    assert not bad, f"{len(bad)} geometry check(s) failed -- nothing exported"
    print("  all pass\n")
    print("STEEL -- plate profiles (DXF = plasma / drill template, STEP = 3D)")
    ap3, ap2 = plates.adapter_plate()
    note(save_dxf("adapter_plate", ap2, plates.adapter_plate_scribe()))
    note(save_step("adapter_plate", ap3))
    dr3, dr2 = plates.discharge_rear_plate()
    note(save_dxf("discharge_rear_plate", dr2))
    dc3, dc2 = plates.discharge_cap()
    note(save_dxf("discharge_cap", dc2))
    note(save_step("discharge_head", plates.discharge_head()))
    bf3, bf2 = plates.barrel_rear_flange()
    note(save_dxf("barrel_rear_flange", bf2))
    bc3, bc2 = plates.barrel_rear_cover()
    note(save_dxf("barrel_rear_cover", bc2))
    gp3, gp2 = plates.gland_plate()
    note(save_dxf("gland_plate", gp2))
    st3, st2 = conrod.shaft_tongue()
    note(save_dxf("shaft_tongue", st2))

    print("STEEL -- weldments (STEP)")
    note(save_step("conrod", conrod.conrod()))
    note(save_step("hex_stub_PRIMARY_INPUT", conrod.hex_stub()))
    note(save_step("drive_shaft", conrod.drive_shaft()))

    print("HOPPER -- flat patterns (cut these, tack, weld the outside)")
    note(save_dxf("hopper_wall_long_x2", hopper.wall_long()))
    note(save_dxf("hopper_wall_short_x2", hopper.wall_short()))
    note(save_dxf("hopper_collar_side_x2", hopper.collar_side()))
    note(save_dxf("hopper_collar_end_x2", hopper.collar_end()))
    tmpl, dev, circ = hopper.barrel_slot_template()
    note(save_dxf("barrel_slot_wrap_template", tmpl))
    print(f"    (slot {P.barrel_slot_l:.0f} x {P.barrel_slot_w:.0f} chord = "
          f"{dev:.1f} mm DEVELOPED; wrap length {circ:.1f} mm)")
    note(save_dxf("hopper_grate", hopper.grate()))

    print("PRINTED -- registry-driven; see out/print_manifest.md")
    rws = manifest.rows()
    for r in rws:
        note(save_stl(r["name"], r["shape"]))
    with open(os.path.join(OUT, "print_manifest.md"), "w") as fh:
        fh.write(manifest.render(rws))
    note(os.path.join(OUT, "print_manifest.md"))
    print(f"    {len(rws)} models, {sum(r['qty'] for r in rws)} parts, "
          f"~{sum(r['mass']*r['qty'] for r in rws)/1000:.1f} kg filament")

    print("DRAWING")
    svg = frame_drawing.draw()
    note(svg)
    # optional raster/PDF of the weldment drawing for the shop wall
    import shutil, subprocess
    chrome = shutil.which("chromium") or shutil.which("google-chrome") or shutil.which("chromium-browser")
    if chrome:
        for flag, ext in (("--screenshot=", "png"), ("--print-to-pdf=", "pdf")):
            dst = os.path.join(OUT, "frame_weldment." + ext)
            try:
                subprocess.run([chrome, "--headless", "--disable-gpu", "--no-sandbox",
                                "--hide-scrollbars", "--window-size=1740,1440",
                                flag + dst, "file://" + svg],
                               capture_output=True, timeout=90)
                if os.path.exists(dst):
                    note(dst)
            except Exception:
                pass
    else:
        print("    (no chromium found -- SVG only; open frame_weldment.svg in a browser)")

    print("DOCS")
    import bom
    with open(os.path.join(ROOT, "BOM.md"), "w") as fh:
        fh.write(bom.render())
    note(os.path.join(ROOT, "BOM.md"))
    import io, contextlib
    sys.path.insert(0, os.path.join(ROOT, "calcs"))
    import pump_calcs
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        pump_calcs.main()
    with open(os.path.join(OUT, "design_summary.txt"), "w") as fh:
        fh.write(buf.getvalue())
    note(os.path.join(OUT, "design_summary.txt"))

    print(f"\n{len(made)} files in {os.path.relpath(OUT, ROOT)}/  ({time.time()-t0:.1f} s)")


if __name__ == "__main__":
    main()
