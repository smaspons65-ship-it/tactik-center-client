"""Verify a published ledger: `python3 -m tactik_eval.verify <ledger.json>`.

The Python half of the two-implementation check. Run `verify/verify.mjs` over
the same file; the two must agree, and a disagreement is a finding about us
rather than about the file.
"""

from __future__ import annotations

import json
import sys

from .record import Ledger, LedgerTampered


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("usage: python3 -m tactik_eval.verify <ledger.json>", file=sys.stderr)
        return 2

    path = argv[1]
    with open(path, encoding="utf-8") as handle:
        payload = json.load(handle)

    try:
        ledger = Ledger.from_payload(payload)
    except LedgerTampered as failure:
        print(f"FAIL  {path}", file=sys.stderr)
        for line in str(failure).splitlines():
            print(f"  {line}", file=sys.stderr)
        return 1

    withdrawn = sum(1 for entry in ledger if ledger.is_withdrawn(entry))
    print(f"OK    {path}")
    print(f"  entries:   {len(ledger)}")
    print(f"  standing:  {len(ledger.standing())}")
    print(f"  withdrawn: {withdrawn}")
    print(f"  head:      {ledger.head}")
    return 0


def console_main() -> int:
    """Entry point for the `tactik-verify` script, which receives no argv."""
    return main(sys.argv)


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
