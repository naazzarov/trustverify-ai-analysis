"""Generate publication figures from measured JSON results, never typed-in scores."""
import json
import os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ.setdefault("MPLCONFIGDIR",str(ROOT/".build/mpl-cache"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

OUT=ROOT/"paper/figures"
plt.rcParams.update({"font.family":"DejaVu Sans","font.size":10,"axes.spines.top":False,
    "axes.spines.right":False,"axes.titleweight":"bold","figure.dpi":160,
    "savefig.bbox":"tight","pdf.fonttype":42,"svg.fonttype":"none"})
COLORS=["#98a9b2","#426b83","#087f78"]

def save(fig,name):
    for ext in ["pdf","png","svg"]:fig.savefig(OUT/f"{name}.{ext}")
    plt.close(fig)

fault=json.loads((ROOT/"results/fault_injection.json").read_text())
names=["Numbers only","Schema + numbers","Full structured check"]
fig,ax=plt.subplots(figsize=(7.6,3.8))
values=[v["recall_all_faults"]*100 for v in fault["profiles"].values()]
ax.barh(names,values,color=COLORS,height=.55)
for i,v in enumerate(values):ax.text(v+1,i,f"{v:.1f}%",va="center")
ax.set(xlim=(0,104),xlabel="Detected injected faults (%)",ylabel="Verification profile",
       title="Additional checks expand controlled error coverage")
ax.invert_yaxis();ax.grid(axis="x",alpha=.15);ax.set_axisbelow(True)
fig.subplots_adjust(left=.25,right=.98,bottom=.24,top=.86)
fig.text(.02,.015,"Source: fault_injection.json · 10 Nov 2026 · 48 datasets × 7 faults; causal prose is outside scope",fontsize=8)
save(fig,"fault_coverage")

families=["numeric","unit","rows","chart","missing_field","nonfinite","causal_claim"]
matrix=np.array([[v["by_fault"][f]/48 for f in families] for v in fault["profiles"].values()])
fig,ax=plt.subplots(figsize=(8,4.2))
ax.imshow(matrix,cmap="Greens",vmin=0,vmax=1,aspect="auto")
ax.set_xticks(range(7),["Numeric","Unit","Row count","Chart data","Missing chart","NaN string","Causal prose"],rotation=25,ha="right")
ax.set_yticks(range(3),names);ax.set(xlabel="Injected fault type",ylabel="Verification profile",title="Detection by fault type (48 cases per cell)")
for (i,j),v in np.ndenumerate(matrix):ax.text(j,i,f"{int(v*48)}/48",ha="center",va="center",color="white" if v>.5 else "#20322c")
fig.subplots_adjust(left=.23,right=.98,bottom=.33,top=.86)
fig.text(.02,.015,"Source: controlled mutation experiment · 10 Nov 2026 · designed coverage, not natural model error rates",fontsize=8)
save(fig,"fault_matrix")

models=[]
for label,path in [("Qwen2.5 0.5B",ROOT/"results/live_pilot.json"),("Qwen2.5 1.5B",ROOT/"results/qwen-1.5b/live_pilot.json")]:
    if path.exists():models.append((label,json.loads(path.read_text())))
if models:
    conditions=["initial","self_review","feedback_repair"]
    fig,ax=plt.subplots(figsize=(7.8,4.6));x=np.arange(3);w=.30
    for i,(label,result) in enumerate(models):
        s=result["summary"];vals=[s[c]["accuracy"]*100 for c in conditions]
        lows=[s[c]["wilson_95"][0]*100 for c in conditions];highs=[s[c]["wilson_95"][1]*100 for c in conditions]
        xpos=x+(i-(len(models)-1)/2)*w
        ax.bar(xpos,vals,w,label=label,color=[COLORS[1],COLORS[2]][i])
        ax.errorbar(xpos,vals,yerr=[np.array(vals)-lows,np.array(highs)-vals],fmt="none",ecolor="#263b40",capsize=4,lw=1)
        for pos,val,c in zip(xpos,vals,conditions):ax.text(pos,val+3,f"{s[c]['correct']}/24",ha="center",fontsize=9)
    ax.set_xticks(x,["Initial answer","Self-review","Executable feedback"])
    ax.set(ylim=(0,108),xlabel="Generation condition",ylabel="Structured correctness (%)",title="Local-model pilot with equal second-call budgets")
    ax.legend(frameon=False,loc="upper left");ax.grid(axis="y",alpha=.15);ax.set_axisbelow(True)
    fig.subplots_adjust(left=.12,right=.98,bottom=.24,top=.86)
    fig.text(.02,.015,"Source: saved live_pilot.json files · 10 Nov 2026 · 24 paired tasks/model; error bars: Wilson 95%",fontsize=8)
    save(fig,"live_accuracy")
print("Figures written to",OUT)
