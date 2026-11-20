# Recent literature and design decisions

Primary sources checked 20 November 2026. Years identify the cited conference or
specific archived version, not necessarily the first preprint posting. None of
these benchmark scores is directly comparable with this small project.

| Work | What it evaluates | Consequence for TrustVerify |
|---|---|---|
| [CRITIC, ICLR 2024](https://arxiv.org/abs/2305.11738v4) | Revision supported by external tool feedback | Compare executable feedback with intrinsic review; disclose that feedback supplies computed expected values. |
| [Huang et al., ICLR 2024](https://arxiv.org/abs/2310.01798v2) | Limits of intrinsic reasoning correction in tested settings | Preserve the equal-call self-review baseline and report failures without generalizing to every model. |
| [DSBench, 2025 v3](https://arxiv.org/abs/2409.07703v3) | Realistic data analysis and modeling tasks | Add attributed real observations; acknowledge that six explicit operations do not test broad data-science competence. |
| [ScienceAgentBench, 2025 v3](https://arxiv.org/abs/2410.05080v3) | Scientific workflow tasks and executable outputs | Score produced artifacts against explicit references; retain raw outputs and operational costs. |
| [JSONSchemaBench, 2025 v3](https://arxiv.org/abs/2501.10868v3) | Constrained generation efficiency, schema coverage and output quality | Separate schema compliance from arithmetic and cross-field correctness. Its quality experiments also caution against assuming constraints always harm reasoning. |
| [TrustDABench, 2026 v1](https://arxiv.org/abs/2608.24145v1) | Reliability under unsupported evidence and robustness to representation changes | State contract/data-quality boundaries; use a causal-prose counterexample and metamorphic software checks. This project does not reproduce its perturbation benchmark. |
| [CausalVerify, 2026 v2](https://arxiv.org/abs/2609.07944v2) | Design, execution and recovery of causal estimates | Treat runnable or numerically consistent output as bounded evidence. TrustVerify does not validate causal identification or estimand choice. |

## Position of this project

The contribution is a small, inspectable software study: independently recompute
six approved operations, compare report fields, expose failure boundaries, and
package each check as replayable evidence. It does not introduce a new language
model, prove general report truth, or claim superiority to the cited systems.

The extension is explicitly post-pilot. It freezes new tasks and generation
settings before execution, adds public data, counterbalances order, and reports
both formatting and substantive outcomes. The receipt feature connects those
bounded checks to reproducible inputs. Its hashes provide integrity relative to
the record, not cryptographic authorship authentication.
