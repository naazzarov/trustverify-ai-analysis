"""Derive manuscript tables, figures and editable-slide values from saved calls."""
import hashlib
import json
import os
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.build/mpl-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from trustverify.study import CONDITIONS, FORMATS

OUT=ROOT/'paper';FIG=OUT/'figures'
BLUE='#315DF6';CYAN='#128CA7';INK='#111B2B';MUTED='#526174';AMBER='#B46A22'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10.5,'text.color':INK,
 'axes.spines.top':False,'axes.spines.right':False,'axes.spines.left':False,
 'axes.labelcolor':MUTED,'xtick.color':MUTED,'ytick.color':INK,'axes.titleweight':'bold',
 'figure.dpi':180,'savefig.bbox':'tight','pdf.fonttype':42,'svg.fonttype':'none'})

def save(fig,name):
 for ext in ('pdf','png','svg'):fig.savefig(FIG/f'{name}.{ext}',facecolor='white')
 plt.close(fig)

def build():
 runs={}
 for path in sorted((ROOT/'results/study').glob('*/study.json')):
  data=json.loads(path.read_text());runs[data['metadata']['context']['model']]=data
 if not runs:raise SystemExit('No completed study to visualize')
 models=list(runs);short=lambda m:m.rsplit(':',1)[-1].upper()
 labels={'initial':'Initial','self_review':'Self-review','feedback_repair':'Feedback'}
 primary=['\\begin{tabular}{llrrr}','\\toprule','Model & Format & Initial & Self-review & Feedback \\\\','\\midrule']
 fields=['\\begin{tabular}{llrrrrrr}','\\toprule',
 'Model / format & Condition & Schema & Numeric & Unit & Rows & Chart & Full \\\\','\\midrule']
 strata=['\\begin{tabular}{llrrrr}','\\toprule',
 'Model & Format & \\multicolumn{2}{c}{Synthetic ($n=12$)} & \\multicolumn{2}{c}{Public ($n=12$)} \\\\',
 '\\cmidrule(lr){3-4}\\cmidrule(lr){5-6}',
 ' & & Numeric & Full & Numeric & Full \\\\','\\midrule']
 comparisons=[]
 for model,d in runs.items():
  for fmt in FORMATS:
   gs=[d['groups'][f'{fmt}/{c}/all'] for c in CONDITIONS]
   primary.append(f'{short(model)} & {({'json':'JSON','schema':'Schema'}[fmt])} & '+' & '.join(f"{g['correct']}/24" for g in gs)+' \\\\')
   for c,g in zip(CONDITIONS,gs):
    fields.append(f'{short(model)} / {fmt} & {labels[c]} & '+' & '.join(str(g[k]) for k in ('schema_valid','numeric','unit','rows','chart','correct'))+' \\\\')
   vals=[]
   for domain in ('synthetic','public'):
    g=d['groups'][f'{fmt}/feedback_repair/{domain}'];vals += [f"{g['numeric']}/12",f"{g['correct']}/12"]
   strata.append(f'{short(model)} & {({'json':'JSON','schema':'Schema'}[fmt])} & '+' & '.join(vals)+' \\\\')
   p=d['paired_comparisons'][f'feedback_minus_review/{fmt}/numeric']
   comparisons.append({'model':model,'comparison':'feedback_minus_review','format':fmt,'outcome':'numeric',**p})
  for c in CONDITIONS:
   for outcome in ('correct','schema_valid','numeric'):
    comparisons.append({'model':model,'comparison':'schema_minus_json','condition':c,'outcome':outcome,
       **d['paired_comparisons'][f'schema_minus_json/{c}/{outcome}']})
 for name,lines in [('study_primary_table',primary),('study_field_table',fields),('study_strata_table',strata)]:
  (OUT/(name+'.tex')).write_text('\n'.join(lines+['\\bottomrule','\\end{tabular}'])+'\n')
 # Dot plots keep uncertainty visible even at a zero score.
 fig,axes=plt.subplots(len(models),2,figsize=(7.2,2.3*len(models)+.7),squeeze=False,sharex=True)
 for i,model in enumerate(models):
  for j,fmt in enumerate(FORMATS):
   ax=axes[i,j];rs=[runs[model]['groups'][f'{fmt}/{c}/all'] for c in CONDITIONS]
   vals=np.array([g['accuracy']*100 for g in rs]);lo=np.array([g['wilson_95'][0]*100 for g in rs]);hi=np.array([g['wilson_95'][1]*100 for g in rs])
   ax.errorbar(vals,range(3),xerr=[vals-lo,hi-vals],fmt='o',color=BLUE if j==0 else CYAN,capsize=4,lw=2)
   ax.set_yticks(range(3),[labels[c] for c in CONDITIONS]);ax.invert_yaxis();ax.set(xlim=(-2,104),xticks=[0,25,50,75,100])
   ax.set_title(f'{short(model)} / {fmt.upper()}',loc='left',pad=10,fontsize=11)
   for y,g in enumerate(rs):ax.text(max(g['accuracy']*100+5,18),y,f"{g['correct']}/24",va='center',fontsize=10)
   ax.grid(axis='x',alpha=.13);ax.set_axisbelow(True)
 for ax in axes[-1]:ax.set_xlabel('Complete-report correctness (%)')
 fig.tight_layout(pad=1.2);save(fig,'study_primary')
 # Field heatmap: genuine counts; completion requires simultaneous agreement.
 matrix=[];ticks=[]
 for model,d in runs.items():
  for fmt in FORMATS:
   for c in CONDITIONS:
    g=d['groups'][f'{fmt}/{c}/all'];matrix.append([g[k] for k in ('schema_valid','numeric','unit','rows','chart','correct')]);ticks.append(f'{short(model)} / {fmt} / {labels[c]}')
 a=np.array(matrix);fig,ax=plt.subplots(figsize=(7.2,.37*len(ticks)+1.2))
 ax.imshow(a,cmap='Blues',vmin=0,vmax=24,aspect='auto')
 ax.set_xticks(range(6),['Schema','Numeric','Unit','Rows','Chart','Complete'])
 ax.set_yticks(range(len(ticks)),ticks);ax.tick_params(length=0,pad=8,labelsize=9.5);ax.spines[:].set_visible(False)
 for (i,j),v in np.ndenumerate(a):ax.text(j,i,str(v),ha='center',va='center',fontsize=10,color='white' if v>=15 else INK,fontweight='bold')
 fig.tight_layout();save(fig,'study_fields')
 # Initial format compliance and feedback accuracy should never be conflated.
 fig,axes=plt.subplots(1,len(models),figsize=(7.2,3.5),squeeze=False)
 for ax,(model,d) in zip(axes[0],runs.items()):
  gs=[d['groups'][f'{f}/initial/all'] for f in FORMATS]
  x=np.arange(2);ax.bar(x-.16,[g['schema_valid'] for g in gs],width=.3,color=BLUE,label='Schema valid')
  ax.bar(x+.16,[g['correct'] for g in gs],width=.3,color=CYAN,label='Complete correct')
  for k,g in enumerate(gs):
   ax.text(k-.16,g['schema_valid']+.6,str(g['schema_valid']),ha='center',fontsize=10)
   ax.text(k+.16,g['correct']+.6,str(g['correct']),ha='center',fontsize=10)
  ax.set_xticks(x,['JSON','Schema']);ax.set(ylim=(0,27),yticks=[0,6,12,18,24],ylabel='Tasks (n=24)')
  ax.set_title(short(model),loc='left',fontsize=12);ax.grid(axis='y',alpha=.12);ax.set_axisbelow(True)
 axes[0,0].legend(loc='upper left',bbox_to_anchor=(0,-.18),ncol=2,frameon=False,fontsize=9)
 fig.tight_layout();save(fig,'schema_vs_truth')
 # Keep a traceable worked failure rather than an invented model example.
 case_model='qwen2.5:1.5b';case={}
 if case_model in runs:
  for c in ('initial','feedback_repair'):
   r=next(r for r in runs[case_model]['records'] if r['id']=='mean-06' and r['format']=='schema' and r['condition']==c)
   case[c]=r
   excerpt={k:v for k,v in r['report'].items() if k!='narrative'}
   formatted=json.dumps(excerpt,indent=2)
   for key in ('labels','values'):
    a=excerpt['chart'][key];pretty=json.dumps(a,indent=2).replace('\n','\n    ')
    formatted=formatted.replace(pretty,json.dumps(a))
   (OUT/f'case_{c}.json').write_text(formatted+'\n')
 all_records=[dict(r,model=m) for m,d in runs.items() for r in d['records']]
 evidence={'models':models,'calls':len(all_records),'tasks':24,'synthetic_tasks':12,'public_tasks':12,
   'groups':{m:d['groups'] for m,d in runs.items()},'comparisons':comparisons,'worked_case':case,
   'sources':{m:{'path':f"results/study/qwen2.5-{m.rsplit(':',1)[-1]}/study.json",'sha256':hashlib.sha256((ROOT/f"results/study/qwen2.5-{m.rsplit(':',1)[-1]}/study.json").read_bytes()).hexdigest()} for m in runs}}
 (ROOT/'presentation/study_evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
 paragraphs=[]
 for model,d in runs.items():
  g=d['groups'];a=g['json/initial/all'];b=g['schema/initial/all']
  jf=g['json/feedback_repair/all'];sf=g['schema/feedback_repair/all']
  paragraphs.append(f"For Qwen2.5 {short(model)}, initial schema compliance is {a['schema_valid']}/24 in JSON mode and {b['schema_valid']}/24 in schema mode. "
   f"Complete correctness is {a['correct']}/24 and {b['correct']}/24 respectively. "
   f"After executable feedback, numerical mappings are correct on {jf['numeric']}/24 JSON-mode tasks and {sf['numeric']}/24 schema-mode tasks; "
   f"complete reports score {jf['correct']}/24 and {sf['correct']}/24.")
  z=d['paired_comparisons']['schema_minus_json/initial/schema_valid']
  paragraphs.append(f"The initial schema-validity contrast improves {z['improved']} tasks and regresses {z['regressed']} (exact two-sided paired $p={z['exact_mcnemar_two_sided_p']:.4g}$). A zero complete-report score creates a floor effect; it does not establish equivalence between formats.")
  for fmt in FORMATS:
   p=d['paired_comparisons'][f'feedback_minus_review/{fmt}/numeric']
   paragraphs.append(f"For the {short(model)} {fmt.upper() if fmt=='json' else fmt} comparison, feedback versus self-review improves numerical correctness on {p['improved']} tasks and regresses on {p['regressed']}; "
    f"the exact two-sided paired test gives $p={p['exact_mcnemar_two_sided_p']:.8f}$. This is a descriptive secondary comparison without a multiplicity adjustment.")
  trunc=sum(r['truncated'] for r in d['records']);tokens=sum(r['output_tokens'] for r in d['records'])
  paragraphs.append(f"The {short(model)} run records {trunc} truncated completions among 144 calls and {tokens:,} generated tokens. "
    "Truncations remain in the denominator. A valid structure can still contain a wrong metric or an inconsistent chart.")
 (OUT/'study_results_text.tex').write_text('\n\n'.join(paragraphs)+'\n')
 n=len(all_records)
 last_model=models[-1];last=runs[last_model]
 a=last['groups']['schema/initial/all'];b=last['groups']['schema/feedback_repair/all']
 abstract=(f"In the extension, the {short(last_model)} model produces {a['schema_valid']}/24 schema-valid initial reports "
   f"under constrained decoding, while complete correctness changes from {a['correct']}/24 initially to {b['correct']}/24 with executable feedback. "
   f"Its feedback numerical mappings are correct on {b['numeric']}/24 tasks within the stated tolerance.")
 (OUT/'study_macros.tex').write_text(f'\\newcommand{{\\StudyCalls}}{{{n}}}\n\\newcommand{{\\StudyModels}}{{{len(models)}}}\n'
   +'\\newcommand{\\StudyAbstract}{'+abstract+'}\n')
 print(f'Derived tables, three figures and presentation evidence from {n} raw-call records.')


if __name__=='__main__':build()
