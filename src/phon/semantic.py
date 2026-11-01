"""PHON semantic analyzer (v0.1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .ast_nodes import (
    Compressor, Channel, CompressStmt, TransmitStmt,
    BandStmt, CaptureStmt, Component, EmitStmt, InterfereStmt,
    Layer, LetStmt, Program, PropagateStmt, ReadStmt, ReturnStmt,
)

__version__ = "0.1.0"


@dataclass
class Diagnostic:
    severity: str
    message: str
    where: str = ""

    def __str__(self) -> str:
        tag = f"[{self.where}] " if self.where else ""
        return f"{self.severity.upper()}: {tag}{self.message}"


class SemanticError(Exception):
    """Raised by validate() when errors exist."""


class SemanticAnalyzer:
    def __init__(self, program: Program) -> None:
        self.program = program
        self.diagnostics: List[Diagnostic] = []
        self.components: Dict[str, Component] = {}
        self.layers: Dict[str, Layer] = {}

    def analyze(self) -> List[Diagnostic]:
        self._build_component_table()
        self._check_duplicate_components()
        self._check_interfere_references()
        self._check_emit_references()
        self._check_capture_read_references()
        self._check_band_frequencies()
        self._check_detect_usage()
        self._check_compression_references()
        self._check_compression_parameters()
        self._build_layer_table()
        self._check_duplicate_layers()
        self._check_layer_dimensions()
        self._check_propagate_references()
        self._check_propagate_chain()
        return self.diagnostics

    def errors(self) -> List[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == "error"]

    def warnings(self) -> List[Diagnostic]:
        return [d for d in self.diagnostics if d.severity == "warning"]

    def ok(self) -> bool:
        return not self.errors()

    def validate(self) -> None:
        errs = self.errors()
        if errs:
            raise SemanticError("; ".join(str(e) for e in errs))

    def _error(self, message: str, where: str = "") -> None:
        self.diagnostics.append(Diagnostic("error", message, where))

    def _build_component_table(self) -> None:
        for c in self.program.components:
            self.components[c.name] = c

    def _build_layer_table(self) -> None:
        for layer in self.program.layers:
            self.layers[layer.name] = layer

    def _check_duplicate_layers(self) -> None:
        seen = set()
        for layer in self.program.layers:
            if layer.name in seen:
                self._error(f"Duplicate layer name: '{layer.name}'", where="layer")
            seen.add(layer.name)

    def _check_layer_dimensions(self) -> None:
        valid = {"relu", "sigmoid", "softmax", "linear"}
        for layer in self.program.layers:
            if layer.input_dim <= 0:
                self._error(f"layer '{layer.name}': input_dim must be positive, got {layer.input_dim}", where="layer")
            if layer.output_dim <= 0:
                self._error(f"layer '{layer.name}': output_dim must be positive, got {layer.output_dim}", where="layer")
            if layer.activation not in valid:
                self._error(f"layer '{layer.name}': unknown activation '{layer.activation}' (expected one of {sorted(valid)})", where="layer")
            if not layer.weights_path:
                self._error(f"layer '{layer.name}': weights_path is empty", where="layer")

    def _check_propagate_references(self) -> None:
        for flow in self.program.flows:
            for stmt in flow.statements:
                if isinstance(stmt, PropagateStmt):
                    if stmt.layer_name not in self.layers:
                        self._error(f"undefined layer '{stmt.layer_name}' in propagate (flow '{flow.name}')", where="propagate")

    def _check_propagate_chain(self) -> None:
        for flow in self.program.flows:
            shapes: Dict[str, int] = {}
            for stmt in flow.statements:
                if isinstance(stmt, BandStmt):
                    shapes[stmt.name] = -1
                elif isinstance(stmt, PropagateStmt):
                    layer = self.layers.get(stmt.layer_name)
                    if layer is None:
                        continue
                    in_shape = shapes.get(stmt.input_var)
                    if in_shape is not None and in_shape != -1 and in_shape != layer.input_dim:
                        self._error(
                            f"propagate into '{layer.name}': '{stmt.input_var}' has dim {in_shape}, layer expects {layer.input_dim} (flow '{flow.name}')",
                            where="propagate",
                        )
                    shapes[stmt.output_var] = layer.output_dim

    def _check_duplicate_components(self) -> None:
        seen = set()
        for c in self.program.components:
            if c.name in seen:
                self._error(f"Duplicate component name: '{c.name}'", where="component")
            seen.add(c.name)

    def _check_interfere_references(self) -> None:
        for flow in self.program.flows:
            for stmt in flow.statements:
                if not isinstance(stmt, InterfereStmt):
                    continue
                for inp in stmt.inputs:
                    if inp not in self.components:
                        self._error(
                            f"undefined input '{inp}' in interfere (flow '{flow.name}')",
                            where="interfere",
                        )
                if stmt.at not in self.components:
                    self._error(
                        f"undefined interferometer '{stmt.at}' (flow '{flow.name}')",
                        where="interfere",
                    )

    def _check_emit_references(self) -> None:
        for flow in self.program.flows:
            for stmt in flow.statements:
                if not isinstance(stmt, EmitStmt):
                    continue
                if stmt.target not in self.components:
                    self._error(
                        f"undefined emit target '{stmt.target}' (flow '{flow.name}')",
                        where="emit",
                    )

    def _check_capture_read_references(self) -> None:
        for flow in self.program.flows:
            for stmt in flow.statements:
                if isinstance(stmt, CaptureStmt):
                    self._require_component(stmt.source, "capture source", flow.name)
                    self._require_resonator(stmt.target, "capture target", flow.name)
                elif isinstance(stmt, ReadStmt):
                    self._require_resonator(stmt.source, "read source", flow.name)
                    self._require_component(stmt.target, "read target", flow.name)

    def _require_component(self, name: str, role: str, flow_name: str) -> None:
        if name not in self.components:
            self._error(
                f"undefined {role} '{name}' (flow '{flow_name}')",
                where="capture/read",
            )

    def _require_resonator(self, name: str, role: str, flow_name: str) -> None:
        if name not in self.components:
            self._error(
                f"undefined {role} '{name}' (flow '{flow_name}')",
                where="capture/read",
            )
            return
        c = self.components[name]
        if c.type != "resonator":
            self._error(
                f"{role} '{name}' is not a resonator (type: {c.type})",
                where="capture/read",
            )

    def _check_band_frequencies(self) -> None:
        for flow in self.program.flows:
            for stmt in flow.statements:
                if not isinstance(stmt, BandStmt):
                    continue
                if stmt.freq.strip().startswith(("load(", "load ")):
                    continue
                head = stmt.freq.split()[0] if stmt.freq.split() else ""
                try:
                    freq = float(head)
                except (ValueError, IndexError):
                    self._error(
                        f"band '{stmt.name}' has non-numeric frequency '{stmt.freq}' "
                        f"(flow '{flow.name}')",
                        where="band",
                    )
                    continue
                if freq <= 0:
                    self._error(
                        f"band '{stmt.name}' frequency must be positive, got {freq} "
                        f"(flow '{flow.name}')",
                        where="band",
                    )

    def _check_detect_usage(self) -> None:
        has_detector = any(getattr(c, "type", None) == "detector" for c in self.program.components)
        for flow in self.program.flows:
            for stmt in flow.statements:
                expr = ""
                if isinstance(stmt, (LetStmt, ReturnStmt)):
                    expr = stmt.expr
                if "detect" in expr.lower() and not has_detector:
                    self._error(
                        f"uses detect() but no detector component is defined "
                        f"(flow '{flow.name}')",
                        where=type(stmt).__name__,
                    )

    def _check_compression_references(self) -> None:
        for flow in self.program.flows:
            for stmt in flow.statements:
                if isinstance(stmt, CompressStmt):
                    if stmt.compressor not in self.components:
                        self._error(f"undefined compressor '{stmt.compressor}' (flow '{flow.name}')", where="compress")
                    elif not isinstance(self.components[stmt.compressor], Compressor):
                        self._error(f"'{stmt.compressor}' is not a compressor (flow '{flow.name}')", where="compress")
                elif isinstance(stmt, TransmitStmt):
                    if stmt.channel not in self.components:
                        self._error(f"undefined channel '{stmt.channel}' (flow '{flow.name}')", where="transmit")
                    elif not isinstance(self.components[stmt.channel], Channel):
                        self._error(f"'{stmt.channel}' is not a channel (flow '{flow.name}')", where="transmit")

    def _check_compression_parameters(self) -> None:
        for c in self.program.components:
            if isinstance(c, Compressor) and c.ratio <= 0:
                self._error(f"compressor '{c.name}' ratio must be positive, got {c.ratio}", where="component")
            if isinstance(c, Channel) and c.bandwidth <= 0:
                self._error(f"channel '{c.name}' bandwidth must be positive, got {c.bandwidth}", where="component")
