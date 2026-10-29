"""PHON AST node classes (v0.1)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Medium:
    name: str
    fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class Component:
    type: str
    name: str
    fields: Dict[str, str] = field(default_factory=dict)


@dataclass
class BandStmt:
    name: str
    freq: str
    phase: str


@dataclass
class EmitStmt:
    expr: str
    target: str


@dataclass
class InterfereStmt:
    inputs: List[str]
    at: str
    target: str


@dataclass
class CaptureStmt:
    source: str
    target: str


@dataclass
class ReadStmt:
    source: str
    target: str


@dataclass
class LetStmt:
    name: str
    expr: str


@dataclass
class ReturnStmt:
    expr: str


@dataclass
class Flow:
    name: str
    statements: List[Any] = field(default_factory=list)


@dataclass
class Program:
    medium: Optional[Medium] = None
    components: List[Component] = field(default_factory=list)
    flows: List[Flow] = field(default_factory=list)
