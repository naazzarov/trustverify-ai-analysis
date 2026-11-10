# Experimental protocol v1

Author: BAHODIR KODIRJON UGLI NAZAROV. Design date: 10 November 2026.

## Scope and hypotheses

The prototype verifies structured descriptive statistics under a **human-approved contract**.
It does not infer the intended analysis, prove causal claims, or certify an entire report.
H1: independent execution detects more supported errors than numeric checking alone.
H2: feedback from execution improves a small local model's structured accuracy compared with
an equal-call-budget self-review baseline. H2 can fail; preserve the observed result.

## Frozen data design

Six operations: sum, mean, weighted mean, ratio of sums expressed as percent, group sums,
and first-to-last percent change. Twelve rows per dataset, intentionally missing observations.
60 reproducible tasks: variants 00–01 form development (12), 02–09 form test (48).
Split at dataset level; do not tune on test answers. Generator seed: 20261110 + 1000*family + variant.
All data are synthetic and describe no real individuals or institutions.
Complete-case handling is explicit. First/last uses CSV order. A ratio of sums is not a mean of ratios.
Gold answers use SQLite; production recomputation uses Decimal arithmetic.

## Experiment A: controlled errors and ablation

For each test task retain one correct report, then create seven distinct single-fault reports:
wrong numeric value, wrong unit, wrong valid-row count, wrong chart value, missing chart,
string-valued NaN, and an unsupported causal narrative. The last is deliberately outside
structured verification scope and must be reported as a blind spot.
Evaluate numeric-only, schema-plus-numeric, and full verification on identical reports.
Report per-fault detection and false alarms on clean reports. These are mutation results,
not measured LLM error frequencies. Related mutations of one task are not independent samples.
Do not present naive binomial confidence intervals over these dependent mutations.

## Experiment B: actual local-model pilot

Use qwen2.5:0.5b via Ollama with model digest recorded, temperature 0, seed 31415,
context 4096, output limit 384, JSON output mode. Select variants 02–05 from every family,
giving 24 held-out tasks. A single model and one generation seed form a limited pilot.
Before running test cases, freeze the prompt and record its SHA-256.
Never include gold answers or mutation labels in prompts.

For every task generate one initial answer, then make two independent second calls starting
from that same answer: (1) self-review using data and task, (2) repair using data, task,
and executable verification findings. Both branches receive exactly one extra generation,
the same output limit and model settings. Invalid JSON is a measured failure; service/network
errors are operational failures and must never be scored as model answers.
Record raw responses, full request settings, latency and provider token counts. No retries of
model content or cherry-picking. Reuse saved completed calls when resuming interrupted runs.

An additional deterministic recomputation condition uses the approved contract without model
reasoning. Label this as tool execution, not LLM improvement, and disclose it is already sufficient
for these six operations. The LLM's potential role is interface and explanation, not essential arithmetic.

Final correctness is evaluated against the independent SQLite answers on metrics, units,
complete-case row count and chart data. Narrative truth is outside that correctness metric.
Report paired task outcomes, descriptive Wilson intervals per condition, and a task-level
paired bootstrap interval for accuracy differences (10,000 resamples, fixed seed 20261110).
Intervals reflect this small synthetic task sample, not the population of real analytics tasks.

## Scope challenge checks

Wrong approved intent and unsupported causal narratives can pass numeric verification.
Unsupported operations, undefined ratios, empty data, and invalid input should abstain.
Keep demonstrations of these boundaries next to the successful examples.

## Reporting and integrity

Report actual results even if feedback does not improve the model. No guarantee of model
generalization, grade, security against arbitrary code, or real-world deployment readiness.
AI assistance in coding, manuscript drafting and layout must be disclosed. The student should
inspect the code, reproduce the commands and defend the assumptions before submission.

## Capacity-check amendment (before second-model calls)

The 0.5B pilot revealed frequent report-schema failures. Retain every result.
Run qwen2.5:1.5b on the identical 24 tasks with the identical frozen prompt, options,
and equal-call branches. Store results in results/qwen-1.5b/. This is a post-pilot
capacity check, not a preregistered replication or a new held-out benchmark.
Do not change prompts after observing either model's test results. Report both models.
