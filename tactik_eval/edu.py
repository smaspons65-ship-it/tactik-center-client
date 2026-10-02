"""TACTIK EDU: the faculty-approved Webscript and the criterion-level readiness card.

The Westcliff pilot proposal (Aug 2026) promises faculty a rehearsal script they
approve and version-lock before any candidate sees it, and a readiness view that
is "criterion-level ... never a single academic grade". Both promises are the
kind that erode under deadline, so both are gates here rather than intentions.

Two implementations answer to docs/WEBSCRIPT.md: this module, and the core
script in studio/faculty.html. Disagreement between them is a finding about us.

Construction refuses what is malformed (unknown states, out-of-range integers,
floats). Locking refuses what is unfinished: a question nobody approved, a
pressure level nobody defined, a mandatory stop condition someone removed. A
draft may be incomplete; a locked Webscript may not.
"""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass, field
from typing import Any, Mapping, Sequence

from .canonical import canonical_bytes, digest
from .casepack import SealedObjective
from .rubric import UNDETERMINED, CalibrationAttestation, PrematureCollapse

__all__ = [
    "FORMAT",
    "SYSTEM",
    "PRESSURE_LEVELS",
    "READINESS_LEVELS",
    "WEIGHT_TOTAL_BP",
    "MANDATORY_EVENTS",
    "MANDATORY_STOPS",
    "NotLockable",
    "ObjectiveDraft",
    "Lens",
    "State",
    "PressureLevel",
    "Question",
    "EventRule",
    "StopCondition",
    "Criterion",
    "ReadinessRubric",
    "TeachingProfile",
    "Webscript",
    "ReadinessObservation",
    "ReadinessCard",
    "load_webscript",
]

#: The payload format both implementations agree on.
FORMAT = "tactik-edu/webscript@1"

#: Owner of the states no committee lens speaks in (orientation, debrief).
SYSTEM = "system"

#: Proposal p.7 names three pressure levels and never defines them. Their
#: meaning is faculty content, so a level with no definition blocks the lock.
PRESSURE_LEVELS: tuple[int, ...] = (1, 2, 3)

#: Readiness is anchored levels 0-3, not a percentage. Four anchors per
#: criterion, written or approved by faculty.
READINESS_LEVELS: tuple[int, ...] = (0, 1, 2, 3)

#: Weights are integer basis points. 15% is 1500, never 0.15.
WEIGHT_TOTAL_BP = 10000

WEIGHT_USES = ("prioritization", "composite")
QUESTION_STATUSES = ("DRAFT", "APPROVED")
RUBRIC_STATUSES = ("DRAFT", "APPROVED")
FORMATS = ("cold_call", "seminar", "presentation")

#: The five adaptive event rules of proposal p.7. Faculty may reword the
#: response; they may not remove the rule. "answer_request" is the refusal to
#: write the candidate's work, and a Webscript without it is not this product.
MANDATORY_EVENTS: tuple[str, ...] = (
    "unsupported_claim",
    "high_confidence_low_evidence",
    "self_correction",
    "evasion_repeat",
    "answer_request",
)

#: The five stop conditions of proposal p.18. Faculty may add; never remove.
MANDATORY_STOPS: tuple[str, ...] = (
    "participant_requests_stop",
    "restricted_information",
    "departs_from_approved_scope",
    "generates_student_work",
    "faculty_concern",
)


class NotLockable(Exception):
    """A Webscript was submitted for version-lock while still unfinished."""

    def __init__(self, blockers: Sequence[tuple[str, str]]) -> None:
        self.blockers = tuple(blockers)
        lines = "\n  ".join(f"{code}: {detail}" for code, detail in self.blockers)
        super().__init__(
            f"this Webscript cannot be locked; {len(self.blockers)} "
            f"blocker(s):\n  {lines}"
        )


