# Project description

**TrustVerify: Executable Verification of AI-Generated Data Analysis**

BAHODIR KODIRJON UGLI NAZAROV · Software Engineering, Sichuan University

New Software Technology · Dr. Hu Dasha · November 2026

## Problem and research questions

A fluent report can contain an incorrect aggregate, unit, valid-row count or chart.
TrustVerify recomputes selected claims under a human-approved analysis contract.
The investigation asks:

1. Which designed errors are detected by successive checking layers?
2. Does executable feedback improve reports compared with equal-call self-review?
3. Does schema-constrained generation improve complete correctness separately from format compliance?
4. What assurance remains outside the check, including prose, data quality and analysis intent?

## Working system

CSV + approved JSON contract + candidate report → Decimal recomputation → field findings
→ pass, fail or abstain. The six operations are sum, mean, weighted mean, percentage ratio
of sums, grouped sum and first-to-last percentage change. Scalar metrics use key `value`.
A candidate contains `metrics`, `unit`, `rows_used`, `chart` and `narrative`.
No model-generated code is executed, and the verifier never reads evaluator gold files.

A local browser demonstration accepts bundled or custom UTF-8 CSVs and allows direct
editing of candidate reports. Deterministic recomputation is separate from model repair.
A downloadable receipt records hashes, contract, report, engine and verdict. Replay checks
the exact input and repeats the computation. Hashes are not signatures or authorship proof.
The complete example in `demo/receipt-example/` records 18 versus the correct 17.5 weighted
mean; replay succeeds while reproducing a failed verdict.

## Evidence collected

| Study | Size and purpose |
|---|---|
| Controlled coverage | 48 clean reports and 336 faults across seven mutation classes; checker ablations |
| Original model pilot | 24 synthetic tasks/model; Qwen2.5 0.5B and 1.5B; 144 actual calls |
| Paired extension | 24 new tasks, half public World Bank data; 1.5B; JSON/schema formats × initial/review/feedback; 144 actual calls |
| Deterministic baseline | Agreement with independent SQLite on all 60 synthetic and 12 public tasks |

Full checking detects 288/288 supported structured mutations and misses all 48 narrative
mutations, with 0/48 clean false alarms. The extension gives initial schema validity of
20/24 in JSON mode and 23/24 with schema constraints. Feedback repairs 19/24 and 18/24
numeric mappings respectively, yet complete correctness stays 0/24 in every condition.
Only 1/24 feedback charts agrees in either format. All failures and truncations remain scored.

The extension planned a second, 3B capacity; acquisition did not complete. Its scope was
reduced after 1.5B results were available, as recorded in `extension_execution_note.md`.
No 3B experiment or general model-capacity conclusion is claimed.

## Contribution and limits

The contribution is the inspectable software, independent oracle, field-level diagnosis,
paired format study and replayable verification evidence. External tool feedback is an
established idea; this project does not claim a new model or a universal truth detector.
Numeric agreement uses absolute/relative tolerance 1e-6. A pass excludes narrative meaning,
rendered-chart geometry, data accuracy and the scientific appropriateness of the contract.

## Delivered artifacts

The repository contains the source, 33 tests, public-data snapshot and provenance, all 288
raw model calls, English SCU-format LaTeX/PDF report, 22-slide editable presentation,
fixed-layout slides, literature review, protocols, result checkers and demonstration guide.
