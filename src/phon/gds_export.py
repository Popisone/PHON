"""PHON GDSII export using gdstk.

Maps PHON components to GDS layers:
  Layer 1: resonator (ring)
  Layer 2: waveguide (path)
  Layer 3: detector (rectangle pad)
  Layer 4: compressor/channel (rectangle with label)
  Layer 5: text labels
"""
from __future__ import annotations

import math
from typing import Any, Dict, List, Tuple

import gdstk
from phon.ast_nodes import Compressor, Channel

# GDS layer numbers
LAYER_RESONATOR = 1
LAYER_WAVEGUIDE = 2
LAYER_DETECTOR = 3
LAYER_COMPRESSOR = 4
LAYER_TEXT = 5

# Physical constants (simplified for demo)
WAVEGUIDE_WIDTH_UM = 0.5
RING_GAP_UM = 0.2
DETECTOR_SIZE_UM = 10.0


def _freq_to_radius(freq_ghz: float) -> float:
    """Convert frequency (GHz) to ring radius (um)."""
    # Simplified: higher freq -> smaller ring
    base_freq = 5.0
    base_radius = 5.0
    if freq_ghz <= 0:
        return base_radius
    return base_radius * (base_freq / freq_ghz)


def _parse_freq(text: str) -> float:
    """Parse '5GHz' -> 5.0."""
    text = text.replace("GHz", "").strip()
    try:
        return float(text)
    except ValueError:
        return 5.0


def build_gds(program, output_path: str) -> None:
    """Build GDS file from a parsed PHON Program."""
    lib = gdstk.Library("PHON")
    top = lib.new_cell("TOP")

    x_cursor = 0.0
    y_cursor = 0.0
    max_y = 0.0
    spacing = 20.0

    for comp in program.components:
        if isinstance(comp, Compressor):
            comp_type = "compressor"
            name = comp.name
            fields = {"ratio": comp.ratio}
        elif isinstance(comp, Channel):
            comp_type = "channel"
            name = comp.name
            fields = {"bandwidth": comp.bandwidth}
        else:
            comp_type = comp.type
            name = comp.name
            fields = comp.fields

        if comp_type == "resonator":
            freq = _parse_freq(fields.get("freq", "5GHz"))
            radius = _freq_to_radius(freq)
            ring = gdstk.ellipse(
                (x_cursor + radius, y_cursor + radius),
                radius,
                inner_radius=radius - WAVEGUIDE_WIDTH_UM,
                layer=LAYER_RESONATOR,
            )
            top.add(ring)
            # Label
            top.add(gdstk.Label(name, (x_cursor, y_cursor - 2.0), layer=LAYER_TEXT))
            max_y = max(max_y, y_cursor + 2 * radius)

        elif comp_type == "waveguide":
            length = 10.0  # default
            path = gdstk.RobustPath(
                (x_cursor, y_cursor),
                WAVEGUIDE_WIDTH_UM,
                layer=LAYER_WAVEGUIDE,
            )
            path.segment((x_cursor + length, y_cursor))
            top.add(path)
            top.add(gdstk.Label(name, (x_cursor, y_cursor - 2.0), layer=LAYER_TEXT))

        elif comp_type == "detector":
            rect = gdstk.rectangle(
                (x_cursor, y_cursor),
                (x_cursor + DETECTOR_SIZE_UM, y_cursor + DETECTOR_SIZE_UM),
                layer=LAYER_DETECTOR,
            )
            top.add(rect)
            top.add(gdstk.Label(name, (x_cursor, y_cursor - 2.0), layer=LAYER_TEXT))
            max_y = max(max_y, y_cursor + DETECTOR_SIZE_UM)

        elif comp_type in ("compressor", "channel"):
            rect = gdstk.rectangle(
                (x_cursor, y_cursor),
                (x_cursor + 8.0, y_cursor + 5.0),
                layer=LAYER_COMPRESSOR,
            )
            top.add(rect)
            top.add(gdstk.Label(name, (x_cursor, y_cursor - 2.0), layer=LAYER_TEXT))

        # Advance cursor
        x_cursor += spacing
        if x_cursor > 200.0:
            x_cursor = 0.0
            y_cursor = max_y + spacing

    lib.add(top)
    lib.write_gds(output_path, max_points=4000)
    print(f"[OK] GDS written: {output_path}")
    print(f"     Cells: {len(lib.cells)}")
    print(f"     Top cell polygons: {len(top.polygons)}")
    print(f"     Top cell labels: {len(top.labels)}")