def _require_int(name: str, value: Any, low: int, high: int) -> None:
    # bool is an int subclass; True is not a pressure level.
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{name} must be an integer, got {value!r}")
    if not low <= value <= high:
        raise ValueError(f"{name} must be within {low}..{high}, got {value}")


def _require_text(name: str, value: Any) -> None:
    if not isinstance(value, str):
        raise ValueError(f"{name} must be a string, got {type(value).__name__}")


@dataclass(frozen=True)
class ObjectiveDraft:
    """The learning objective while faculty are still writing it.

    It may be incomplete in a draft. Locking turns it into a `SealedObjective`,
    which refuses a missing floor or a missing must-not-happen clause.
    """

    target: str
    floor: str
    must_not_happen: tuple[str, ...]

    def __post_init__(self) -> None:
        _require_text("objective.target", self.target)
        _require_text("objective.floor", self.floor)
        for clause in self.must_not_happen:
            _require_text("objective.must_not_happen[]", clause)

    def gaps(self) -> tuple[str, ...]:
        missing = []
        if not self.target.strip():
            missing.append("target")
        if not self.floor.strip():
            missing.append("floor")
        if not any(clause.strip() for clause in self.must_not_happen):
            missing.append("must_not_happen")
        return tuple(missing)

    def sealed(self) -> SealedObjective:
        return SealedObjective(
            target=self.target,
            floor=self.floor,
            must_not_happen=tuple(c for c in self.must_not_happen if c.strip()),
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "target": self.target,
            "floor": self.floor,
            "must_not_happen": list(self.must_not_happen),
        }


@dataclass(frozen=True)
class Lens:
    """A committee lens: a job and a boundary, never a person (proposal p.13)."""

    key: str
    name: str
    job: str
    primary_lens: str
    boundary: str

    def __post_init__(self) -> None:
        if not self.key.strip() or self.key == SYSTEM:
            raise ValueError(f"lens key {self.key!r} is empty or reserved")

    def to_payload(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "job": self.job,
            "primary_lens": self.primary_lens,
            "boundary": self.boundary,
        }


@dataclass(frozen=True)
class State:
    """One controlled state of the session (proposal p.8), with its exit."""

    key: str
    name: str
    owner: str
    goal: str
    exit: str

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("state requires a key")

    def to_payload(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "owner": self.owner,
            "goal": self.goal,
            "exit": self.exit,
        }


@dataclass(frozen=True)
class PressureLevel:
    level: int
    definition: str

    def __post_init__(self) -> None:
        _require_int("pressure level", self.level, 1, 3)
        _require_text("pressure definition", self.definition)

    def to_payload(self) -> dict[str, Any]:
        return {"level": self.level, "definition": self.definition}


@dataclass(frozen=True)
class Question:
    """One question in the bank. Only APPROVED questions ever reach a candidate."""

    qid: str
    state: str
    lens: str
    pressure: int
    text: str
    status: str
    approved_by: str | None
    outcomes: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        if not self.qid.strip():
            raise ValueError("question requires an id")
        for outcome in self.outcomes:
            _require_text(f"{self.qid}.outcomes[]", outcome)
        _require_int(f"{self.qid}.pressure", self.pressure, 1, 3)
        if self.status not in QUESTION_STATUSES:
            raise ValueError(
                f"{self.qid}: status must be one of {QUESTION_STATUSES}, "
                f"got {self.status!r}"
            )
        if self.approved_by is not None:
            _require_text(f"{self.qid}.approved_by", self.approved_by)

    def to_payload(self) -> dict[str, Any]:
        return {
            "qid": self.qid,
            "state": self.state,
            "lens": self.lens,
            "pressure": self.pressure,
            "text": self.text,
            "status": self.status,
            "approved_by": self.approved_by,
            "outcomes": list(self.outcomes),
        }


