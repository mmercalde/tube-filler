"""Shared CAD helpers.  Every model in cad/ is driven by ../params.py."""
import os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
OUT = os.path.join(ROOT, "out")
os.makedirs(OUT, exist_ok=True)

import params as P                                    # noqa: E402
from build123d import *                               # noqa: E402,F401,F403
from build123d import ColorIndex, LineType            # noqa: E402


def _faces(obj):
    if hasattr(obj, "faces"):
        f = obj.faces()
        return list(f) if not isinstance(f, list) else f
    return [obj]


def save_dxf(name, cut, scribe=None):
    """2D cut profile -> DXF.  `scribe` goes on a dashed layer (weld/fold marks)."""
    ex = ExportDXF(unit=Unit.MM)
    ex.add_layer("CUT", color=ColorIndex.RED, line_weight=0.5)
    ex.add_layer("SCRIBE", color=ColorIndex.YELLOW, line_type=LineType.DASHED)
    ex.add_shape(_faces(cut), layer="CUT")
    if scribe is not None:
        ex.add_shape(scribe if isinstance(scribe, list) else [scribe], layer="SCRIBE")
    path = os.path.join(OUT, name + ".dxf")
    ex.write(path)
    return path


def save_svg(name, cut, scribe=None):
    ex = ExportSVG(unit=Unit.MM, line_weight=0.4)
    ex.add_layer("CUT", line_color=ColorIndex.BLACK, line_weight=0.5)
    ex.add_shape(_faces(cut), layer="CUT")
    if scribe is not None:
        ex.add_layer("SCRIBE", line_color=ColorIndex.BLUE, line_type=LineType.DASHED)
        ex.add_shape(scribe if isinstance(scribe, list) else [scribe], layer="SCRIBE")
    path = os.path.join(OUT, name + ".svg")
    ex.write(path)
    return path


def save_step(name, shape):
    path = os.path.join(OUT, name + ".step")
    export_step(shape, path)
    return path


def save_stl(name, shape, tol=0.05):
    path = os.path.join(OUT, name + ".stl")
    export_stl(shape, path, tolerance=tol, angular_tolerance=0.1)
    return path


# ---------------------------------------------------------------- primitives
def tie_hole_positions():
    return [(sx * P.tie_xy, sy * P.tie_xy) for sx in (-1, 1) for sy in (-1, 1)]


def clamp_plate_2d(bore, size=None):
    """Square clamp plate: central bore + 4 tie-rod holes on the diagonals."""
    size = size or P.plate_size
    sk = Rectangle(size, size) - Circle(bore / 2)
    for x, y in tie_hole_positions():
        sk -= Pos(x, y) * Circle(P.tie_rod_hole / 2)
    return sk


def bolt_ring_2d(size, bore, bc, dia, n=4, diagonal=True):
    sk = Rectangle(size, size) - Circle(bore / 2)
    r = bc / 2
    off = r * (0.5 ** 0.5) if diagonal else r
    pts = ([(sx * off, sy * off) for sx in (-1, 1) for sy in (-1, 1)] if diagonal
           else [(off, 0), (-off, 0), (0, off), (0, -off)])
    for x, y in pts:
        sk -= Pos(x, y) * Circle(dia / 2)
    return sk
