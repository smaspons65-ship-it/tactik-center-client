# The hash recipe

This document is the specification. `tactik_eval/canonical.py` and
`verify/verify.mjs` are two implementations of it, and either may be wrong; the
prose is what they are both answerable to.

The purpose is Principle 11. A reviewer who has none of our software, none of
our goodwill, and no access to our systems must be able to arrive at the same
hashes we published — or catch us. Both outcomes are fine. Only the third,
where nobody can check, is not.

## Canonical form

To hash a value, first render it to exactly one byte sequence:

1. **Objects.** Serialize as `{"key":value,...}` with keys sorted ascending by
   Unicode code point, no space after `:` or `,`. Keys must be strings.
2. **Arrays.** Serialize as `[value,...]`, no space after `,`, order preserved.
   Array order is significant and is never normalized.
3. **Strings.** Standard JSON escaping: `"` and `\` escaped, control characters
   below U+0020 as `\uXXXX` lowercase-hex. Every other character is emitted
   literally as UTF-8 — non-ASCII text is **not** escaped to `\uXXXX`.
4. **Integers.** Base-ten, no leading zeros, no `+`, `-0` normalized to `0`.
5. **Booleans and null.** `true`, `false`, `null`.
6. **Floats are rejected.** See below.
7. Encode the finished text as UTF-8.

Then take **SHA-256** of those bytes and render it as **lowercase hex**.

## Why floats are refused

Two languages do not always agree on the shortest representation that
round-trips a given IEEE-754 double, and JSON has no canonical float form. A
recipe with that ambiguity in it fails open: the hashes agree on almost every
input and diverge on rare ones, which is the worst available failure mode
because it looks like correctness until it matters.

So the record carries no floats. Quantities are integers (bands are `0`–`100`,
money is minor units) or decimal strings (`"1250.75"`) that the reader parses
after verification rather than before. Implementations must raise rather than
coerce.

Integers must also be exactly representable by any conforming implementation.
The JavaScript verifier rejects anything outside ±(2^53 − 1); do not put larger
numbers in the record.

## The two hashes on an entry

Each ledger entry has two, and they answer different questions.

**`content_hash`** — over `{"kind":…,"body":…}` only. It identifies *what an
entry says*, independent of where it sits. Withdrawals reference this, which is
what makes "withdrawn and never reissued" enforceable: the same content
appended again at a later index is still recognizably the same claim.

**`link`** — over `{"index":…,"kind":…,"body":…,"previous":…}`. It identifies
*this entry in this position after this predecessor*, chaining the record. The
first entry's `previous` is 64 zeros.

The ledger's `head` is the last entry's `link`, or 64 zeros when empty. Publish
the head. Anyone holding an earlier head can then prove the history beneath it
never changed — which is the whole point of appending rather than editing.

## Checking a published record

```
node verify/verify.mjs ledger.json      # second implementation, no dependencies
python3 -m tactik_eval.verify ledger.json
```

Disagreement between the two is a finding about us, and should be reported as
one. Neither implementation is authoritative over the other; this document is.
