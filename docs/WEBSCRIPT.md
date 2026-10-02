# The Webscript

This document is the specification. `tactik_eval/edu.py` and the core script in
`studio/faculty.html` are two implementations of it, and either may be wrong;
this prose is what both are answerable to. Hashing follows `docs/HASHING.md`
exactly: no floats anywhere, integers within ±(2^53 − 1).

A Webscript is the faculty-controlled rehearsal script the Westcliff pilot
proposal describes (pp.13, 17–19, 21): a learning objective, a fictional or
approved dossier, committee lenses, controlled states, a question bank, event
rules, stop conditions, visibility rules, a readiness rubric and a teaching
profile. Faculty approve it and version-lock it before any candidate sees it.
The lock is a SHA-256 seal over the canonical form of the payload below.

## Payload, format `tactik-edu/webscript@1`

```
format            "tactik-edu/webscript@1"
webscript_id      string, non-empty
version           integer ≥ 1
supersedes        null, or the 64-hex seal of the locked version this replaces
course            object of strings (code, title, institution, program, syllabus_seal);
                  syllabus_seal is the digest of the syllabus the script was built from
objective         {target, floor, must_not_happen: [string]}
dossier           object (title, design, domain, facts: [string]); design
                  "cross-sectional" enables the causal-language trigger, domain
                  "business" the projection trigger, domain "law" the conclusory one
lenses            [{key, name, job, primary_lens, boundary}]   key ≠ "system"
states            [{key, name, owner, goal, exit}]   owner is "system" or a lens key
pressure_levels   [{level: 1|2|3, definition}]
questions         [{qid, state, lens, pressure: 1|2|3, text,
                    status: "DRAFT"|"APPROVED", approved_by: string|null,
                    outcomes: [syllabus outcome ids]}]
event_rules       [{event, response, prompt, lens: string|null}]
                  response is the instruction faculty approve; prompt is the exact
                  text the candidate sees; lens is who says it (null: the owner of
                  the current state)
stop_conditions   [{key, text}]
visibility        {student: [string], faculty: [string]}
rubric            {weight_use: "prioritization"|"composite",
                   status: "DRAFT"|"APPROVED", approved_by: string|null,
                   criteria: [{key, name, evidence, weight_bp, anchors: [4 strings]}]}
profile           {challenge_intensity: 0..100, evidence_strictness: 0..100,
                   evasions_before_reframe: 1..3,
                   format: "cold_call"|"seminar"|"presentation"}
```

A payload is loaded strictly: a field this format does not define is refused,
never dropped, because a seal recomputed without it would not cover it.

Weights are basis points: 15% is `1500`. Readiness levels are integers 0–3, one
anchor each. Who locked the script and when are recorded in the ledger entry
that carries the seal, never inside the sealed payload. A seal that changed
whenever someone looked at it would prove nothing.

## Lock gates

A draft may be incomplete. Locking requires an empty blocker list. Both
implementations produce blockers with these codes, in this order:

1. `OBJECTIVE_INCOMPLETE`, once per blank field among target, floor and
   must_not_happen. must_not_happen is blank when it has no non-blank clause.
2. `DOSSIER_EMPTY`, once, if `dossier.facts` has no non-blank string. A
   rehearsal with no evidence pack cannot test evidence.
3. `STATES_UNBOUNDED`, once, if there are no states or the first or last state
   is not system-owned. Orientation and debrief bound the session; without them
   it can wander into open-ended tutoring (proposal p.8).
4. Per state in order: `STATE_OWNER_UNKNOWN` if the owner is neither "system"
   nor a lens key, then `STATE_INCOMPLETE` if goal or exit is blank.
5. `PRESSURE_UNDEFINED`, once per level 1, 2, 3 with no non-blank definition.
   The proposal names three levels and never defines them; that is faculty
   content.
6. Per question in order: `QUESTION_PENDING` if DRAFT, or
   `QUESTION_UNATTRIBUTED` if APPROVED with a blank or null approver; then
   `QUESTION_MISPLACED` if its state does not exist, is system-owned, or is
   owned by a different lens.
7. Per lens-owned state in order: `STATE_WITHOUT_QUESTION` if no APPROVED
   question belongs to it.
8. Per mandatory event in order: `EVENT_RULE_MISSING` if absent, or if its
   response or its prompt is blank.
   Mandatory events (proposal p.7): `unsupported_claim`,
   `high_confidence_low_evidence`, `self_correction`, `evasion_repeat`,
   `answer_request`.
9. Per rule in order: `EVENT_LENS_UNKNOWN` if its lens is not null and is
   not a lens key.
