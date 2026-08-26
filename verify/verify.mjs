#!/usr/bin/env node
// Independent verifier for a tactik_eval ledger.
//
// Doctrine P11: publishing a hash and asking for belief is theater. This is the
// second of the two implementations of the hash recipe, written against the
// prose in docs/HASHING.md. It shares no code with the Python package on
// purpose — two implementations that agree are evidence, and one implementation
// called twice is not.
//
// Node >= 18, no dependencies.
//
//   node verify/verify.mjs <ledger.json>
//
// Exit 0: the chain recomputes and the head matches.
// Exit 1: it does not, and the output says where.

import { createHash } from "node:crypto";
import { readFileSync } from "node:fs";

const GENESIS = "0".repeat(64);

/**
 * Canonical form, per docs/HASHING.md: keys sorted by code unit, no
 * insignificant whitespace, UTF-8, non-ASCII left as-is, floats rejected.
 */
function canonical(value, path = "$") {
  if (value === null) return "null";

  const type = typeof value;

  if (type === "boolean") return value ? "true" : "false";

  if (type === "number") {
    if (!Number.isInteger(value)) {
      throw new Error(
        `${path}: float values are not hashable in this record; ` +
          `use an integer or a decimal string`,
      );
    }
    if (!Number.isSafeInteger(value)) {
      throw new Error(`${path}: integer ${value} exceeds exact range`);
    }
    return String(value);
  }

  // JSON string escaping is identical in both implementations: quotes and
  // backslashes escaped, control characters as \uXXXX, everything else raw.
  if (type === "string") return JSON.stringify(value);

  if (Array.isArray(value)) {
    const items = value.map((item, i) => canonical(item, `${path}[${i}]`));
    return `[${items.join(",")}]`;
  }

  if (type === "object") {
    // Sorted by JS default string comparison, which orders by UTF-16 code
    // unit — the same order Python's sort_keys produces for the ASCII keys
    // this record uses.
    const keys = Object.keys(value).sort();
    const pairs = keys.map(
      (key) => `${JSON.stringify(key)}:${canonical(value[key], `${path}.${key}`)}`,
    );
    return `{${pairs.join(",")}}`;
  }

  throw new Error(`${path}: ${type} is not serializable`);
}

function digest(value) {
  return createHash("sha256").update(canonical(value), "utf8").digest("hex");
}

function linkOf(entry) {
  return digest({
    index: entry.index,
    kind: entry.kind,
    body: entry.body,
    previous: entry.previous,
  });
}

function contentHashOf(entry) {
  return digest({ kind: entry.kind, body: entry.body });
}

function verify(ledger) {
  const problems = [];
  const entries = ledger.entries ?? [];
  let previous = GENESIS;

  entries.forEach((entry, position) => {
    if (entry.index !== position) {
      problems.push(
        `entry at position ${position} claims index ${entry.index}`,
      );
    }
    if (entry.previous !== previous) {
      problems.push(
        `entry ${position} breaks the chain:\n` +
          `    expects predecessor ${previous}\n` +
          `    records predecessor ${entry.previous}`,
      );
    }
    const recomputed = linkOf(entry);
    if (entry.link !== recomputed) {
      problems.push(
        `entry ${position} link mismatch:\n` +
          `    recorded   ${entry.link}\n` +
          `    recomputed ${recomputed}`,
      );
    }
    previous = recomputed;
  });

  if ((ledger.head ?? GENESIS) !== previous) {
    problems.push(
      `head mismatch:\n` +
        `    recorded   ${ledger.head}\n` +
        `    recomputed ${previous}`,
    );
  }

  return { problems, head: previous, entries };
}

function main() {
  const path = process.argv[2];
  if (!path) {
    console.error("usage: node verify/verify.mjs <ledger.json>");
    process.exit(2);
  }

  const ledger = JSON.parse(readFileSync(path, "utf8"));
  const { problems, head, entries } = verify(ledger);

  const withdrawn = new Set(
    entries
      .filter((entry) => entry.kind === "withdrawal")
      .map((entry) => entry.body.withdraws_content_hash),
  );
  const standing = entries.filter(
    (entry) => entry.kind !== "withdrawal" && !withdrawn.has(contentHashOf(entry)),
  );

  if (problems.length > 0) {
    console.error(`FAIL  ${path}`);
    for (const problem of problems) console.error(`  - ${problem}`);
    process.exit(1);
  }

  console.log(`OK    ${path}`);
  console.log(`  entries:   ${entries.length}`);
  console.log(`  standing:  ${standing.length}`);
  console.log(`  withdrawn: ${withdrawn.size}`);
  console.log(`  head:      ${head}`);
}

main();
