import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
lines=['Controlled fault injection: full checking detects **288/336 faults (85.7%)**, including **288/288 supported structured faults**, with **0/48 clean-report false alarms**. It misses all **48 causal-prose faults**, which are outside its scope. These are designed mutations, not natural model error frequencies.','',
       '| Actual local model | Initial | Self-review | Executable-feedback repair |','|---|---:|---:|---:|']
for label,relative in [('Qwen2.5 0.5B','results/live_pilot.json'),('Qwen2.5 1.5B','results/qwen-1.5b/live_pilot.json')]:
    data=json.loads((ROOT/relative).read_text());s=data['summary']
    lines.append('| '+label+' | '+' | '.join(str(s[c]['correct'])+'/24' for c in ['initial','self_review','feedback_repair'])+' |')
lines+=['','The table reports **full structured correctness**, including chart data and units. Deterministic recomputation reaches **24/24** separately and is not counted as LLM improvement.',
        '', 'The model results reveal a floor effect on the full-report endpoint. [Exploratory numeric-only diagnostics](results/secondary_diagnostics.json) distinguish correct arithmetic from complete report compliance. All failures are retained. Wilson intervals, paired outcomes, timing and limitations appear in the report.']
diagnostics=json.loads((ROOT/'results/secondary_diagnostics.json').read_text())['models']['1.5B']
lines+=['',f"For the 1.5B model, correct numeric mappings increase from **{diagnostics['self_review']['numeric_mapping_correct']}/24 with self-review** to **{diagnostics['feedback_repair']['numeric_mapping_correct']}/24 with executable feedback**. This is an exploratory field-level result; the full reports still fail."]
readme=ROOT/'README.md';s=readme.read_text();a=s.index('<!-- RESULTS_START -->')+len('<!-- RESULTS_START -->');b=s.index('<!-- RESULTS_END -->');readme.write_text(s[:a]+'\n'+'\n'.join(lines)+'\n'+s[b:])
