# Project description

**Title:** Trust but Verify: Detecting and Repairing Errors in AI-Generated Data Analysis

**Author:** BAHODIR KODIRJON UGLI NAZAROV  
**Course:** New Software Technology, Sichuan University  
**Instructor:** Dr. Hu Dasha  
**Date:** November 2026

## Problem

A syntactically valid, fluent report can still contain the wrong aggregate, denominator,
unit, valid-row count, or chart values. Asking the same model to review itself does not
provide an independent computational signal. This project studies a limited alternative:
recompute structured claims from an approved analysis contract and provide precise feedback.

## Research questions

1. Which error classes does each verification layer detect, and where does verification fail?
2. Does executable feedback improve a local model more than an equal-call self-review baseline?
3. When the analysis contract is already known, does deterministic execution remove the need
   for a language model in the arithmetic itself?

## Contribution

A dependency-free Python verifier for six descriptive operations, a reproducible synthetic
benchmark with an independent SQLite oracle, an ablation study, actual local-model response
logs, and an interactive local demonstration. The contribution is engineering integration
and a bounded experimental study, not a new model or a universal truth detector.

## Implementation

Input CSV + approved JSON contract + candidate report → validation and Decimal recomputation
→ field-specific findings → one model repair or deterministic recomputation.
No model-generated Python or shell code is executed. The trusted contract is a human input,
not a hidden gold answer. The checker never loads the benchmark gold file. The demo uses
deliberately injected errors, visibly labelled as such.

## Acceptance criteria

- Reproduce all 60 datasets from a fixed seed, preserving a 12/48 development/test split.
- Agree with independently implemented SQL answers on all supported generated tasks.
- Report detection and false alarms separately, including unsupported narrative errors.
- Preserve raw model requests and responses and compare equal second-call budgets.
- Provide tests, report source and PDF, editable slides, a demonstration, and reproduction instructions.
- State limitations and disclose AI assistance. No promised grade or unsupported research novelty.
