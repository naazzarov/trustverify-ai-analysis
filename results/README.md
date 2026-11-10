# Recorded experimental evidence

All experiments were executed on 10 November 2026. Model-call timestamps are UTC.

- `fault_injection.json`: 48 held-out datasets, one clean report and seven single-fault
  reports per dataset, evaluated with three profiles. 1,152 profile evaluations. There
  are 336 faulty reports per profile, not 1,152 independent faulty observations.
- `live_pilot.json`: actual Qwen2.5 0.5B calls on 24 tasks. `raw/` contains all 72 requests
  and responses, including malformed outputs. No response is silently retried.
- `qwen-1.5b/live_pilot.json`: the disclosed second-model capacity check, with another
  72 raw calls in its `raw/` subdirectory. Same prompts, seed, limits and datasets.
- `live_metadata.json` and its second-model counterpart record model digests, hardware,
  runtime settings, task-file hashes and the relevant protocol hash.
- `secondary_diagnostics.json`: **exploratory** field decomposition. Numeric correctness
  does not include units, row count, chart fields or narrative. It supplements, not replaces,
  the prespecified full structured correctness outcome.
- `live_progress.json` files are complete task-level checkpoints retained for transparency.
  `*-run.log` files are captured orchestrator progress, not separate experiments.

The original protocol is `docs/protocol_v1.md`; its hash matches the first pilot metadata.
`docs/protocol.md` includes the later capacity-check amendment. This project was not
externally preregistered. Model-call count and output-token limits are matched between
review branches, but available computation and prompt length differ.

Primary full-report correctness is 0/24 for every generation condition in both models.
The 1.5B model's feedback branch has 19/24 correct numeric mappings versus 0/24 for
self-review, while report formatting and chart requirements still fail. Deterministic
recomputation gives 24/24 on those task subsets and is conventional tool execution.

Do not interpret the mutation study's designed coverage as model error prevalence, or
the deterministic result as whole-report truth. The repeated task templates limit the
interpretation of uncertainty intervals and transfer to real analysis.
