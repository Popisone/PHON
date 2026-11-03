"""
Hardware material presets for photonic MZI meshes.

Replaces hardcoded values (0.2 dB/m, 200 um footprint, 25 GHz BW)
with configurable material properties.
"""
from dataclasses import dataclass, field
from typing import Dict, Optional


@dataclass
class MaterialProperties:
    name: str
    propagation_loss_db_per_cm: float
    mzi_insertion_loss_db: float
    mzi_footprint_um: float
    phase_shifter_type: str
    static_power_per_mzi_mw: float
    switching_energy_pj: float
    modulator_bw_ghz: float
    notes: str = ""

    def loss_db_per_m(self) -> float:
        return self.propagation_loss_db_per_cm * 100.0

    def total_loss_per_mzi_db(self, waveguide_length_per_mzi_um: Optional[float] = None) -> float:
        length_um = waveguide_length_per_mzi_um or self.mzi_footprint_um
        prop_loss_db = self.propagation_loss_db_per_cm * (length_um / 1e4)
        return prop_loss_db + self.mzi_insertion_loss_db


MATERIALS: Dict[str, MaterialProperties] = {
    "SiN": MaterialProperties(
        name="Silicon Nitride",
        propagation_loss_db_per_cm=0.2,
        mzi_insertion_loss_db=0.05,
        mzi_footprint_um=200.0,
        phase_shifter_type="thermo-optic",
        static_power_per_mzi_mw=20.0,
        switching_energy_pj=1000.0,
        modulator_bw_ghz=10.0,
        notes="Mature, low loss, slow switching",
    ),
    "Si": MaterialProperties(
        name="Silicon Photonics",
        propagation_loss_db_per_cm=2.0,
        mzi_insertion_loss_db=0.10,
        mzi_footprint_um=50.0,
        phase_shifter_type="carrier",
        static_power_per_mzi_mw=10.0,
        switching_energy_pj=50.0,
        modulator_bw_ghz=50.0,
        notes="Mature, fast, higher propagation loss",
    ),
    "TFLN": MaterialProperties(
        name="Thin-Film Lithium Niobate",
        propagation_loss_db_per_cm=0.3,
        mzi_insertion_loss_db=0.08,
        mzi_footprint_um=1000.0,
        phase_shifter_type="electro-optic",
        static_power_per_mzi_mw=0.1,
        switching_energy_pj=1.0,
        modulator_bw_ghz=100.0,
        notes="Fast, low V_pi, emerging",
    ),
    "BTO": MaterialProperties(
        name="Barium Titanate",
        propagation_loss_db_per_cm=0.5,
        mzi_insertion_loss_db=0.10,
        mzi_footprint_um=500.0,
        phase_shifter_type="electro-optic",
        static_power_per_mzi_mw=0.1,
        switching_energy_pj=1.0,
        modulator_bw_ghz=100.0,
        notes="Very fast, low loss, new material",
    ),
    "InP": MaterialProperties(
        name="Indium Phosphide",
        propagation_loss_db_per_cm=3.0,
        mzi_insertion_loss_db=0.15,
        mzi_footprint_um=500.0,
        phase_shifter_type="carrier",
        static_power_per_mzi_mw=20.0,
        switching_energy_pj=100.0,
        modulator_bw_ghz=40.0,
        notes="Active integration, higher loss",
    ),
    "Polymer": MaterialProperties(
        name="Electro-Optic Polymer",
        propagation_loss_db_per_cm=0.5,
        mzi_insertion_loss_db=0.10,
        mzi_footprint_um=1000.0,
        phase_shifter_type="electro-optic",
        static_power_per_mzi_mw=0.0,
        switching_energy_pj=0.1,
        modulator_bw_ghz=100.0,
        notes="Ultra-fast, low loss, stability concerns",
    ),
    "GST": MaterialProperties(
        name="Germanium-Antimony-Telluride (phase-change)",
        propagation_loss_db_per_cm=1.0,
        mzi_insertion_loss_db=0.50,
        mzi_footprint_um=100.0,
        phase_shifter_type="phase-change (non-volatile)",
        static_power_per_mzi_mw=0.0,
        switching_energy_pj=10000.0,
        modulator_bw_ghz=0.001,
        notes="Non-volatile, zero static power, slow switching (kHz)",
    ),
}


def get_material(name: str) -> MaterialProperties:
    if name not in MATERIALS:
        raise ValueError(
            f"Unknown material {name!r}. Available: {sorted(MATERIALS.keys())}"
        )
    return MATERIALS[name]