@dataclass(frozen=True)
class EventRule:
    """What the engine does on an event, and the words the candidate sees.

    `response` is the instruction faculty approve. `prompt` is the exact text
    shown to the candidate: the engine never composes its own. `lens` names
    who speaks, or None for whoever owns the current state.
    """

    event: str
    response: str
    prompt: str
    lens: str | None = None

    def __post_init__(self) -> None:
        _require_text(f"{self.event}.response", self.response)
        _require_text(f"{self.event}.prompt", self.prompt)
        if self.lens is not None:
            _require_text(f"{self.event}.lens", self.lens)

    def to_payload(self) -> dict[str, Any]:
        return {
            "event": self.event,
            "response": self.response,
            "prompt": self.prompt,
            "lens": self.lens,
        }


@dataclass(frozen=True)
class StopCondition:
    key: str
    text: str

    def to_payload(self) -> dict[str, Any]:
        return {"key": self.key, "text": self.text}


@dataclass(frozen=True)
class Criterion:
    """One readiness criterion (proposal p.8), weighted in basis points."""

    key: str
    name: str
    evidence: str
    weight_bp: int
    anchors: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.key.strip():
            raise ValueError("criterion requires a key")
        _require_int(f"{self.key}.weight_bp", self.weight_bp, 0, WEIGHT_TOTAL_BP)
        if len(self.anchors) != len(READINESS_LEVELS):
            raise ValueError(
                f"{self.key}: needs exactly {len(READINESS_LEVELS)} anchors, "
                f"one per readiness level, got {len(self.anchors)}"
            )

    def to_payload(self) -> dict[str, Any]:
        return {
            "key": self.key,
            "name": self.name,
            "evidence": self.evidence,
            "weight_bp": self.weight_bp,
            "anchors": list(self.anchors),
        }


@dataclass(frozen=True)
class ReadinessRubric:
    """The criteria, and what their weights are allowed to do.

    `weight_use` is a faculty decision recorded in the seal. "prioritization"
    means the weights order criteria and nothing more. "composite" permits a
    combined figure, and even then only behind a calibration attestation.
    """

    weight_use: str
    status: str
    approved_by: str | None
    criteria: tuple[Criterion, ...]

    def __post_init__(self) -> None:
        if self.weight_use not in WEIGHT_USES:
            raise ValueError(
                f"weight_use must be one of {WEIGHT_USES}, got {self.weight_use!r}"
            )
        if self.status not in RUBRIC_STATUSES:
            raise ValueError(f"rubric status must be one of {RUBRIC_STATUSES}")
        if not self.criteria:
            raise ValueError("a rubric requires at least one criterion")
        keys = [c.key for c in self.criteria]
        if len(set(keys)) != len(keys):
            raise ValueError("duplicate criterion keys")

    def criterion(self, key: str) -> Criterion:
        for candidate in self.criteria:
            if candidate.key == key:
                return candidate
        raise KeyError(key)

    def prioritized(self) -> tuple[Criterion, ...]:
        """Criteria by descending weight; the order a faculty view reads them in."""
        return tuple(sorted(self.criteria, key=lambda c: -c.weight_bp))

    def to_payload(self) -> dict[str, Any]:
        return {
            "weight_use": self.weight_use,
            "status": self.status,
            "approved_by": self.approved_by,
            "criteria": [c.to_payload() for c in self.criteria],
        }


@dataclass(frozen=True)
class TeachingProfile:
    """A parameter set, not a person (proposal p.13).

    Every field changes behavior the studio can show. A parameter that only
    changes a label is the failure the Lovable prototype had, and is not here.
    """

    challenge_intensity: int
    evidence_strictness: int
    evasions_before_reframe: int
    format: str

    def __post_init__(self) -> None:
        _require_int("challenge_intensity", self.challenge_intensity, 0, 100)
        _require_int("evidence_strictness", self.evidence_strictness, 0, 100)
        _require_int("evasions_before_reframe", self.evasions_before_reframe, 1, 3)
        if self.format not in FORMATS:
            raise ValueError(f"format must be one of {FORMATS}, got {self.format!r}")

    @property
    def starting_pressure(self) -> int:
        """0-33 starts at level 1, 34-66 at level 2, 67-100 at level 3."""
        if self.challenge_intensity <= 33:
            return 1
        if self.challenge_intensity <= 66:
            return 2
        return 3

    @property
    def escalates_on_confidence(self) -> bool:
        """Whether confident-without-evidence raises pressure (p.7 rule 2)."""
        return self.evidence_strictness >= 50

    def to_payload(self) -> dict[str, Any]:
        return {
            "challenge_intensity": self.challenge_intensity,
            "evidence_strictness": self.evidence_strictness,
            "evasions_before_reframe": self.evasions_before_reframe,
            "format": self.format,
        }


