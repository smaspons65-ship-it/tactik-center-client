"""Run conditions, blinding, and the gates that void a measurement.

Doctrine P08: blindness is attested, never assumed. A run where the wall was
crossed does not get a lower score. It gets no score, because a contaminated
measurement is not a weak measurement — it is not a measurement.

Doctrine, evaluation: a behavioral protocol must not grade itself as proof of
effectiveness. Self-evaluation is for debugging, not validation.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .canonical import digest
from .rubric import Scorecard

__all__ = [
    "RunConditions",
    "BlindingAttestation",
    "Breach",
    "Run",
    "ContaminatedRun",
    "SelfGraded",
    "NO_SCORE",
]

#: What a voided run reports instead of a number. It is deliberately not zero:
#: zero is a measurement, and this is the absence of one.
NO_SCORE = "NO_SCORE"


class ContaminatedRun(Exception):
    """A scorecard was requested for a run whose blinding was breached."""


class SelfGraded(Exception):
    """The subject of a run also graded it."""


@dataclass(frozen=True)
class RunConditions:
    """Everything that must be held constant across an A/B comparison.

    If two arms differ here, a difference in outcome is not attributable to
    the thing under test.
    """

    model: str
    tools: tuple[str, ...]
    retrieval: str
    fresh_session: bool

    def __post_init__(self) -> None:
        if not self.model.strip():
            raise ValueError("run conditions must name the model")
        if not self.retrieval.strip():
            raise ValueError(
                "run conditions must state the retrieval condition, including "
                "'none' when there was none"
            )

    def to_payload(self) -> dict[str, Any]:
        return {
            "model": self.model,
            "tools": sorted(self.tools),
            "retrieval": self.retrieval,
            "fresh_session": self.fresh_session,
        }

    @property
    def seal(self) -> str:
        return digest(self.to_payload())

    def differences_from(self, other: "RunConditions") -> tuple[str, ...]:
        """Name the fields that differ, so an unsound comparison is visible."""
        mine, theirs = self.to_payload(), other.to_payload()
        return tuple(key for key in sorted(mine) if mine[key] != theirs[key])


@dataclass(frozen=True)
class Breach:
    """A recorded crossing of the wall between roles."""

    what: str
    when: str
    recorded_by: str

    def __post_init__(self) -> None:
        if not self.what.strip():
            raise ValueError("a breach must say what was crossed")

    def to_payload(self) -> dict[str, Any]:
        return {"what": self.what, "when": self.when, "recorded_by": self.recorded_by}


@dataclass(frozen=True)
class BlindingAttestation:
    """Who could see what, attested by name.

    Doctrine P08 splits the mandate: whoever owns the objective does not watch
    the exchange, whoever negotiates does not know the sealed objective, and
    observers see nothing live.
    """

    objective_holder: str
    negotiator: str
    grader: str
    negotiator_saw_objective: bool
    holder_watched_live: bool
    breaches: tuple[Breach, ...] = field(default=())

    def __post_init__(self) -> None:
        for role, name in (
            ("objective_holder", self.objective_holder),
            ("negotiator", self.negotiator),
            ("grader", self.grader),
        ):
            if not name.strip():
                raise ValueError(f"{role} must be named; blindness is attested")

    @property
    def is_clean(self) -> bool:
        return not (
            self.negotiator_saw_objective
            or self.holder_watched_live
            or self.breaches
        )

    def contamination(self) -> tuple[str, ...]:
        """Every reason this run is not a measurement."""
        reasons: list[str] = []
        if self.negotiator_saw_objective:
            reasons.append(
                "negotiator knew the sealed objective; hitting it proves steering, "
                "not performance"
            )
        if self.holder_watched_live:
            reasons.append(
                "objective holder watched the exchange live; the wall was open"
            )
        reasons.extend(f"recorded breach: {breach.what}" for breach in self.breaches)
        return tuple(reasons)

    def to_payload(self) -> dict[str, Any]:
        return {
            "objective_holder": self.objective_holder,
            "negotiator": self.negotiator,
            "grader": self.grader,
            "negotiator_saw_objective": self.negotiator_saw_objective,
            "holder_watched_live": self.holder_watched_live,
            "breaches": [breach.to_payload() for breach in self.breaches],
        }


@dataclass(frozen=True)
class Run:
    """One graded attempt at one frozen case."""

    run_id: str
    case_seal: str
    conditions: RunConditions
    blinding: BlindingAttestation
    scorecard: Scorecard
    subject: str

    def __post_init__(self) -> None:
        if not self.run_id.strip():
            raise ValueError("run requires an id")
        if not self.subject.strip():
            raise ValueError(
                "run must name its subject: the protocol or model under test"
            )

    def result(self) -> Scorecard | str:
        """The scorecard, or NO_SCORE if the run was contaminated."""
        return NO_SCORE if not self.blinding.is_clean else self.scorecard

    def require_measurement(self) -> Scorecard:
        """Return the scorecard, or refuse because this run measured nothing."""
        if not self.blinding.is_clean:
            raise ContaminatedRun(
                f"run {self.run_id!r} is not a measurement:\n  "
                + "\n  ".join(self.blinding.contamination())
            )
        return self.scorecard

    def require_independent_grading(self) -> None:
        """Raise if the subject graded itself.

        Such a run is still useful for debugging. It is not evidence that the
        protocol works, and the distinction erodes the moment it is left to
        a reader to notice.
        """
        if self.blinding.grader.strip() == self.subject.strip():
            raise SelfGraded(
                f"run {self.run_id!r}: {self.subject!r} graded its own output. "
                "Usable for debugging, not as independent validation."
            )

    def to_payload(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "case_seal": self.case_seal,
            "subject": self.subject,
            "conditions": self.conditions.to_payload(),
            "blinding": self.blinding.to_payload(),
            "scorecard": self.scorecard.to_payload(),
            "contaminated": not self.blinding.is_clean,
        }

    @property
    def seal(self) -> str:
        return digest(self.to_payload())
