"""The scoring rubric, frozen before runs and scored dimension by dimension.

Two doctrine rules are enforced here rather than described:

Never blank (P09). Every dimension must carry either a band or an explicit
UNDETERMINED. A missing dimension is an error, not a pass. A blank field reads
as innocence to a human eye, and that single fact is responsible for a great
deal of institutional self-deception.

No premature collapse (evaluation doctrine). `aggregate()` refuses to return a
single number until a calibration attestation says the bands mean something
comparable across dimensions. An average of eight uncalibrated scales is a
number with no referent, and it will be quoted as though it had one.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from .canonical import digest

__all__ = [
    "DIMENSIONS",
    "UNDETERMINED",
    "DimensionScore",
    "Scorecard",
    "CalibrationAttestation",
    "PrematureCollapse",
    "BlankScore",
]

#: The eight dimensions, kept separate on purpose. Collapsing them hides the
#: trade the operator actually made: a run can be decisive and wrong, or
#: correct and useless, and one number cannot say which.
DIMENSIONS: tuple[str, ...] = (
    "factual_correctness",
    "protocol_adherence",
    "deduction_quality",
    "decision_usefulness",
    "calibration",
    "drift_control",
    "completion",
    "evidence_richness",
)

#: The value a grader must use when a dimension cannot be resolved. Distinct
#: from a low score: unresolved is not the same as bad.
UNDETERMINED = "UNDETERMINED"


class PrematureCollapse(Exception):
    """An aggregate was requested before the bands were calibrated."""


class BlankScore(Exception):
    """A dimension was left silent instead of scored or declared undetermined."""


@dataclass(frozen=True)
class DimensionScore:
    """One dimension's verdict, with the evidence that supports it.

    `band` is an integer 0-100 or the string UNDETERMINED. Integers keep the
    record hashable across languages; see canonical.py.
    """

    band: int | str
    rationale: str

    def __post_init__(self) -> None:
        if self.band == UNDETERMINED:
            if not self.rationale.strip():
                raise BlankScore(
                    "UNDETERMINED requires a rationale saying what is unresolved. "
                    "Undetermined is a finding, not a shrug."
                )
            return
        if isinstance(self.band, bool) or not isinstance(self.band, int):
            raise ValueError(
                f"band must be an int 0-100 or {UNDETERMINED!r}, got {self.band!r}"
            )
        if not 0 <= self.band <= 100:
            raise ValueError(f"band out of range: {self.band}")
        if not self.rationale.strip():
            raise BlankScore("every band requires a rationale")

    @property
    def is_undetermined(self) -> bool:
        return self.band == UNDETERMINED

    def to_payload(self) -> dict[str, Any]:
        return {"band": self.band, "rationale": self.rationale}


@dataclass(frozen=True)
class CalibrationAttestation:
    """A signed claim that the bands are comparable across dimensions.

    This exists to be hard to produce. It is the only key that unlocks
    `Scorecard.aggregate()`, and it names a human who can be asked how the
    bands were established.
    """

    method: str
    attested_by: str
    reference_runs: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.method.strip():
            raise ValueError("calibration requires a stated method")
        if not self.attested_by.strip():
            raise ValueError("calibration requires a named attester")
        if not self.reference_runs:
            raise ValueError(
                "calibration requires reference runs; bands cannot be declared "
                "comparable in the abstract"
            )

    def to_payload(self) -> dict[str, Any]:
        return {
            "method": self.method,
            "attested_by": self.attested_by,
            "reference_runs": list(self.reference_runs),
        }


@dataclass(frozen=True)
class Scorecard:
    """A complete set of dimension scores for one run."""

    scores: Mapping[str, DimensionScore]

    def __post_init__(self) -> None:
        missing = [name for name in DIMENSIONS if name not in self.scores]
        if missing:
            raise BlankScore(
                "silence is prohibited; score or declare UNDETERMINED for: "
                + ", ".join(missing)
            )
        unknown = set(self.scores) - set(DIMENSIONS)
        if unknown:
            raise ValueError(f"unknown dimensions: {', '.join(sorted(unknown))}")

    @property
    def undetermined(self) -> tuple[str, ...]:
        return tuple(
            name for name in DIMENSIONS if self.scores[name].is_undetermined
        )

    def to_payload(self) -> dict[str, Any]:
        return {name: self.scores[name].to_payload() for name in DIMENSIONS}

    @property
    def seal(self) -> str:
        return digest(self.to_payload())

    def aggregate(self, calibration: CalibrationAttestation | None = None) -> int:
        """Return a single number, or refuse to.

        Refusal is the point. Without calibration the dimensions are eight
        different scales wearing the same units.
        """
        if calibration is None:
            raise PrematureCollapse(
                "dimensions cannot be collapsed into one number before "
                "semantics and calibration are established. Report the "
                "scorecard, or supply a CalibrationAttestation."
            )
        determined = [
            self.scores[name].band
            for name in DIMENSIONS
            if not self.scores[name].is_undetermined
        ]
        if not determined:
            raise PrematureCollapse(
                "every dimension is undetermined; there is nothing to aggregate"
            )
        # Integer mean, floor-rounded: the aggregate must never read as more
        # precise than the bands it came from.
        return sum(determined) // len(determined)  # type: ignore[arg-type]
