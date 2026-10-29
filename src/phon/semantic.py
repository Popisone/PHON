"""PHON semantic analyzer (v0.1)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List

from .ast_nodes import (
    BandStmt, CaptureStmt, Component, EmitStmt, InterfereStmt,
    LetStmt, Program, ReadStmt, ReturnStmt,
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

    def analyze(self) -> List[Diagnostic]:
        self._build_component_table()
        self._check_duplicate_components()
        self._check_interfere_references()
        self._check_emit_references()
        self._check_capture_read_references()
        self._check_band_frequencies()
        self._check_detect_usage()
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
        has_detector = any(c.type == "detector" for c in self.program.components)
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