@dataclass(frozen=True)
class Webscript:
    """A faculty-controlled rehearsal script, sealable once it is finished."""

    webscript_id: str
    version: int
    supersedes: str | None
    course: Mapping[str, str]
    objective: ObjectiveDraft
    dossier: Mapping[str, Any]
    lenses: tuple[Lens, ...]
    states: tuple[State, ...]
    pressure_levels: tuple[PressureLevel, ...]
    questions: tuple[Question, ...]
    event_rules: tuple[EventRule, ...]
    stop_conditions: tuple[StopCondition, ...]
    visibility: Mapping[str, Sequence[str]]
    rubric: ReadinessRubric
    profile: TeachingProfile
    format: str = field(default=FORMAT)

    def __post_init__(self) -> None:
        if self.format != FORMAT:
            raise ValueError(f"unknown Webscript format {self.format!r}")
        if not self.webscript_id.strip():
            raise ValueError("webscript requires an id")
        _require_int("version", self.version, 1, 2**31 - 1)
        if self.supersedes is not None and len(self.supersedes) != 64:
            raise ValueError("supersedes must be the 64-hex seal of a locked version")
        qids = [q.qid for q in self.questions]
        if len(set(qids)) != len(qids):
            raise ValueError("duplicate question ids")
        state_keys = [s.key for s in self.states]
        if len(set(state_keys)) != len(state_keys):
            raise ValueError("duplicate state keys")

    def to_payload(self) -> dict[str, Any]:
        return {
            "format": self.format,
            "webscript_id": self.webscript_id,
            "version": self.version,
            "supersedes": self.supersedes,
            "course": dict(self.course),
            "objective": self.objective.to_payload(),
            "dossier": dict(self.dossier),
            "lenses": [lens.to_payload() for lens in self.lenses],
            "states": [state.to_payload() for state in self.states],
            "pressure_levels": [p.to_payload() for p in self.pressure_levels],
            "questions": [q.to_payload() for q in self.questions],
            "event_rules": [r.to_payload() for r in self.event_rules],
            "stop_conditions": [s.to_payload() for s in self.stop_conditions],
            "visibility": {k: list(v) for k, v in self.visibility.items()},
            "rubric": self.rubric.to_payload(),
            "profile": self.profile.to_payload(),
        }

    @property
    def seal(self) -> str:
        """The hash a session record cites to prove which script it ran."""
        return digest(self.to_payload())

    def lock_blockers(self) -> tuple[tuple[str, str], ...]:
        """Every reason this Webscript cannot be locked yet, in spec order.

        The order and codes are defined in docs/WEBSCRIPT.md, and the studio's
        JavaScript produces the same list for the same payload.
        """
        blockers: list[tuple[str, str]] = []

        for gap in self.objective.gaps():
            blockers.append(("OBJECTIVE_INCOMPLETE", f"objective {gap} is blank"))

        facts = self.dossier.get("facts") or ()
        if not any(isinstance(f, str) and f.strip() for f in facts):
            blockers.append(
                (
                    "DOSSIER_EMPTY",
                    "the dossier has no facts; a rehearsal with no evidence "
                    "pack cannot test evidence",
                )
            )

        lens_keys = {lens.key for lens in self.lenses}
        states = {s.key: s for s in self.states}
        if not self.states or self.states[0].owner != SYSTEM or self.states[-1].owner != SYSTEM:
            blockers.append(
                (
                    "STATES_UNBOUNDED",
                    "the first and last states must be system-owned "
                    "(orientation and debrief); a session must not wander",
                )
            )
        for state in self.states:
            if state.owner != SYSTEM and state.owner not in lens_keys:
                blockers.append(
                    ("STATE_OWNER_UNKNOWN", f"{state.key} is owned by unknown '{state.owner}'")
                )
            if not state.goal.strip() or not state.exit.strip():
                blockers.append(
                    ("STATE_INCOMPLETE", f"{state.key} needs a goal and an exit condition")
                )

        defined = {p.level: p.definition for p in self.pressure_levels}
        for level in PRESSURE_LEVELS:
            if not defined.get(level, "").strip():
                blockers.append(
                    ("PRESSURE_UNDEFINED", f"pressure level {level} has no definition")
                )

        for question in self.questions:
            if question.status == "DRAFT":
                blockers.append(("QUESTION_PENDING", f"{question.qid} awaits faculty approval"))
            elif not (question.approved_by or "").strip():
                blockers.append(
                    ("QUESTION_UNATTRIBUTED", f"{question.qid} is approved by nobody named")
                )
            state = states.get(question.state)
            if state is None or state.owner == SYSTEM or state.owner != question.lens:
                blockers.append(
                    (
                        "QUESTION_MISPLACED",
                        f"{question.qid}: lens '{question.lens}' does not own "
                        f"state '{question.state}'",
                    )
                )
        for state in self.states:
            if state.owner == SYSTEM:
                continue
            if not any(
                q.state == state.key and q.status == "APPROVED" for q in self.questions
            ):
                blockers.append(
                    ("STATE_WITHOUT_QUESTION", f"{state.key} has no approved question")
                )

        rules = {r.event: r for r in self.event_rules}
        for event in MANDATORY_EVENTS:
            rule = rules.get(event)
            if rule is None or not rule.response.strip() or not rule.prompt.strip():
                blockers.append(("EVENT_RULE_MISSING", f"rule '{event}' is missing or blank"))
        for rule in self.event_rules:
            if rule.lens is not None and rule.lens not in lens_keys:
                blockers.append(
                    ("EVENT_LENS_UNKNOWN", f"rule '{rule.event}' names unknown lens '{rule.lens}'")
                )

        stops = {s.key: s.text for s in self.stop_conditions}
        for key in MANDATORY_STOPS:
            if not stops.get(key, "").strip():
                blockers.append(
                    ("STOP_CONDITION_MISSING", f"stop condition '{key}' is missing or blank")
                )

        total = sum(c.weight_bp for c in self.rubric.criteria)
        if total != WEIGHT_TOTAL_BP or any(c.weight_bp <= 0 for c in self.rubric.criteria):
            blockers.append(
                (
                    "RUBRIC_WEIGHTS",
                    f"weights total {total} basis points; they must be positive "
                    f"and total {WEIGHT_TOTAL_BP}",
                )
            )
        for criterion in self.rubric.criteria:
            if any(not anchor.strip() for anchor in criterion.anchors):
                blockers.append(
                    ("RUBRIC_ANCHOR_BLANK", f"{criterion.key} has a blank level anchor")
                )
        if self.rubric.status != "APPROVED" or not (self.rubric.approved_by or "").strip():
            blockers.append(("RUBRIC_PENDING", "the rubric awaits named faculty approval"))

        return tuple(blockers)

    def require_lockable(self) -> SealedObjective:
        """Raise `NotLockable` unless finished; return the sealed objective."""
        blockers = self.lock_blockers()
        if blockers:
            raise NotLockable(blockers)
        return self.objective.sealed()

    def approved_questions(self, state: str) -> tuple[Question, ...]:
        return tuple(
            q for q in self.questions if q.state == state and q.status == "APPROVED"
        )


