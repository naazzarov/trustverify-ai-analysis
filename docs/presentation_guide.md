# Presentation and demonstration guide

Suggested duration: 10–12 minutes, then questions. Confirm the actual allotted time with the instructor.

## Opening explanation

"I studied how to verify selected claims in an AI-generated analysis. I separated a controlled
error-injection experiment from actual local-model responses. My tool recomputes an approved
analysis contract and checks numbers, units, valid-row counts and chart values. A passing
structured check does not prove that the whole report is true."

## Live demonstration

1. From the repository root run `python3 -m trustverify.server` and open http://127.0.0.1:8765 .
2. Choose ratio-02 and Wrong numeric answer. Explain ratio of sums and missing-value exclusion.
3. Press Verify structured fields. Show the metric discrepancy and its expected value.
4. Press Recompute from contract. Explain that this uses deterministic computation, not model repair.
5. Choose Unsupported causal prose and verify. The structured fields pass. Read the scope warning.
6. Switch coverage to Numbers only, choose Wrong unit, and show why the narrower checker misses it.

## Questions to prepare

**Why use an LLM when Python can compute these answers?**
The deterministic baseline is sufficient once the operation and columns are specified.
The experiment evaluates candidate report checking and feedback, not the necessity of an LLM.
A future interface could help users propose contracts, but approval of intent would remain essential.

**Is the gold answer leaked to the model?**
The evaluator uses independent SQLite answers. The production checker recomputes using Decimal
from data and the approved contract. Feedback may reveal the expected field value; that is a
tool result available at deployment, not a hidden benchmark label. It is privileged computation,
which the equal-call model-only baseline does not have. Describe it as a system comparison.

**Why are controlled detection rates high?**
The designed mutations directly target the designed checks. They measure coverage and basic
implementation correctness, not open-world detection. The narrative blind spot and actual
model pilot provide separate evidence. Do not merge these denominators.

**What counts as correct?**
All metric labels/values, the contract's unit, complete-case row count, and chart labels/values
must match an independent reference within 1e-6 absolute or relative tolerance. Prose is excluded.

**Does a statistically insignificant difference mean the systems are equivalent?**
No. With only 24 tasks, intervals can be wide and power is limited. Report the paired outcomes
and uncertainty, and avoid a general claim of superiority or equivalence.

**How original is the project?**
External feedback and verification are established ideas. The course contribution is the working
integration, reproducible benchmark, field-level ablation and explicit examination of failure boundaries.

**How was AI used?**
Codex assisted with implementation, writing and layout. The reported model responses are real
logged local calls. The student must explain and reproduce the work before submission.
