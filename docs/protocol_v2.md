# Study extension: structure constraints and public data

Design date: 20 November 2026. This extension follows inspection of the original
pilot. It is not an independent preregistration. Commit history freezes this plan,
the prompts, the schema and the new task manifest before the first study call.
All original results remain unchanged.

## Questions and design

The original pilot confounds arithmetic failure with output-contract failure.
This extension asks whether enforcing JSON structure changes complete-report
correctness, and whether executable feedback helps after that constraint.

- Models: local Qwen2.5 1.5B and 3B, with exact downloaded digests recorded.
- Tasks: 12 previously uncalled synthetic tasks (variants 06 and 07, two per
  operation) and 12 public-data tasks (two per operation).
- Public observations: World Bank World Development Indicators, population and
  urban population, two fixed disjoint country cohorts and two 2013–2024 series.
  Cross-sectional observations use 2024. Freeze source responses and SHA-256s.
- Generation factors: JSON mode and JSON-Schema-constrained mode. Both receive
  the same system prompt and schema text. Only the API `format` value differs.
- Conditions within each format: initial, one self-review call, one executable-
  feedback call. Both second calls start from the same initial answer.
- Budget: 24 tasks × 2 formats × 3 calls × 2 models = **288 new calls**.
  Temperature 0, seed 31415, context 4096, maximum 512 generated tokens per call.
  No content retry, best-of selection or prompt changes after inspecting outputs.
- Counterbalance format order and second-call branch order by task index.

The schema constrains field presence and types. It contains no computed answer,
correct unit, row count, metric-key enumeration or chart-value reference. Schema
compliance cannot establish arithmetic or cross-field consistency.

## Outcomes

The primary outcome requires schema compliance and correct metric labels/values,
unit, valid-row count and chart data against the independent SQLite oracle.
Narrative meaning is outside scope. Separately report schema validity, exact
numeric mappings, each checked field, truncations, latency and token counts.

Report paired changes between formats and between review branches. Give raw
paired counts, Wilson intervals and an exact two-sided McNemar test on discordant
pairs. These are descriptive analyses of a small constructed task set, with no
population-wide claim or correction of the original negative outcome.

Report synthetic and public-data strata separately. Operations reuse country
cohorts, and public tasks share one source; 24 tasks are not 24 independent domains.
The country cohorts are curated for coverage, not representative samples. Population
estimates and national urban definitions introduce measurement limitations.

## Evidence and execution

Store every request and response, model digest, request hash, dataset hash, prompt
hash, schema hash, protocol hash and frozen code commit. Operational failures stop
the run and are not counted as model failures. Reuse a completed call only when
its request, model digest and protocol hash match. A new run uses a new directory.

The production checker never reads gold answers. Deterministic recomputation is
reported separately as ordinary software execution. No generated code executes.
The dataset loader and oracle use independent logic; hand checks and metamorphic
tests supplement implementation agreement.

## Completion and interpretation

Publish all conditions, including failures. Do not revise success criteria to
obtain a higher score. Update the report, presentation and evidence map only from
saved results. Recent related work informs the design, but this small study does
not reproduce or compete with those papers' benchmark scores.