@dataclass(frozen=True)
class ReadinessObservation:
    """One criterion, observed for one candidate in one session.

    A level must cite evidence; UNDETERMINED must say what is unresolved. A
    blank is neither, and is refused.
    """

    level: int | str
    evidence_ref: str
    rationale: str

    def __post_init__(self) -> None:
        if self.level == UNDETERMINED:
            if not self.rationale.strip():
                raise ValueError(
                    "UNDETERMINED requires a rationale saying what is unresolved"
                )
            return
        _require_int("readiness level", self.level, 0, len(READINESS_LEVELS) - 1)
        if not self.evidence_ref.strip():
            raise ValueError(
                "a readiness level must cite the evidence it rests on; "
                "use UNDETERMINED with a rationale when there is none"
            )

    @property
    def is_undetermined(self) -> bool:
        return self.level == UNDETERMINED

    def to_payload(self) -> dict[str, Any]:
        return {
            "level": self.level,
            "evidence_ref": self.evidence_ref,
            "rationale": self.rationale,
        }


@dataclass(frozen=True)
class ReadinessCard:
    """Every criterion of a rubric, observed or declared undetermined."""

    rubric: ReadinessRubric
    observations: Mapping[str, ReadinessObservation]

    def __post_init__(self) -> None:
        keys = [c.key for c in self.rubric.criteria]
        missing = [k for k in keys if k not in self.observations]
        if missing:
            raise ValueError(
                "silence is prohibited; observe or declare UNDETERMINED for: "
                + ", ".join(missing)
            )
        unknown = set(self.observations) - set(keys)
        if unknown:
            raise ValueError(f"unknown criteria: {', '.join(sorted(unknown))}")

    @property
    def undetermined(self) -> tuple[str, ...]:
        return tuple(
            c.key for c in self.rubric.criteria if self.observations[c.key].is_undetermined
        )

    def to_payload(self) -> dict[str, Any]:
        return {c.key: self.observations[c.key].to_payload() for c in self.rubric.criteria}

    def composite(self, calibration: CalibrationAttestation | None = None) -> int:
        """A combined figure in hundredths of a level, or a refusal.

        Two keys are required: the sealed rubric must declare its weights for
        composite use, and a calibration attestation must name who says the
        levels are comparable across criteria. Undetermined criteria are
        excluded and the remaining weights renormalized, never zeroed.
        """
        if self.rubric.weight_use != "composite":
            raise PrematureCollapse(
                "this rubric declares its weights for prioritization only; "
                "report criterion by criterion. A composite needs a new "
                "Webscript version whose sealed rubric says otherwise."
            )
        if calibration is None:
            raise PrematureCollapse(
                "criteria cannot be combined into one figure before a "
                "calibration attestation says the levels are comparable"
            )
        determined = [
            (self.observations[c.key].level, c.weight_bp)
            for c in self.rubric.criteria
            if not self.observations[c.key].is_undetermined
        ]
        if not determined:
            raise PrematureCollapse("every criterion is undetermined; nothing to combine")
        weight = sum(w for _, w in determined)
        # Floor-rounded integer arithmetic: never more precise than the levels.
        return sum(level * 100 * w for level, w in determined) // weight  # type: ignore[operator]


