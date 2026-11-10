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

## AI assistance statement

Codex assisted with software implementation, experiment orchestration, prose and presentation
layout. Published local-model responses come from the logged Ollama calls. Controlled
mutations are programmatically generated. No invented model performance or human studies
are presented. The student must inspect the evidence, reproduce the commands and explain
the assumptions before submitting and presenting the work.
