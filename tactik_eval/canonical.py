"""Canonical serialization and hashing.

Every freeze, seal and ledger hash in this package reduces to `digest()`. The
recipe is deliberately small so that it can be reimplemented from the prose in
docs/HASHING.md by someone who has none of this software (Doctrine, P11).

Floats are rejected rather than serialized. IEEE-754 shortest-repr differs
across languages at the margins, and a hash recipe that two implementations
disagree about is worse than no hash at all: it fails open, quietly. Quantities
belong in the record as integers or as decimal strings.
"""

from __future__ import annotations

import hashlib
import json
from typing import Any

__all__ = ["canonical_bytes", "digest", "CanonicalizationError"]


class CanonicalizationError(TypeError):
    """A payload contains something that cannot be hashed reproducibly."""


_ALLOWED_SCALARS = (str, bool, int, type(None))


def _check(value: Any, path: str = "$") -> None:
    """Reject anything whose serialization is not identical across languages."""
    if isinstance(value, float):
        raise CanonicalizationError(
            f"{path}: float values are not hashable in this record. "
            "Use an integer or a decimal string."
        )
    # bool is a subclass of int; both are fine, and the isinstance order in
    # _ALLOWED_SCALARS does not matter because we only test membership.
    if isinstance(value, _ALLOWED_SCALARS):
        return
    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise CanonicalizationError(
                    f"{path}: object keys must be strings, got {type(key).__name__}"
                )
            _check(item, f"{path}.{key}")
        return
    if isinstance(value, (list, tuple)):
        for index, item in enumerate(value):
            _check(item, f"{path}[{index}]")
        return
    raise CanonicalizationError(f"{path}: {type(value).__name__} is not serializable")


def canonical_bytes(payload: Any) -> bytes:
    """Serialize `payload` to the one byte sequence both implementations agree on.

    Keys sorted, no insignificant whitespace, UTF-8, non-ASCII left as-is.
    """
    _check(payload)
    text = json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
        allow_nan=False,
    )
    return text.encode("utf-8")


def digest(payload: Any) -> str:
    """Return the lowercase hex SHA-256 of the canonical form of `payload`."""
    return hashlib.sha256(canonical_bytes(payload)).hexdigest()
