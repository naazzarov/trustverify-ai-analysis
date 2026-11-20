# Extension execution note — 20 November 2026

The frozen `protocol_v2.md` planned two capacities (1.5B and 3B), 144 calls each.
The **realized extension contains the complete 1.5B run only: 144 calls**. Together
with the preserved 144-call original pilot, the repository contains **288 actual
model calls**, not 432. No partial 3B output is scored or reported.

The 3B weight transfer repeatedly failed with EOF/TLS errors. Eight standard
download attempts and a separate byte-range acquisition did not produce a fully
verified model file. Alternate publisher-host transfer checks did not establish
a complete usable download. These are acquisition failures, not model-content
failures. The planned larger-capacity comparison remains unperformed; the final
report makes no inference about its performance.

This note records a reduction in realized scope after the 1.5B results were
available. It is not a result-blind amendment or independent preregistration.
The original design, prompts, tasks and negative results are retained unchanged.
No substitute model, seed, prompt or preferred completion was selected to improve
the results. A future 3B replication must be a separately completed, labeled run.

## Complete 1.5B extension

| Format / condition | Schema valid | Numeric mapping | Complete report |
|---|---:|---:|---:|
| JSON / initial | 20/24 | 0/24 | 0/24 |
| JSON / self-review | 20/24 | 0/24 | 0/24 |
| JSON / feedback | 19/24 | 19/24 | 0/24 |
| Schema / initial | 23/24 | 0/24 | 0/24 |
| Schema / self-review | 23/24 | 0/24 | 0/24 |
| Schema / feedback | 23/24 | 18/24 | 0/24 |

Each denominator is the same 24 tasks (12 new synthetic, 12 public). The initial
schema-validity paired contrast improves three tasks and regresses none (exact
two-sided McNemar p=0.25). Three schema-mode completions truncate and remain scored.
Numerical agreement uses the declared absolute/relative tolerance; it is not
integer-exact population accounting. All complete-report outcomes are zero,
so that endpoint has a floor effect and cannot establish equivalence of methods.

Reproduce all scores and request/response integrity checks offline:

```bash
python3 scripts/check_study.py
```
