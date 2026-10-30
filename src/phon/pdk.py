"""PHON PDK (Process Design Kit) - layer definitions.

Standard layer stack for silicon photonics / phononics:
  Layer 1: Silicon (Si) waveguide core
  Layer 2: Silicon Dioxide (SiO2) cladding
  Layer 3: Lithium Niobate (LiNbO3) - for electro-optic modulators
  Layer 4: Metal (Al or Au) - for electrical contacts / detectors
  Layer 5: Text labels
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

@dataclass(frozen=True)
class Layer:
    name: str
    number: int
    color: str  # hex color for KLayout visualization
    material: str
    thickness_nm: float

# Standard PHON PDK layer stack
PHON_PDK: Dict[str, Layer] = {
    "si": Layer("Silicon", 1, "#4C6EF5", "Si", 220.0),
    "sio2": Layer("Silicon Dioxide", 2, "#F59F00", "SiO2", 2000.0),
    "linbo3": Layer("Lithium Niobate", 3, "#40C057", "LiNbO3", 600.0),
    "metal": Layer("Metal", 4, "#FA5252", "Al", 100.0),
    "text": Layer("Text", 5, "#868E96", "Label", 0.0),
}

def get_layer(name: str) -> Layer:
    if name not in PHON_PDK:
        raise ValueError(f"Unknown PDK layer: {name}. Available: {list(PHON_PDK.keys())}")
    return PHON_PDK[name]

def list_layers() -> str:
    lines = ["PHON PDK Layer Stack:"]
    for k, v in PHON_PDK.items():
        lines.append(f"  {k:8s} | Layer {v.number:2d} | {v.material:6s} | {v.thickness_nm:6.0f} nm | {v.name}")
    return "\n".join(lines)
