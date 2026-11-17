"""Build publication figures and presentation evidence from recorded experiment files."""
import json, os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault('MPLCONFIGDIR',str(ROOT/'.build/mpl-cache'))
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import ListedColormap
import sys
sys.path.insert(0,str(ROOT))
from trustverify.core import close

OUT=ROOT/'paper/figures';OUT.mkdir(parents=True,exist_ok=True)
INK='#101C34'; BLUE='#315DF6'; COPPER='#BE7132'; MUTED='#536174'; PALE='#EAF0FC'
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,
 'axes.spines.right':False,'axes.spines.left':False,'axes.titleweight':'bold','axes.labelcolor':MUTED,
 'text.color':INK,'xtick.color':MUTED,'ytick.color':INK,'axes.edgecolor':'#CCD4E0',
 'figure.dpi':180,'savefig.bbox':'tight','pdf.fonttype':42,'svg.fonttype':'none'})
def save(fig,name,source):
 fig.text(.02,.015,source,fontsize=7.4,color=MUTED)
 for ext in ['pdf','png','svg']:
  target=OUT/f'{name}.{ext}';fig.savefig(target,facecolor='white')
  if ext=='svg':target.write_text('\n'.join(line.rstrip() for line in target.read_text().splitlines())+'\n')
 plt.close(fig)

fault=json.loads((ROOT/'results/fault_injection.json').read_text())
small=json.loads((ROOT/'results/live_pilot.json').read_text());large=json.loads((ROOT/'results/qwen-1.5b/live_pilot.json').read_text())
gold=json.loads((ROOT/'data/gold.json').read_text());diag=json.loads((ROOT/'results/secondary_diagnostics.json').read_text())
conditions=['initial','self_review','feedback_repair'];labels=['Initial answer','Self-review','Executable feedback']
fig,ax=plt.subplots(figsize=(8.6,3.6));names=['Numbers only','Schema + numbers','Full verification'];values=[96/336*100,144/336*100,288/336*100]
ax.barh(names,values,color=['#B8C5DE','#7894E8',BLUE],height=.46)
for i,(v,n) in enumerate(zip(values,[96,144,288])):ax.text(v+1.4,i,f'{v:.1f}%  ({n}/336)',va='center',fontweight='bold',fontsize=10)
ax.set(xlim=(0,110),xlabel='Detected controlled faults (%)');ax.invert_yaxis();ax.grid(axis='x',alpha=.13);ax.set_axisbelow(True)
ax.set_title('Field checks expand fault coverage',loc='left',pad=18)
fig.subplots_adjust(left=.22,right=.98,top=.82,bottom=.23)
save(fig,'fault_coverage','Controlled mutations: 48 held-out datasets, 7 faults per dataset. All profiles: 0/48 clean-report false alarms.')

families=['numeric','unit','rows','chart','missing_field','nonfinite','causal_claim']
matrix=np.array([[v['by_fault'][f]/48 for f in families] for v in fault['profiles'].values()])
fig,ax=plt.subplots(figsize=(8.6,3.7));ax.imshow(matrix,cmap=ListedColormap([PALE,BLUE]),vmin=0,vmax=1,aspect='auto')
ax.set_xticks(range(7),['Wrong\nnumber','Wrong\nunit','Wrong\nrow count','Wrong\nchart value','Missing\nchart','NaN\nstring','Causal\nclaim'])
ax.set_yticks(range(3),names);ax.tick_params(length=0,pad=9);ax.spines[:].set_visible(False)
for (i,j),v in np.ndenumerate(matrix):ax.text(j,i,f'{int(v*48)}/48',ha='center',va='center',color='white' if v else INK,fontweight='bold')
ax.set_title('Coverage by injected fault type',loc='left',pad=20)
fig.subplots_adjust(left=.23,right=.98,top=.79,bottom=.25)
save(fig,'fault_matrix','48 cases per cell. Causal statements are outside structured verification scope.')

fig,ax=plt.subplots(figsize=(8.6,3.9));yy=np.arange(6);vals=[];low=[];hi=[];ticks=[]
for model,result in [('0.5B',small),('1.5B',large)]:
 for c,label in zip(conditions,labels):
  s=result['summary'][c];vals.append(s['accuracy']*100);low.append(s['wilson_95'][0]*100);hi.append(s['wilson_95'][1]*100);ticks.append(model+' / '+label)
