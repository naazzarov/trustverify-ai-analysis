# Dataset card: TrustVerify synthetic analytics v1

## Composition and licence

60 independently seeded CSV files, 12 observations each. Columns: x (numeric observation),
n (weight or denominator), g (group A, B or C). Two x values and one n value are missing
per dataset. Synthetic values have no real-world evidential meaning. They contain no
personal records. The generated dataset is distributed under this repository's AGPL-3.0 licence.

## Tasks and evaluation split

Six operation families with ten variants each. Variants 00 and 01 are development.
Variants 02–09 are test. The model pilot uses variants 02–05, four per family (24 total).
Task prompts explicitly define missingness, units, ordering and the aggregate.
data/tasks.jsonl records the contract, split and SHA-256 of every CSV.
data/gold.json holds evaluation-only SQLite results; it is never passed to model calls.

## Error design

For every test dataset, create a clean structured report and seven single mutations.
Numeric: add 3.25 to one metric. Unit: swap to an incorrect string. Rows: add one.
Chart: add five to one plotted value. Missing field: remove chart. Nonfinite: replace
one metric with the string NaN. Narrative: insert an unsupported causal assertion.
The narrative mutation is intentionally outside checker coverage. Report mutation results
as controlled sensitivity, never as a distribution of naturally occurring LLM mistakes.

## Evaluation assumptions

All duplicate records would count as separate observations; deduplication is not inferred.
Complete cases are operation-specific. Weights must be nonnegative and have positive total.
Ratios with zero aggregate denominator and change from zero abstain. Units are supplied by
the approved contract; the verifier does not discover dimensions from column names.
Numeric tolerance: absolute 1e-6 or relative 1e-6. Differences below it are not detected.

## Limitations

The task generator is narrow, templated, small, and synthetic. Dataset-level separation does
not imply new task-family generalization. Six mutation classes directly match six designed
checks, so high detection is an expected coverage result. Actual model tests and blind-spot
examples are included to avoid interpreting designed coverage as universal reliability.

## Public-data extension (November 2026)

Twelve tasks derive from a frozen World Bank WDI population/urban-population snapshot.
They use two curated 12-country cohorts for 2024 cross-sections and Uzbekistan/Japan
2013–2024 series for percentage change. These are observational source estimates, not
synthetic values; the task templates remain curated and small. Raw bulk ZIPs, normalized
responses, exact source URLs, dates, SHA-256 hashes, derived-variable rules and CC BY 4.0
attribution are in [data/public/README.md](../data/public/README.md).

The paired extension uses 12 previously unused synthetic tasks (variants 06–07) plus all
12 public tasks. Its realized 144 calls, output-schema rules, counterbalancing, strict
request reuse and scope reduction are documented in protocol_v2.md and
extension_execution_note.md. The original 12/48 split and pilot evidence remain unchanged.