10. Per mandatory stop condition in order: `STOP_CONDITION_MISSING` if absent or
   blank. Mandatory stop conditions (proposal p.18):
   `participant_requests_stop`, `restricted_information`,
   `departs_from_approved_scope`, `generates_student_work`, `faculty_concern`.
11. `RUBRIC_WEIGHTS`, once, unless every weight is positive and they total 10000.
12. Per criterion in order: `RUBRIC_ANCHOR_BLANK` if any anchor is blank.
13. `RUBRIC_PENDING`, once, unless the rubric is APPROVED by a named approver.

Faculty may reword any rule or condition and may add more. They may not remove
a mandatory one. `answer_request` is the refusal to write the candidate's work;
a Webscript without it is not this product.

## What the weights may do

`weight_use` is sealed with everything else. With `"prioritization"` the
weights order criteria in the faculty view and do nothing more, and every
request for a combined figure is refused. With `"composite"` a combined figure
is still refused unless a calibration attestation (method, named attester,
reference runs) is supplied. The figure is an integer in hundredths of a level,
floor-rounded, with undetermined criteria excluded and the remaining weights
renormalized. The proposal says "never a single academic grade" (p.8); this is
how that sentence survives a deadline.

## Teaching profile, and what each field changes

Every field changes behavior, and the studio shows which:

- `challenge_intensity`: the starting pressure level. 0–33 starts at level 1,
  34–66 at level 2, 67–100 at level 3.
- `evidence_strictness`: at 50 or above, a confident claim without cited
  evidence raises pressure one level (p.7 rule 2). Below 50 it does not.
- `evasions_before_reframe`: the number of evasions or repetitions before the
  question is reframed once and the objection recorded as open (p.7 rule 4).
- `format`: recorded and sealed. The studio's preview does not yet change
  anything on it, and says so.

## The engine

A candidate rehearses only against a locked Webscript. The engine is a state
machine over the script's states. It never writes what the candidate sees.
Every line shown to a candidate is an approved question, an approved rule
prompt, or one of the engine's fixed system lines.

- **Opening question of a state**: the highest-level approved question at or
  below the current pressure, ties in bank order; if none is that low, the
  lowest-level approved question. **Follow-ups**: the next unused approved
  question in bank order.
- **Classification**: each candidate turn is labelled with events, either by
  the disclosed rules in the page or, when the viewer turns it on, by Claude.
  Claude returns event names only. Anything that is not an event this script
  defines is discarded, and Claude's text is never shown to the candidate. If
  Claude is unavailable, the rules classify that turn and the trace says so.
- **A turn with no event** meets the state's exit, and the engine moves on.
  **A self-correction** keeps both versions, pairing the restatement with the
  most recent challenged claim, then tests the revision with a follow-up.
  **Evasions** up to the profile's threshold re-ask the question; at the
  threshold the question is reframed, the objection is recorded as open, and
  the engine moves on. **Three challenged turns** in one state also leave the
  objection open and move on. **A request for an answer** is declined and the
  question re-asked. When a turn both restates a claim and contains domain
  wording (causal, projection, conclusory), the restatement rule wins.
- **The debrief** lists what was defended, what was revised (both versions),
  what is still open, and next preparation actions. It contains no grade.

## Ledger entries the studio writes

The studio appends to a `tactik_eval`-compatible ledger (`docs/HASHING.md`), so
`node verify/verify.mjs` and `python3 -m tactik_eval.verify` both check it.
Candidate and rater text never enters an entry body. A body carries only
references (`content_ref` for a candidate turn, `note_ref` for a rater's
evidence note, `reason_ref` for an override's reason, `original_ref` and
`revised_ref` for a preserved claim), each the digest of
`{"salt": <32 hex>, "text": <text>}`. The text and salt live in a separate
content store. Erasing them honors a deletion decision (proposal
p.17). The chain still verifies, and the text cannot be recovered from the
hash. The erasure is itself appended (`content_erased`).

Kinds: `fixture_loaded`, `syllabus_imported`, `webscript_drafted`,
`question_approved`, `question_rejected`, `rubric_approved`, `webscript_locked`,
`trigger_reviewed`, `classifier_compared`, `dry_run_reviewed`, `session_opened`,
`session_events`, `turn_recorded`, `claim_preserved`, `objection_opened`,
`pressure_raised`, `observation_recorded`,
`observation_overridden`, `session_paused`, `session_resumed`,
`session_completed`, `session_stopped`, `charter_event`, `teaching_action`,
`content_erased`. An override never edits the observation it disagrees with: it
is a new entry naming the content hash it supersedes, so rater and faculty
disagreement stays in the record (proposal p.19). A stopped session's result is
`NO_SCORE`; its observations are excluded from every count, never zeroed. The studio never writes `withdrawal`, which `tactik_eval`
reserves.