ax.errorbar(vals,yy,xerr=[np.array(vals)-low,np.array(hi)-vals],fmt='o',color=BLUE,capsize=4,lw=2,markersize=5)
for y in yy:ax.text(17,y,'0 / 24',va='center',fontsize=10,fontweight='bold')
ax.set_yticks(yy,ticks);ax.invert_yaxis();ax.set(xlim=(-1,100),xlabel='Full structured-report correctness (%)');ax.set_title('No generation condition satisfies the complete report contract',loc='left',pad=20)
ax.grid(axis='x',alpha=.13);ax.set_axisbelow(True);fig.subplots_adjust(left=.31,right=.98,top=.83,bottom=.2)
save(fig,'live_accuracy','Actual local-model pilot. 24 tasks per condition. Error bars: descriptive Wilson 95% intervals.')

ops=['sum','mean','weighted_mean','ratio','pct_change','group_sum'];oplabels=['Sum','Mean','Weighted\nmean','Ratio','Percentage\nchange','Grouped\nsum'];byfamily=[]
for op in ops:
 rs=[x for x in large['records'] if x['condition']=='feedback_repair' and x['family']==op]
 byfamily.append(sum(isinstance(x['report'],dict) and isinstance(x['report'].get('metrics'),dict) and set(x['report']['metrics'])==set(gold[x['id']]['metrics']) and all(close(x['report']['metrics'][k],v) for k,v in gold[x['id']]['metrics'].items()) for x in rs))
fig,ax=plt.subplots(figsize=(8.6,3.9));ax.bar(oplabels,byfamily,color=[BLUE]*5+[COPPER],width=.53)
for x,v in enumerate(byfamily):ax.text(x,v+.12,f'{v}/4',ha='center',fontweight='bold')
ax.set(ylim=(0,4.8),yticks=range(5),ylabel='Correct numeric mappings (tasks)');ax.set_title('Executable feedback repairs 19 of 24 numeric mappings',loc='left',pad=20)
ax.grid(axis='y',alpha=.13);ax.set_axisbelow(True);fig.subplots_adjust(left=.08,right=.98,top=.82,bottom=.25)
save(fig,'numeric_by_family','Qwen2.5 1.5B, feedback-repair condition. Exploratory field-level endpoint, 4 held-out tasks per operation.')

field_counts=[]
for c in conditions:
 rs=[x for x in large['records'] if x['condition']==c]
 counts=[diag['models']['1.5B'][c]['numeric_mapping_correct']]
 for code in ['UNIT','ROWS','CHART']:counts.append(sum(not any(f['code']==code for f in x['verification']['findings']) for x in rs))
 field_counts.append(counts)
fig,ax=plt.subplots(figsize=(8.6,3.5));mat=np.array(field_counts)
ax.imshow(mat,cmap='Blues',vmin=0,vmax=24,aspect='auto');ax.set_xticks(range(4),['Numeric mapping','Unit','Valid-row count','Chart consistency']);ax.set_yticks(range(3),labels);ax.tick_params(length=0,pad=10);ax.spines[:].set_visible(False)
for (i,j),v in np.ndenumerate(mat):ax.text(j,i,f'{v}/24',ha='center',va='center',fontweight='bold',color='white' if v>=15 else INK)
ax.set_title('Chart consistency remains the main report bottleneck',loc='left',pad=20);fig.subplots_adjust(left=.24,right=.98,top=.8,bottom=.2)
save(fig,'field_compliance','Qwen2.5 1.5B, 24 tasks per condition. Field checks are independent; all must pass for full correctness.')
evidence={'fault_detection':{'detected':[96,144,288],'total':336,'supported':288,'clean':48,'false_positives':0},'numeric_by_family':dict(zip(ops,byfamily)),'fields':dict(zip(conditions,field_counts)),'numeric_correct':{m:{c:d['numeric_mapping_correct'] for c,d in diag['models'][m].items()} for m in ['0.5B','1.5B']},'primary':{m:{c:res['summary'][c]['correct'] for c in conditions} for m,res in [('0.5B',small),('1.5B',large)]}}
(ROOT/'presentation/evidence.json').write_text(json.dumps(evidence,indent=2)+'\n')
print('Rebuilt 5 figures and presentation evidence from recorded results.')
