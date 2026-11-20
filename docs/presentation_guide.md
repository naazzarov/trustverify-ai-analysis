# Presentation and demonstration guide

The deck has **18 main slides and four appendices**. Speaker notes are embedded in the
PowerPoint. Allow approximately 12–15 minutes for the main explanation and a short demo;
this is a rehearsal suggestion, not a course-imposed duration. Adapt to the allotted slot.

## Main-slide route

| Slides | Purpose | Suggested time |
|---|---|---:|
| 1–3 | Introduce the problem using 266.71% versus 263.46%, then define the contract | 2 min |
| 4–5 | Explain independent computation and the three distinct evidence sources | 1 min |
| 6–8 | Controlled coverage, narrative blind spot and preserved pilot floor effect | 2 min |
| 9–10 | Paired extension design, frozen World Bank snapshot and two output formats | 1.5 min |
| 11–14 | Distinguish schema validity, numeric repair, chart agreement and complete correctness | 2 min |
| 15–16 | Show a retained model failure and the replayable receipt contribution | 1.5 min |
| 17–18 | State assurance boundaries and the measured conclusion | 1 min |
| 19–22 | Optional references, paired statistics, reproduction commands and formulas | Q&A |

Opening: “I studied how to verify selected claims in an AI-generated analysis. The
software recomputes an approved contract and checks numbers, units, valid-row counts
and chart data. I separated designed faults from actual model responses, and separated
schema compliance from complete computational correctness.”

Closing: “The checker detects all supported designed faults in this benchmark, while
model feedback repairs many numbers without fixing the whole report. A schema-valid
response still needs computational evidence, and a structured pass does not validate
scientific intent or narrative claims.”

## Short live demonstration

1. Run `python3 -m trustverify.server`; open http://127.0.0.1:8765/#theme=dark .
2. Choose ratio-02 with Wrong numeric answer. It uses 9 complete rows, ratio of sums,
   and a deliberately injected +3.25 percentage-point error. Label it as controlled.
3. Verify and show the discrepancy. Recompute from contract and explain that this is
   deterministic execution, not a model call.
4. Choose Unsupported causal prose. The checked fields pass while the causal claim
   remains unsupported. Read the scope notice.
5. Optionally apply custom CSV `x,n` with rows `10,1`, `20,3`, `,5` and contract
   `{"op":"weighted_mean","column":"x","weight":"n","unit":"points"}`.
   Explain why the valid-row count is two and the weighted mean is 17.5.
6. Download a receipt. If browser downloads are inconvenient, replay the shipped example:

```bash
python3 -m trustverify.audit replay --csv demo/receipt-example/observations.csv   --receipt demo/receipt-example/receipt.json
```

Replay should say `replay_ok: true` while the recorded verification status is `fail`.
They answer different questions: whether the computation reproduces and whether the
candidate agrees with that computation.

## Questions to prepare

**Why use a model when Python can compute these operations?**

Once the operation and columns are specified, deterministic computation is sufficient.
The experiment evaluates report checking and feedback, not the necessity of an LLM.

**Is the model given the answer?**

Feedback can include recomputed expected values. They come from the production checker,
not the evaluator gold file, but they are substantive external information. Equal-call
review controls the number of generations, not the information available to each system.

**Why do all complete reports fail?**

The endpoint requires simultaneous agreement of schema, metrics, unit, rows and chart.
Only one feedback chart per format matches. In mean-06 the metric changes from 5.6 to
14.3 but the chart retains the twelve original observations. Report the floor effect;
do not claim the methods are equivalent or generalize to larger models.

**What does schema-constrained generation improve?**

Observed initial compliance changes 20/24→23/24. Three paired improvements, no
regressions; exact p=.25. The schema constrains types and fields, not gold values,
metric-key identities, correct units or chart/metric equality.

**What happened to the planned 3B model?**

The model download could not be completed and verified. Only 1.5B was run in the
extension. This reduction was recorded after those outcomes were available. The original
pilot separately contains 0.5B and 1.5B results; total actual saved calls are 288.

**Do public data make the benchmark realistic?**

They replace some synthetic values with attributed observations, but the selected
countries and six fixed operation templates still limit generality. Observations end in
2024; the 2026 dates describe release/access, not the observation year.

**How original is this?**

External verification and tool-supported revision are established. The course contribution
is the working integration, frozen evidence, paired structure-versus-correctness study,
field diagnosis and portable receipts with explicit limits.

**Are receipt hashes proof of authorship or correctness?**

No. Hashes provide consistency against the recorded input and engine. They are not digital
signatures. A receipt can faithfully preserve an incorrect candidate and a failed verdict.