def load_webscript(payload: Mapping[str, Any]) -> Webscript:
    """Rebuild a Webscript from its canonical payload (inverse of `to_payload`).

    Strict: the rebuilt payload must be byte-identical in canonical form to
    the one given. A field the format does not define would otherwise be
    dropped on load and the seal recomputed without it, so an export carrying
    extra content would report a seal that does not cover that content.
    """
    webscript = _build(payload)
    if canonical_bytes(webscript.to_payload()) != canonical_bytes(payload):
        raise ValueError(
            "payload does not round-trip through the Webscript format: "
            + "; ".join(_differences(payload, webscript.to_payload()))
            + ". A seal computed after dropping fields would not cover them."
        )
    return webscript


def _differences(given: Any, rebuilt: Any, path: str = "$") -> list[str]:
    if isinstance(given, Mapping) and isinstance(rebuilt, Mapping):
        found = [f"{path}.{k} is not part of the format" for k in given if k not in rebuilt]
        found += [f"{path}.{k} is missing" for k in rebuilt if k not in given]
        for key in given:
            if key in rebuilt:
                found += _differences(given[key], rebuilt[key], f"{path}.{key}")
        return found
    if isinstance(given, (list, tuple)) and isinstance(rebuilt, (list, tuple)):
        if len(given) != len(rebuilt):
            return [f"{path} has {len(given)} items, rebuilt {len(rebuilt)}"]
        found: list[str] = []
        for index, (a, b) in enumerate(zip(given, rebuilt)):
            found += _differences(a, b, f"{path}[{index}]")
        return found
    if canonical_bytes(given) != canonical_bytes(rebuilt):
        return [f"{path} changes on rebuild"]
    return []


