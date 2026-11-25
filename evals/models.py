from dataclasses import dataclass, field
from typing import Callable


@dataclass
class Run:
    reply: str = ""
    tool_calls: list[dict] = field(default_factory=list)
    tool_outputs: list[str] = field(default_factory=list)
    seconds: float = 0.0
    error: str | None = None


@dataclass
class Verdict:
    ok: bool
    reason: str = ""


Check = Callable[[Run, "Case"], Verdict]


@dataclass
class Case:
    name: str
    family: str
    questions: list[str]
    checks: list[Check]