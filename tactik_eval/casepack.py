"""Sealed objectives and frozen case packs.

Doctrine P07: the objective is fixed and sealed before the first exchange
exists, and the session cannot begin without it. A goal stated after the
outcome is known will always have been met.

Doctrine, cross-model testing: freeze the prompt and the evidence pack, and
include cases whose correct behavior is YES, NO and bounded action under
uncertainty. A suite made only of cases that should end in NO measures
timidity and calls it rigor.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .canonical import digest

__all__ = [
    "CorrectBehavior",
    "SealedObjective",
    "Case",
    "CasePack",
    "SealBroken",
    "CoverageError",
]


class SealBroken(Exception):
    """Frozen content no longer hashes to the value recorded when it was sealed."""


class CoverageError(Exception):
    """A pack does not exercise the full decision range the doctrine requires."""


class CorrectBehavior:
    """The behavior a case is built to reward.

    BOUNDED is the load-bearing one. Doctrine P02: the most common failure in
    real negotiations is the false binary of accept-or-leave, and the posture
    that actually wins sits between them. A rubric that cannot express "acted,
    but inside a boundary" will score that posture as indecision.
    """

    YES = "YES"
    NO = "NO"
    BOUNDED = "BOUNDED"

    ALL = frozenset({YES, NO, BOUNDED})


@dataclass(frozen=True)
class SealedObjective:
    """What the run came for, fixed before it can be edited by the outcome.

    `floor` and `must_not_happen` are what make a consolation prize detectable:
    without them, movement is indistinguishable from movement toward the goal.
    """

    target: str
    floor: str
    must_not_happen: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.target.strip():
            raise ValueError("sealed objective requires a target")
        if not self.floor.strip():
            raise ValueError(
                "sealed objective requires a floor: without one, any outcome "
                "clears the bar retroactively"
            )
        if not self.must_not_happen:
            raise ValueError(
                "sealed objective requires at least one must-not-happen clause"
            )

    def to_payload(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "floor": self.floor,
            "must_not_happen": list(self.must_not_happen),
        }

    @property
    def seal(self) -> str:
        """The hash a grader can check the objective against after the fact."""
        return digest(self.to_payload())


@dataclass(frozen=True)
class Case:
    """One frozen scenario: sealed objective, fixed evidence, expected behavior."""

    case_id: str
    objective: SealedObjective
    evidence: tuple[str, ...]
    correct_behavior: str
    actor_constraints: tuple[str, ...] = field(default=())
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case requires an id")
        if self.correct_behavior not in CorrectBehavior.ALL:
            raise ValueError(
                f"unknown correct_behavior {self.correct_behavior!r}; "
                f"expected one of {sorted(CorrectBehavior.ALL)}"
            )
        if not self.evidence:
            raise ValueError(
                f"case {self.case_id}: an empty evidence pack cannot be frozen"
            )

    def to_payload(self) -> dict[str, Any]:
        return {
            "case_id": self.case_id,
            "objective": self.objective.to_payload(),
            "evidence": list(self.evidence),
            "correct_behavior": self.correct_behavior,
            "actor_constraints": list(self.actor_constraints),
            "notes": self.notes,
        }

    @property
    def seal(self) -> str:
        return digest(self.to_payload())


@dataclass(frozen=True)
class CasePack:
    """A frozen suite. Its seal is what a rerun is checked against."""

    pack_id: str
    cases: tuple[Case, ...]

    def __post_init__(self) -> None:
        if not self.cases:
            raise ValueError("a case pack requires at least one case")
        seen: set[str] = set()
        for case in self.cases:
            if case.case_id in seen:
                raise ValueError(f"duplicate case_id {case.case_id!r}")
            seen.add(case.case_id)

    def to_payload(self) -> dict[str, Any]:
        return {
            "pack_id": self.pack_id,
            "cases": [case.to_payload() for case in self.cases],
        }

    @property
    def seal(self) -> str:
        return digest(self.to_payload())

    def require_full_decision_range(self) -> None:
        """Raise unless YES, NO and BOUNDED are all exercised.

        A pack that omits one of these cannot distinguish judgment from a
        standing disposition, and a standing disposition scores well on a
        suite built in its own image.
        """
        present = {case.correct_behavior for case in self.cases}
        missing = CorrectBehavior.ALL - present
        if missing:
            raise CoverageError(
                f"pack {self.pack_id!r} never exercises "
                f"{', '.join(sorted(missing))}: it cannot separate judgment "
                "from disposition"
            )

    def verify_seal(self, expected: str) -> None:
        """Raise if the pack's content has moved since `expected` was recorded."""
        actual = self.seal
        if actual != expected:
            raise SealBroken(
                f"pack {self.pack_id!r} no longer matches its seal.\n"
                f"  sealed as: {expected}\n"
                f"  hashes to: {actual}\n"
                "Results measured against the sealed content do not carry over."
            )

    def case(self, case_id: str) -> Case:
        for candidate in self.cases:
            if candidate.case_id == case_id:
                return candidate
        raise KeyError(case_id)


def load_pack(payload: Mapping[str, Any]) -> CasePack:
    """Rebuild a pack from its canonical payload (the inverse of `to_payload`)."""
    raw_cases: Sequence[Mapping[str, Any]] = payload["cases"]
    cases = tuple(
        Case(
            case_id=raw["case_id"],
            objective=SealedObjective(
                target=raw["objective"]["target"],
                floor=raw["objective"]["floor"],
                must_not_happen=tuple(raw["objective"]["must_not_happen"]),
            ),
            evidence=tuple(raw["evidence"]),
            correct_behavior=raw["correct_behavior"],
            actor_constraints=tuple(raw.get("actor_constraints", ())),
            notes=raw.get("notes", ""),
        )
        for raw in raw_cases
    )
    return CasePack(pack_id=payload["pack_id"], cases=cases)
