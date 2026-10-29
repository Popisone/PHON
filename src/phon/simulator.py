"""PHON simulator - idealized wave-physics evaluator."""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

__version__ = "0.1.0"
DEFAULT_AMPLITUDE = 1.0
DEFAULT_THRESHOLD = 0.5


class SimulationError(Exception):
    """Raised when a program cannot be simulated."""


@dataclass
class Signal:
    freq_ghz: float
    phase_rad: float
    amplitude: float


def parse_phase(text: str) -> float:
    """Parse a PHON phase literal into radians."""
    s = text.strip().lower()
    if s in ("0", "0.0"):
        return 0.0
    if s in ("pi", "π"):
        return math.pi
    if s in ("-pi", "-π"):
        return -math.pi
    if s.endswith("pi"):
        try:
            return float(s[:-2]) * math.pi
        except ValueError:
            pass
    try:
        return float(s)
    except ValueError as e:
        raise SimulationError(f"Cannot parse phase {text!r}") from e


def parse_freq(text: str) -> float:
    """Parse a PHON frequency literal in GHz (takes the first number)."""
    parts = text.split()
    if not parts:
        raise SimulationError(f"Empty frequency: {text!r}")
    try:
        return float(parts[0])
    except ValueError as e:
        raise SimulationError(f"Cannot parse frequency {text!r}") from e


class Simulator:
    """Evaluates a PHON config dict using idealized wave physics.

    Model:
      - Each band has frequency (GHz), phase (rad), amplitude (default 1.0).
      - emit assigns a band to a bus.
      - interfere computes the complex sum of inputs and stores magnitude+phase.
      - detect compares amplitude against detector threshold -> 0 or 1.
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.bands: Dict[str, Signal] = {}
        self.buses: Dict[str, Signal] = {}
        self.values: Dict[str, Any] = {}
        self._last_result: Any = None
        self._components = {c["name"]: c for c in config.get("components", [])}
        self._detector_thresholds = self._build_detector_thresholds()

    # ---------- helpers ----------

    @staticmethod
    def _parse_bus_list(text: str) -> List[str]:
        s = text.strip()
        if s.startswith("[") and s.endswith("]"):
            s = s[1:-1]
        return [p.strip() for p in s.split(",") if p.strip()]

    def _build_detector_thresholds(self) -> Dict[str, float]:
        out: Dict[str, float] = {}
        for comp in self.config.get("components", []):
            if comp["type"] != "detector":
                continue
            fields = comp.get("fields", {})
            thr_text = fields.get("threshold", str(DEFAULT_THRESHOLD))
            try:
                thr = float(thr_text)
            except ValueError:
                thr = DEFAULT_THRESHOLD
            for bus in self._parse_bus_list(fields.get("in", "")):
                out[bus] = thr
        return out

    def _detect(self, bus_name: str) -> int:
        signal = self.buses.get(bus_name)
        if signal is None:
            return 0
        threshold = self._detector_thresholds.get(bus_name, DEFAULT_THRESHOLD)
        return 1 if signal.amplitude >= threshold else 0

    def _interfere(self, inputs: List[str]) -> Signal:
        present = [self.buses[i] for i in inputs if i in self.buses]
        if not present:
            return Signal(0.0, 0.0, 0.0)
        z = sum(s.amplitude * cmath.exp(1j * s.phase_rad) for s in present)
        return Signal(present[0].freq_ghz, cmath.phase(z), abs(z))

    # ---------- main loop ----------

    def run(self, flow_name: str = "main") -> Any:
        flow = next(
            (f for f in self.config.get("flows", []) if f["name"] == flow_name),
            None,
        )
        if flow is None:
            raise SimulationError(f"No flow named {flow_name!r}")

        for stmt in flow["statements"]:
            self._step(stmt)
        return self._last_result

    def _step(self, stmt: Dict[str, Any]) -> None:
        t = stmt["type"]
        if t == "band":
            self.bands[stmt["name"]] = Signal(
                freq_ghz=parse_freq(stmt["freq"]),
                phase_rad=parse_phase(stmt["phase"]),
                amplitude=DEFAULT_AMPLITUDE,
            )
        elif t == "emit":
            band = self.bands.get(stmt["expr"])
            if band is None:
                raise SimulationError(f"emit of unknown band {stmt['expr']!r}")
            self.buses[stmt["target"]] = band
        elif t == "interfere":
            self.buses[stmt["target"]] = self._interfere(stmt["inputs"])
        elif t == "let":
            expr = stmt["expr"]
            if expr.startswith("detect "):
                bus = expr.split(" ", 1)[1].strip()
                self.values[stmt["name"]] = self._detect(bus)
            elif expr in self.values:
                self.values[stmt["name"]] = self.values[expr]
            elif expr in self.bands:
                self.values[stmt["name"]] = self.bands[expr]
            else:
                self.values[stmt["name"]] = expr
        elif t == "return":
            expr = stmt["expr"]
            if expr in self.values:
                self._last_result = self.values[expr]
            elif expr in self.bands:
                self._last_result = self.bands[expr]
            else:
                self._last_result = expr
