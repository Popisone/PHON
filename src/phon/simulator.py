"""PHON simulator - idealized wave-physics evaluator with state."""

from __future__ import annotations

import cmath
import math
from dataclasses import dataclass
from typing import Any, Dict, List

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


def _snapshot(sig: Signal) -> Signal:
    return Signal(freq_ghz=sig.freq_ghz, phase_rad=sig.phase_rad, amplitude=sig.amplitude)


def parse_phase(text: str) -> float:
    """Parse a PHON phase literal into radians."""
    s = text.strip().lower()
    if s in ("0", "0.0"):
        return 0.0
    if s in ("pi", "\u03c0"):
        return math.pi
    if s in ("-pi", "-\u03c0"):
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
      - band:   allocates a signal with amplitude 1.0
      - emit:   bus = band
      - interfere: bus = complex sum of input buses
      - capture: resonator = snapshot of source bus
      - read:   bus = snapshot of source resonator (or zero if empty)
      - let:    value = detect(bus) OR alias of value/band
      - return: sets _last_result
    """

    def __init__(self, config: Dict[str, Any]) -> None:
        self.config = config
        self.bands: Dict[str, Signal] = {}
        self.buses: Dict[str, Signal] = {}
        self.resonators: Dict[str, Signal] = {}
        self.values: Dict[str, Any] = {}
        self._last_result: Any = None
        self._components = {c["name"]: c for c in config.get("components", [])}
        self._detector_thresholds = self._build_detector_thresholds()

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


    def _eval_condition(self, expr: str) -> bool:
        """Evaluate a simple condition: X OP Y (OP in ==, !=, <, >, <=, >=)."""
        import re
        m = re.match(r"^\s*(\w+)\s*(==|!=|<=|>=|<|>)\s*(.+?)\s*$", expr)
        if not m:
            return False
        lhs_name, op, rhs_str = m.groups()
        lhs = self.values.get(lhs_name, 0)
        # Try to coerce both sides to floats for numeric comparison
        try:
            lhs_num = float(lhs)
        except (ValueError, TypeError):
            lhs_num = lhs
        try:
            rhs_num = float(rhs_str)
        except ValueError:
            rhs_num = self.values.get(rhs_str, 0)
            try:
                rhs_num = float(rhs_num)
            except (ValueError, TypeError):
                pass
        # Prefer numeric comparison when both sides are numeric
        if isinstance(lhs_num, float) and isinstance(rhs_num, float):
            a, b = lhs_num, rhs_num
        else:
            a, b = lhs, rhs_num
        if op == "==":
            return a == b
        if op == "!=":
            return a != b
        if op == "<":
            return a < b
        if op == ">":
            return a > b
        if op == "<=":
            return a <= b
        if op == ">=":
            return a >= b
        return False

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
                raise SimulationError(f"emit of unknown band: {stmt}")
            self.buses[stmt["target"]] = band
        elif t == "interfere":
            self.buses[stmt["target"]] = self._interfere(stmt["inputs"])
        elif t == "capture":
            src = self.buses.get(stmt["source"])
            if src is not None:
                self.resonators[stmt["target"]] = _snapshot(src)
        elif t == "read":
            stored = self.resonators.get(stmt["source"])
            if stored is not None:
                self.buses[stmt["target"]] = _snapshot(stored)
            else:
                self.buses[stmt["target"]] = Signal(0.0, 0.0, 0.0)
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
        elif t == "if":
            cond = stmt["condition"]
            branch = stmt["then"] if self._eval_condition(cond) else stmt["else"]
            for inner in branch:
                self._step(inner)
        elif t == "compress":
            src_sig = self.buses.get(stmt["source"]) or self.bands.get(stmt["source"])
            if src_sig is None:
                raise SimulationError(f"compress of unknown signal: {stmt}")
            comp = self._components.get(stmt["compressor"])
            if comp is None:
                raise SimulationError(f"unknown compressor: {stmt}")
            ratio = comp.get("ratio", 1.0)
            # Свиваме честотата (компресия)
            self.buses[stmt["target"]] = Signal(
                freq_ghz=src_sig.freq_ghz / ratio,
                phase_rad=src_sig.phase_rad,
                amplitude=src_sig.amplitude
            )
        elif t == "transmit":
            src_sig = self.buses.get(stmt["source"])
            if src_sig is None:
                raise SimulationError(f"transmit of unknown signal: {stmt}")
            ch = self._components.get(stmt["channel"])
            if ch is None:
                raise SimulationError(f"unknown channel: {stmt}")
            bw = ch.get("bandwidth", 1.0)
            # Опростена физика: скорост = лента * 100 Gbps
            self.values[stmt["target"]] = bw * 100.0
        elif t == "return":
            expr = stmt["expr"]
            if expr in self.values:
                self._last_result = self.values[expr]
            elif expr in self.bands:
                self._last_result = self.bands[expr]
            else:
                self._last_result = expr
        else:
            raise SimulationError(f"Unknown statement type: {t!r}")
