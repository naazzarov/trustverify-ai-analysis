"""Derive manuscript tables and secondary diagnostics from recorded evidence."""
import argparse
import json
import sys
from collections import Counter
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from trustverify.benchmark import dump
from trustverify.core import close

ROOT=Path(__file__).resolve().parents[1]


def summarize(allow_partial=False):
    paths=[('0.5B',ROOT/'results/live_pilot.json'),('1.5B',ROOT/'results/qwen-1.5b/live_pilot.json')]
    if not allow_partial and not all(p.exists() for _,p in paths):raise SystemExit('Both complete model runs are required.')
    models=[(label,json.loads(p.read_text())) for label,p in paths if p.exists()]
    gold=json.loads((ROOT/'data/gold.json').read_text())
    diagnostics={}
    for label,result in models:
        counts={}
        for condition in result['summary']:
            records=[r for r in result['records'] if r['condition']==condition]
            exact=0;errors=Counter()
            for r in records:
                report=r['report'];want=gold[r['id']]['metrics']
                if isinstance(report,dict) and isinstance(report.get('metrics'),dict):
                    if set(report['metrics'])==set(want) and all(close(report['metrics'][k],v) for k,v in want.items()):exact+=1
                errors.update({f['code'] for f in r.get('verification',{}).get('findings',[])})
            counts[condition]={'n':len(records),'numeric_mapping_correct':exact,'finding_codes_by_task':dict(errors)}
        diagnostics[label]=counts
    dump(ROOT/'results/secondary_diagnostics.json',{'label':'Exploratory decomposition of the prespecified full correctness metric','models':diagnostics})
    rows=[]
    names={'initial':'Initial','self_review':'Self-review','feedback_repair':'Feedback repair'}
    for label,result in models:
        for condition in names:
            s=result['summary'][condition];low,high=s['wilson_95']
            rows.append(f"{label} & {names[condition]} & {s['correct']}/24 & {100*low:.1f}--{100*high:.1f} & {s['mean_cumulative_wall_seconds']:.2f} \\")
    table='\\begin{tabular}{llrrr}\n\\toprule\nModel & Condition & Correct & 95\\% interval (\\%) & Time (s) \\\\\n\\midrule\n'+'\n'.join(rows)+'\n\\bottomrule\n\\end{tabular}\n'
    # Each data row needs a TeX line break, not a literal single slash.
    table=table.replace(' \\\n',' \\\\\n')
    (ROOT/'paper/live_table.tex').write_text(table)
    comparison=[]
    for label,result in models:
        c=result['paired_comparison'];lo,hi=c['paired_bootstrap_95']
        comparison.append(f"For the {label} model, executable feedback minus self-review is {100*c['feedback_minus_self_review']:.1f} percentage points (paired bootstrap 95\\% interval {100*lo:.1f} to {100*hi:.1f}). There are {c['improved']} improved and {c['regressed']} regressed paired tasks.")
    comparison.append('These descriptive intervals do not establish general equivalence or superiority. In a floor-effect condition, a zero-width empirical bootstrap interval reflects no observed successes in either branch, not certainty about unseen tasks.')
    error_text=''
    if any(label=='1.5B' for label,_ in models):
        d=diagnostics['1.5B'];nums=[d[c]['numeric_mapping_correct'] for c in names]
        error_text=(f"An exploratory decomposition for the 1.5B model finds correct numeric metric mappings on {nums[0]}/24 initial, {nums[1]}/24 self-review and {nums[2]}/24 feedback-repair responses. This secondary diagnostic excludes units, row counts and chart fields and must not replace the primary correctness score. It helps distinguish arithmetic repair from complete-report repair. The field-level finding counts are preserved in \\texttt{{secondary\\_diagnostics.json}}.")
    (ROOT/'paper/results_macros.tex').write_text('\\newcommand{\\ComparisonText}{'+' '.join(comparison)+'}\n\\newcommand{\\LargeErrorText}{'+error_text+'}\n')
    print(json.dumps(diagnostics,indent=2))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--allow-partial',action='store_true');args=p.parse_args();summarize(args.allow_partial)
