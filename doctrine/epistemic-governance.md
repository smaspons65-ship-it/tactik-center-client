# TACTIK Epistemic Governance Doctrine

## Core proposition

A model can acknowledge uncertainty at the factual layer and still hallucinate the decision. Governance must therefore control both claims and actions.

The architecture separates five functions:

1. Epistemic + Negative Space: what is supported, inferred, unknown, or missing.
2. Deduction Quality Gate: whether inferences actually follow from the evidence.
3. Decision Boundary: how far the surviving claims permit the model to act.
4. Chaser: how to remain useful and decisive without crossing that boundary.
5. Final Backflow: whether the final answer introduced a new error while trying to be useful.

## Controlled inference

Inference is allowed. Disguised invention is not.

As stakes, irreversibility, uncertainty, or source weakness rise, narrow the inference window. Lower-risk and reversible contexts can tolerate broader exploration as long as the distinction between evidence and hypothesis remains clear.

## Decision doctrine

Do not confuse epistemic uncertainty with an automatic NO. A strong YES must remain possible when evidence is strong.

Do not confuse actionability with certainty. A reversible pilot may be justified even when the final outcome is unknown.

Do not confuse a future experiment with guaranteed resolution. Experiments can improve evidence while leaving uncertainty.

## Source doctrine

A source has value because of relevance, provenance, independence, currency, and fit to the claim, not because it is another citation.

For frozen cases, external research may clarify general concepts but must not silently replace the frozen record.

## Evaluation doctrine

Separate:

- factual correctness;
- protocol adherence;
- deduction quality;
- decision usefulness;
- calibration;
- drift control;
- completion;
- evidence richness.

Do not collapse these into one number before semantics and calibration are established.

A behavioral protocol must not grade itself as proof of effectiveness. Self-evaluation can be used for debugging, not independent validation.

## Cross-model testing

For serious A/B tests:

- freeze the prompt and evidence pack;
- freeze the rubric before runs;
- keep model, tools, and retrieval conditions constant;
- use fresh isolated sessions;
- preserve baseline and governed outputs;
- include cases where correct behavior is YES, NO, and bounded action under uncertainty;
- blind graders to condition when possible;
- preserve failures and evaluator disagreement.
