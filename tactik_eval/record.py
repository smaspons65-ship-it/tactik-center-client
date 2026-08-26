"""The append-only record.

Doctrine P10: when a published number turns out to be wrong, the old figure is
withdrawn in public, preserved as withdrawn, and never reissued. The record
grows; it never gets rewritten.

This class therefore has no update and no delete. Not "has them but discourages
them" — a record whose author can improve it after the fact proves nothing, and
everybody knowledgeable knows it. Entries are chained so that a rewrite is
detectable by anyone holding a later hash.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterator, Sequence

from .canonical import digest

__all__ = ["Entry", "Ledger", "LedgerTampered", "Reissued"]

#: The chain's anchor. Chosen so the first entry's link is well defined rather
#: than special-cased.
GENESIS = "0" * 64


class LedgerTampered(Exception):
    """A ledger's recomputed chain does not match its recorded hashes."""


class Reissued(Exception):
    """A withdrawn figure was published again."""


@dataclass(frozen=True)
class Entry:
    """One immutable line in the record."""

    index: int
    kind: str
    body: dict[str, Any]
    previous: str

    @property
    def content_hash(self) -> str:
        """Hash of what this entry says, independent of where it sits."""
        return digest({"kind": self.kind, "body": self.body})

    @property
    def link(self) -> str:
        """Hash of this entry including its position and predecessor."""
        return digest(
            {
                "index": self.index,
                "kind": self.kind,
                "body": self.body,
                "previous": self.previous,
            }
        )

    def to_payload(self) -> dict[str, Any]:
        return {
            "index": self.index,
            "kind": self.kind,
            "body": self.body,
            "previous": self.previous,
            "link": self.link,
        }


class Ledger:
    """An append-only, hash-chained sequence of entries."""

    def __init__(self) -> None:
        self._entries: list[Entry] = []
        self._withdrawn: set[str] = set()

    def __len__(self) -> int:
        return len(self._entries)

    def __iter__(self) -> Iterator[Entry]:
        return iter(self._entries)

    @property
    def entries(self) -> Sequence[Entry]:
        return tuple(self._entries)

    @property
    def head(self) -> str:
        """The hash that summarizes the whole record so far.

        Publish this. Anyone who kept an earlier head can prove the history
        under it never changed.
        """
        return self._entries[-1].link if self._entries else GENESIS

    def append(self, kind: str, body: dict[str, Any]) -> Entry:
        """Add an entry. The only way content enters the record."""
        if not kind.strip():
            raise ValueError("an entry requires a kind")
        entry = Entry(
            index=len(self._entries), kind=kind, body=body, previous=self.head
        )
        if entry.content_hash in self._withdrawn:
            raise Reissued(
                f"this content was withdrawn as {entry.content_hash[:12]}… and "
                "cannot be republished. Correct by addition: publish the new "
                "figure as a new entry that says what it supersedes."
            )
        self._entries.append(entry)
        return entry

    def withdraw(self, index: int, reason: str, withdrawn_by: str) -> Entry:
        """Withdraw an earlier entry by appending a withdrawal.

        The original stays exactly where it was and says exactly what it said.
        The withdrawal is what the record grows by.
        """
        if not reason.strip():
            raise ValueError("a withdrawal must state its reason in public")
        if not withdrawn_by.strip():
            raise ValueError("a withdrawal must name who made it")
        try:
            target = self._entries[index]
        except IndexError:
            raise KeyError(f"no entry at index {index}") from None
        if target.kind == "withdrawal":
            raise ValueError("a withdrawal cannot itself be withdrawn")
        if target.content_hash in self._withdrawn:
            raise ValueError(f"entry {index} is already withdrawn")

        withdrawal = self.append(
            "withdrawal",
            {
                "withdraws_index": index,
                "withdraws_content_hash": target.content_hash,
                "reason": reason,
                "withdrawn_by": withdrawn_by,
            },
        )
        self._withdrawn.add(target.content_hash)
        return withdrawal

    def is_withdrawn(self, entry: Entry) -> bool:
        return entry.content_hash in self._withdrawn

    def standing(self) -> tuple[Entry, ...]:
        """Entries that still stand: not withdrawn, not withdrawals themselves.

        Withdrawn entries remain readable through `entries`. They are excluded
        here, never deleted.
        """
        return tuple(
            entry
            for entry in self._entries
            if entry.kind != "withdrawal" and not self.is_withdrawn(entry)
        )

    def verify_chain(self) -> None:
        """Recompute every link. Raise on the first that does not match."""
        previous = GENESIS
        for position, entry in enumerate(self._entries):
            if entry.index != position:
                raise LedgerTampered(
                    f"entry at position {position} claims index {entry.index}"
                )
            if entry.previous != previous:
                raise LedgerTampered(
                    f"entry {position} breaks the chain:\n"
                    f"  expects predecessor {previous}\n"
                    f"  records predecessor {entry.previous}"
                )
            previous = entry.link

    def to_payload(self) -> dict[str, Any]:
        return {
            "head": self.head,
            "entries": [entry.to_payload() for entry in self._entries],
        }

    @classmethod
    def from_payload(cls, payload: dict[str, Any]) -> "Ledger":
        """Rebuild and immediately verify a ledger read from disk."""
        ledger = cls()
        for raw in payload["entries"]:
            entry = Entry(
                index=raw["index"],
                kind=raw["kind"],
                body=raw["body"],
                previous=raw["previous"],
            )
            # The stored link is redundant with the entry's content, which is
            # exactly why it is worth checking: a body edited after the fact
            # disagrees with the link written beside it.
            recorded_link = raw.get("link")
            if recorded_link is not None and recorded_link != entry.link:
                raise LedgerTampered(
                    f"entry {raw['index']} link mismatch:\n"
                    f"  recorded   {recorded_link}\n"
                    f"  recomputed {entry.link}"
                )
            ledger._entries.append(entry)
        ledger.verify_chain()
        for entry in ledger._entries:
            if entry.kind == "withdrawal":
                ledger._withdrawn.add(entry.body["withdraws_content_hash"])
        if ledger.head != payload["head"]:
            raise LedgerTampered(
                f"recorded head {payload['head']} does not match recomputed "
                f"{ledger.head}"
            )
        return ledger
