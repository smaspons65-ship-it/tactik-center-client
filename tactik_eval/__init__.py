"""tactik_eval — the frozen-evaluation substrate for the Santiago Doctrine.

Stdlib only, by design. A reviewer who distrusts us should not have to install
anything of ours to check our arithmetic (P11).

The package enforces, in code, the doctrine rules that are easiest to waive
under pressure:

  P07  a session cannot start without a sealed objective  (casepack)
  P08  a contaminated run gets no score, not a low one    (protocol)
  P09  undetermined is stated; blank is an error          (rubric)
  P10  the record is appended to, never rewritten         (record)
  P11  the hash recipe is reimplementable from prose      (canonical, verify/)

  evaluation doctrine
       dimensions do not collapse into one number         (rubric)
       a protocol does not grade itself as validation     (protocol)
"""

from .canonical import CanonicalizationError, canonical_bytes, digest
from .casepack import (
    Case,
    CasePack,
    CorrectBehavior,
    CoverageError,
    SealBroken,
    SealedObjective,
    load_pack,
)
from .protocol import (
    NO_SCORE,
    BlindingAttestation,
    Breach,
    ContaminatedRun,
    Run,
    RunConditions,
    SelfGraded,
)
from .record import Entry, Ledger, LedgerTampered, Reissued
from .rubric import (
    DIMENSIONS,
    UNDETERMINED,
    BlankScore,
    CalibrationAttestation,
    DimensionScore,
    PrematureCollapse,
    Scorecard,
)

__version__ = "0.1.0"

__all__ = [
    "canonical_bytes",
    "digest",
    "CanonicalizationError",
    "SealedObjective",
    "Case",
    "CasePack",
    "CorrectBehavior",
    "SealBroken",
    "CoverageError",
    "load_pack",
    "DIMENSIONS",
    "UNDETERMINED",
    "DimensionScore",
    "Scorecard",
    "CalibrationAttestation",
    "PrematureCollapse",
    "BlankScore",
    "RunConditions",
    "BlindingAttestation",
    "Breach",
    "Run",
    "ContaminatedRun",
    "SelfGraded",
    "NO_SCORE",
    "Entry",
    "Ledger",
    "LedgerTampered",
    "Reissued",
    "__version__",
]
