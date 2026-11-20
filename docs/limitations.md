# Reliability boundaries

- **Approved intent:** If the contract says mean when the user really needs median, correct
  execution can pass the wrong analysis. The contract requires human review.
- **Narrative:** Free text can contain a causal or contextual error while all checked fields pass.
  The causal_claim example demonstrates this; a pass is not a whole-report certificate.
- **Data quality:** Accurate computation on inaccurate data remains inaccurate evidence.
  Deduplication, outlier treatment, population coverage and measurement validity require decisions.
- **Charts:** The checker validates supplied labels and values, not a rendered chart's axes,
  visual geometry, accessibility, or a screenshot. It does not inspect image pixels.
- **Floating-point output:** Decimal is used internally but JSON results are finite floats.
  Relative/absolute tolerance is 1e-6. This is not arbitrary-precision proof.
- **Causality and inference:** No causal identification, hypothesis testing, regression,
  privacy certification, or external fact checking is implemented.
- **Pilot:** Only two small quantized local models, one generation seed and 24 synthetic tasks.
  The second model is a disclosed capacity-check amendment after observing the first.
- **Feedback budget:** Review and feedback repair have equal generation count and token limit,
  but feedback contains extra computational information and may have different prompt lengths.
  It is a system comparison, not an isolation of wording effects.
- **Execution control:** This implementation never executes model-generated code. It does
  not claim to be a sandbox suitable for adding arbitrary code execution later.
- **Deterministic baseline:** Because supported contracts are already specified, direct
  computation is sufficient. The experiment should not imply that an LLM is required here.

## Paired extension

The completed extension uses Qwen2.5 1.5B only, 24 new tasks, two generation formats,
three conditions and one seed: 144 actual calls. A planned 3B model could not be fully
acquired and verified. The reduction was recorded after 1.5B outcomes were available;
it is not a result-blind amendment. See extension_execution_note.md.

Schema validity improves from 20/24 to 23/24 initially, while complete correctness stays
zero. A zero/zero comparison is a floor effect, not evidence of equivalence. Field-level
paired tests are descriptive secondary analyses with no multiplicity adjustment.
Repeated templates, related endpoints and overlapping countries limit independence.

The World Bank snapshot contains 2024 cross-sections and 2013–2024 series. Download
and release dates are 2026; these are not 2026 observations. Curated country cohorts are
not representative samples; grouped totals refer only to included countries. Urban share
is derived and rounded to six decimals. Source estimates are not independently validated.
At a billion people, relative tolerance 1e-6 allows about a thousand people of difference;
reported numeric correctness is not integer-exact population accounting.

## Evidence receipts

Receipts tie a recorded verdict to CSV bytes, the contract, candidate, checking profile
and engine fingerprint. A hash can reveal a change against an unchanged record. An
attacker can rewrite both the content and its hash; no digital signature, time authority
or authorship authentication is provided. Replay success can reproduce a failed verdict.