def _build(payload: Mapping[str, Any]) -> Webscript:
    rubric = payload["rubric"]
    return Webscript(
        format=payload["format"],
        webscript_id=payload["webscript_id"],
        version=payload["version"],
        supersedes=payload.get("supersedes"),
        course=dict(payload["course"]),
        objective=ObjectiveDraft(
            target=payload["objective"]["target"],
            floor=payload["objective"]["floor"],
            must_not_happen=tuple(payload["objective"]["must_not_happen"]),
        ),
        dossier=dict(payload["dossier"]),
        lenses=tuple(Lens(**raw) for raw in payload["lenses"]),
        states=tuple(State(**raw) for raw in payload["states"]),
        pressure_levels=tuple(PressureLevel(**raw) for raw in payload["pressure_levels"]),
        questions=tuple(
            Question(**{**raw, "outcomes": tuple(raw.get("outcomes", ()))})
            for raw in payload["questions"]
        ),
        event_rules=tuple(EventRule(**raw) for raw in payload["event_rules"]),
        stop_conditions=tuple(StopCondition(**raw) for raw in payload["stop_conditions"]),
        visibility={k: tuple(v) for k, v in payload["visibility"].items()},
        rubric=ReadinessRubric(
            weight_use=rubric["weight_use"],
            status=rubric["status"],
            approved_by=rubric.get("approved_by"),
            criteria=tuple(
                Criterion(
                    key=raw["key"],
                    name=raw["name"],
                    evidence=raw["evidence"],
                    weight_bp=raw["weight_bp"],
                    anchors=tuple(raw["anchors"]),
                )
                for raw in rubric["criteria"]
            ),
        ),
        profile=TeachingProfile(**payload["profile"]),
    )


def main(argv: list[str]) -> int:
    """`python3 -m tactik_eval.edu <webscript.json>`: recompute the seal, list blockers.

    Accepts the studio's export, `{"webscript": {...}, "seal": "..."}`, or a bare
    payload. Exit 0 when the Webscript is lockable and any recorded seal matches.
    """
    if len(argv) != 2:
        print("usage: python3 -m tactik_eval.edu <webscript.json>", file=sys.stderr)
        return 2
    with open(argv[1], encoding="utf-8") as handle:
        document = json.load(handle)
    payload = document.get("webscript", document)
    recorded = document.get("seal") if "webscript" in document else None

    webscript = load_webscript(payload)
    seal = webscript.seal
    blockers = webscript.lock_blockers()
    failed = False

    print(f"{webscript.webscript_id} v{webscript.version}")
    print(f"  seal:      {seal}")
    if recorded is not None:
        if recorded == seal:
            print("  recorded:  matches")
        else:
            print(f"  recorded:  {recorded}  MISMATCH", file=sys.stderr)
            failed = True
    if blockers:
        print(f"  lockable:  no, {len(blockers)} blocker(s)")
        for code, detail in blockers:
            print(f"    {code}: {detail}")
        failed = True
    else:
        print("  lockable:  yes")
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
