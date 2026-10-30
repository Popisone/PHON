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

@dataclass
class IfStmt:
    condition: str
    then_body: List[Any] = field(default_factory=list)
    else_body: List[Any] = field(default_factory=list)

# --- v0.4: Compression & Transmission Nodes ---
@dataclass
class Compressor:
    name: str
    ratio: float

@dataclass
class Channel:
    name: str
    bandwidth: float

@dataclass
class CompressStmt:
    source: str
    compressor: str
    target: str

@dataclass
class TransmitStmt:
    source: str
    channel: str
    target: str

@dataclass
class ForStmt:
    variable: str
    start: str
    end: str
    body: List["FlowStmt"]


@dataclass
class WhileStmt:
    condition: Any
    body: List[Any]


@dataclass
class BreakStmt:
    pass

@dataclass
class ContinueStmt:
    pass
