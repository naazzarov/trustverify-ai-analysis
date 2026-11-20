import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const root=path.resolve(path.dirname(fileURLToPath(import.meta.url)),'../..');
const dir=path.resolve(root,'.build/slides');
const finalPath=path.resolve(process.env.SLIDE_OUTPUT || path.join(dir,'TrustVerify-Research-Defense.pptx'));
await fs.mkdir(dir,{recursive:true});
const P=Presentation.create({slideSize:{width:1280,height:720}});
const E=JSON.parse(await fs.readFile(path.join(root,'presentation/study_evidence.json'),'utf8'));
const D=JSON.parse(await fs.readFile(path.join(root,'presentation/evidence.json'),'utf8'));
const C={night:'#080F20',ink:'#E8EEF8',blue:'#7199FF',cyan:'#68D8EB',amber:'#FFB665',muted:'#AFBED2',line:'#283C57',pale:'#152B47',paper:'#0D1B31',white:'#F4F7FC',dim:'#AAB9D0'};
const font='Avenir Next';
const backgrounds=new WeakMap();
function text(s,v,x,y,w,h,size=28,{color=C.ink,bold=false,align='left',mono=false}={}){
  const a=s.shapes.add({geometry:'textbox',name:String(v).slice(0,40),position:{left:x,top:y,width:w,height:h},fill:'none',line:{fill:'none',width:0}});
  a.text=v;a.text.style={typeface:mono?'Menlo':font,fontSize:size,color,bold,alignment:align};a.text.insets=0;return a;
}
function rule(s,x,y,w,color=C.line){s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:1},fill:color,line:{fill:'none',width:0}});}
function block(s,label,x,y,w,h,{dark=true,highlight=false,size=25}={}){
 const a=s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill:highlight?'#3569DD':(dark?'#142440':C.pale),line:{fill:highlight?'#3569DD':(dark?'#314363':C.line),width:1}});
 a.text=label;a.text.style={typeface:font,fontSize:size,bold:true,color:dark||highlight?C.white:C.ink};a.text.insets=18;return a;
}
function arrow(s,x,y,w=42,color=C.blue){s.shapes.add({geometry:'rightArrow',position:{left:x,top:y,width:w,height:20},fill:color,line:{fill:'none',width:0}});}
function slide(title,notes,{dark=true,bg,plain=false}={}){
 const s=P.slides.add();const shades=['#080F20','#0B182B','#101922','#0A1B30','#0D1B31','#080F20'];const fill=bg||shades[(P.slides.items.length-1)%shades.length];s.background.fill=fill;backgrounds.set(s,fill);s.speakerNotes.text=notes;
 if(!plain)text(s,title,64,54,1150,120,44,{color:dark?C.white:C.ink,bold:true});
 text(s,String(P.slides.items.length).padStart(2,'0'),1162,672,52,24,15,{color:dark?C.dim:C.muted,align:'right'});return s;
}
function source(s,t,dark=true){text(s,t,64,651,1080,35,14,{color:dark?C.dim:C.muted});}
async function img(s,file,x,y,w,h,fit='contain'){
 const b=await fs.readFile(file);s.images.add({blob:b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),contentType:'image/png',alt:path.basename(file),fit,position:{left:x,top:y,width:w,height:h}});
}
function table(s,v,x,y,w,h,widths,{dark=true,heat=false,size=24}={}){
 const t=s.tables.add({rows:v.length,columns:v[0].length,left:x,top:y,width:w,height:h,values:v,columnWidths:widths});
 t.borders.assign({fill:backgrounds.get(s),width:3,style:'solid'});
 for(let r=0;r<v.length;r++)for(let c=0;c<v[0].length;c++){
  const a=t.getCell(r,c);a.fill=r===0?(dark?'#233450':C.ink):(c===0?(dark?'#142440':C.pale):(dark?'#0D1A30':C.paper));
  a.text.style={typeface:font,fontSize:size,color:r===0||dark?C.white:C.ink,bold:r===0||c===0};
  if(heat&&r>0&&c>0){let [n,d]=String(v[r][c]).split('/').map(Number);let f=n/d;a.fill=f===1?'#3569DD':(f===0?'#19243A':(f<.5?'#203E66':'#315A9D'));a.text.style={typeface:font,fontSize:size,color:f>0?C.white:C.dim,bold:true};}
 }
 return t;
}
function chart(s,cats,series,x,y,w,h,{dark=true,horizontal=false,max=24,step=6,format='0',labels=true,legend=false,...extra}={}){
 const fg=dark?C.dim:C.muted, grid=dark?'#25344B':C.line;
 return s.charts.add('bar',{position:{left:x,top:y,width:w,height:h},categories:cats,series,
   chartFill:backgrounds.get(s),plotAreaFill:backgrounds.get(s),chartLine:{fill:'none',width:0},plotAreaLine:{fill:'none',width:0},
   barOptions:{direction:horizontal?'bar':'column',grouping:'clustered',gapWidth:90},hasLegend:legend,
   legend:{position:'bottom',textStyle:{typeface:font,fontSize:19,fill:fg}},
   xAxis:{textStyle:{typeface:font,fontSize:21,fill:fg},line:{fill:grid,width:1},majorGridlines:null},
   yAxis:{min:0,max,majorUnit:step,numberFormatCode:format,textStyle:{typeface:font,fontSize:18,fill:fg},line:{fill:'none',width:0},majorGridlines:{fill:grid,width:1}},
   dataLabels:{showValue:labels,position:'outEnd',numberFormatCode:format,textStyle:{typeface:font,fontSize:24,fill:dark?C.white:C.ink,bold:true}},...extra});
}

const G=E.groups['qwen2.5:1.5b'];
const stat=(fmt,c,field,domain='all')=>G[`${fmt}/${c}/${domain}`][field];
const codeColor={key:'#9CDCFE',string:'#CE9178',number:'#B5CEA8',punct:'#FFD700',text:'#D4D4D4'};
function editor(s,name,lines,x,y,w,h,{size=25,lineHeight=38}={}){
 s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:h},fill:'#1E1E1E',line:{fill:'#3D4450',width:1}});
 s.shapes.add({geometry:'rect',position:{left:x,top:y,width:w,height:40},fill:'#252526',line:{fill:'none',width:0}});
 text(s,name,x+18,y+10,w-36,28,18,{mono:true,color:'#CCCCCC'});
 lines.forEach((line,i)=>{
  text(s,String(i+1),x+8,y+57+i*lineHeight,30,32,17,{mono:true,color:'#858585',align:'right'});
  const runs=[];const regex=/("[^"\\]*(?:\\.[^"\\]*)*"(?=\s*:))|("[^"\\]*(?:\\.[^"\\]*)*")|(-?\d+(?:\.\d+)?)|([{}\[\]])/g;let start=0;
  for(const m of line.matchAll(regex)){
   if(m.index>start)runs.push({run:line.slice(start,m.index)});
   runs.push({run:m[0],style:{color:m[1]?codeColor.key:m[2]?codeColor.string:m[3]?codeColor.number:codeColor.punct}});start=m.index+m[0].length;
  }
  if(start<line.length)runs.push({run:line.slice(start)});
  const a=text(s,'',x+54,y+53+i*lineHeight,w-68,lineHeight,size,{mono:true,color:codeColor.text});a.text={runs};
 });
}

// 01 Institutional cover. Supplied wordmark is unchanged.
let s=slide('','TrustVerify. Executable Verification of AI-Generated Data Analysis. BAHODIR KODIRJON UGLI NAZAROV, Software Engineering, Sichuan University. New Software Technology, Dr. Hu Dasha. November 2026. University wordmark: unchanged SCU_TITLE.png supplied in the course-paper template. Background: conceptual verification artwork, not an experimental image.',{plain:true});
await img(s,path.join(root,'presentation/assets/verification-cover.png'),0,0,1280,720,'cover');
s.shapes.add({geometry:'rect',position:{left:0,top:0,width:1280,height:110},fill:'#FFFFFF',line:{fill:'none',width:0}});
await img(s,path.join(root,'paper/figures/SCU_TITLE.png'),64,20,252,66);
text(s,'Sichuan University',355,38,450,45,27,{color:'#111B2B',bold:true});
text(s,'NEW SOFTWARE TECHNOLOGY',850,45,370,40,17,{color:'#526174',align:'right'});
text(s,'TrustVerify',64,184,660,110,78,{bold:true,color:C.white});
text(s,'Executable verification of\nAI-generated data analysis',68,319,630,135,37,{color:C.white});
text(s,'BAHODIR KODIRJON UGLI NAZAROV',68,570,810,35,23,{color:C.white});
text(s,'Software Engineering · November 2026',68,623,730,35,21,{color:C.dim});

// 02 A concrete controlled discrepancy.
s=slide('A plausible report can contain the wrong statistic','Controlled ratio-02 example, demo/examples.json. 100 × 137 / 52 = 263.46153846153845%; nine complete observations. The deliberately injected metric adds 3.25 percentage points. This is not a natural model output.');
text(s,'266.71%',64,215,540,115,89,{bold:true,color:C.amber});
text(s,'Candidate metric',72,350,480,45,28,{color:C.dim});
text(s,'263.46%',698,215,530,115,89,{bold:true,color:C.cyan});
text(s,'Independent recomputation',705,350,500,45,28,{color:C.dim});
rule(s,64,431,1152);
text(s,'100 × Σx / Σn',68,474,510,65,38,{bold:true});
text(s,'9 complete observations\nSame CSV and approved contract',700,471,510,95,27,{color:C.dim});
text(s,'3.25 percentage points of error',68,562,1050,50,33,{bold:true});
source(s,'Controlled ratio-02 mutation. Displayed percentages rounded to two decimals.');

// 03 Editable syntax highlighted code.
s=slide('The approved analysis contract','The contract is human approved. It fixes operation, columns, unit and missing-value semantics. The ratio is a ratio of sums, not an average of row ratios. The checker cannot infer whether this is the right research question. Source: trustverify/core.py, data/tasks.jsonl.');
editor(s,'contract.json',['{','  "op": "ratio",','  "column": "x",','  "denominator": "n",','  "unit": "%"','}'],64,241,630,348,{size:27,lineHeight:43});
text(s,'Fields that must agree',762,220,444,45,29,{bold:true});
for(const [i,v] of ['Metric labels and values','Output unit and valid rows','Chart labels and values'].entries()){
 rule(s,762,294+i*96,444);text(s,v,762,312+i*96,444,70,27);
}
source(s,'Six supported operations. Blank required observations are excluded by an explicit complete-case rule.');

// 04 Native editable architecture.
s=slide('Independent verification architecture','Production: trustverify/core.py uses Decimal with a 40-digit context and never reads evaluator gold files. Evaluation: trustverify/benchmark.py uses independently implemented SQLite queries. No model-generated code executes. Both follow the approved contract, so a shared specification error remains possible.');
block(s,'CSV + approved\ncontract',64,216,290,100);arrow(s,390,256,46,C.cyan);
block(s,'Decimal\nrecomputation',475,216,310,100,{highlight:true});
block(s,'Candidate\nJSON report',64,395,290,100);arrow(s,390,435,46,C.cyan);
block(s,'Field comparison',475,395,310,100);
s.shapes.add({geometry:'downArrow',position:{left:615,top:336,width:20,height:40},fill:C.cyan,line:{fill:'none',width:0}});
block(s,'Pass, fail\nor abstain',925,395,290,100);arrow(s,835,435,46,C.cyan);
rule(s,64,553,1152);text(s,'Separate evaluation',64,583,350,40,24,{color:C.dim});
text(s,'SQLite reference answers',475,579,730,45,29,{bold:true,color:C.cyan});
source(s,'Independent implementations reduce shared-code errors; they do not validate the contract’s scientific intent.');

// 05 Three experiments, distinct denominators.
s=slide('Evidence collected','Sources: results/fault_injection.json, results/live_pilot.json, results/qwen-1.5b/live_pilot.json, results/study/qwen2.5-1.5b/study.json. The original pilot has 144 calls; the extension adds 144. The planned 3B download failed and produced no scored run; it must not be counted as 432 calls.');
table(s,[['Study','Data / comparison','Measured size'],['Controlled coverage','48 synthetic test datasets','48 clean + 336 faulty reports'],['Original model pilot','Qwen2.5 0.5B and 1.5B','24 tasks/model; 144 calls'],['Paired extension','1.5B; JSON vs schema','24 new tasks; 144 calls']],64,231,1152,306,[306,430,416],{size:24});
text(s,'288',64,563,290,80,63,{bold:true,color:C.cyan});
text(s,'actual saved model calls',350,583,840,45,29,{bold:true});
source(s,'Controlled mutations and natural model outputs remain separate experiments.');

// 06 Editable native coverage chart.
s=slide('Full checking detects 288 of 336 designed faults','Source: results/fault_injection.json. Numeric-only detects 96, schema+numeric 144, full 288. All 288 supported structured mutations are detected. Causal prose is outside scope. Every profile has zero false alarms on 48 clean reports. Counts describe designed coverage, not natural LLM error prevalence.');
chart(s,['Numbers only','Schema + numbers','Full verification'],[{name:'Detected faults',values:D.fault_detection.detected,fill:C.blue,points:[{idx:0,fill:'#435D83'},{idx:1,fill:'#718FC8'},{idx:2,fill:C.cyan}]}],44,227,825,330,{horizontal:true,max:336,step:84});
text(s,'85.7%',927,236,300,110,75,{bold:true,color:C.cyan});
text(s,'of all injected faults',933,366,280,70,25,{color:C.dim});
rule(s,64,579,1152);text(s,'288/288 structured faults detected',64,600,720,42,27,{bold:true});
text(s,'0/48 clean false alarms',813,602,400,40,24,{color:C.dim});
source(s,'Seven injected fault classes. The denominator includes 48 unsupported causal narratives.');

// 07 Native fault-class heatmap table.
s=slide('Checking coverage depends on the field','Source: results/fault_injection.json. Forty-eight cases per cell. Full structured checking adds unit, row-count and chart validation; no profile checks the meaning of a narrative.');
table(s,[['Checker','Number','Unit','Rows','Chart','Missing','NaN','Causal'],['Numbers','48/48','0/48','0/48','0/48','0/48','48/48','0/48'],['Schema + numeric','48/48','0/48','0/48','0/48','48/48','48/48','0/48'],['Full','48/48','48/48','48/48','48/48','48/48','48/48','0/48']],64,244,1152,270,[235,131,131,131,131,131,131,131],{heat:true,size:22});
text(s,'All 48 causal-prose faults remain unchecked',64,564,1130,55,34,{bold:true,color:C.amber});
source(s,'“Missing” removes the required chart. “NaN” replaces a number with the string NaN.');

// 08 Preserve the original pilot floor effect.
s=slide('The original pilot exposes a report-level floor effect','Sources: both original live_pilot.json files and results/secondary_diagnostics.json. Every generated condition scores 0/24 on full structured correctness. Qwen2.5 1.5B feedback nevertheless repairs 19/24 numerical mappings. The numerical endpoint is exploratory. The capacity check followed inspection of the 0.5B pilot.');
table(s,[['Original model','Initial','Self-review','Feedback'],['Qwen2.5 0.5B','0/24','0/24','0/24'],['Qwen2.5 1.5B','0/24','0/24','0/24']],64,228,1152,225,[342,270,270,270],{size:28});
text(s,'19/24',64,505,440,105,77,{bold:true,color:C.cyan});
text(s,'numerical mappings repaired in the 1.5B pilot\nComplete-report correctness remains 0/24',518,526,695,100,29,{color:C.dim});
source(s,'Primary endpoint: metric mapping + unit + valid rows + chart agreement. Narrative truth excluded.');

// 09 The paired design is editable and unambiguous.
s=slide('Paired extension: generation format and repair','Frozen protocol: docs/protocol_v2.md; realized scope: docs/extension_execution_note.md. Twenty-four new tasks: twelve previously uncalled synthetic variants and twelve public tasks. Identical system prompt and schema text; only API format differs. Each second call starts from the same initial response. Counterbalanced order. Actual 1.5B run: 144 calls. Planned 3B run was not realized.');
text(s,'24 tasks',64,205,400,72,53,{bold:true,color:C.cyan});
text(s,'12 synthetic + 12 public',530,219,670,45,29,{color:C.dim});
block(s,'JSON mode',64,333,290,86);block(s,'Schema mode',64,454,290,86,{highlight:true});
arrow(s,394,368,49,C.cyan);arrow(s,394,490,49,C.cyan);
block(s,'Initial report',488,333,290,86);block(s,'Initial report',488,454,290,86);
text(s,'Self-review',886,333,325,43,28,{bold:true});text(s,'or executable feedback',886,382,325,68,25,{color:C.cyan});
text(s,'Self-review',886,454,325,43,28,{bold:true});text(s,'or executable feedback',886,503,325,68,25,{color:C.cyan});
arrow(s,809,368,42,C.cyan);arrow(s,809,490,42,C.cyan);
source(s,'Identical data and prompts. One extra call per branch. Seed 31415; output cap 512.');

// 10 Public observations with attribution and explicit boundaries.
s=slide('Public-data tasks use a frozen World Bank snapshot','Source: World Bank WDI, population SP.POP.TOTL and urban population SP.URB.TOTL. Official bulk exports updated 11 November 2026; accessed 20 November 2026. Original ZIPs, JSON metadata, transformations and hashes are retained under data/public/source. CC BY 4.0, attribution World Bank. National urban definitions differ. Country subsets are curated and not representative global samples.');
text(s,'2024',64,214,450,102,77,{bold:true,color:C.cyan});
text(s,'country observations',70,335,470,50,28,{color:C.dim});
text(s,'2013–2024',664,214,550,102,66,{bold:true,color:C.blue});
text(s,'Uzbekistan and Japan series',671,335,540,50,28,{color:C.dim});
table(s,[['Cohort A','CHN  IDN  IND  PAK  UZB  KAZ','DEU  FRA  NGA  KEN  BRA  MEX'],['Cohort B','JPN  VNM  BGD  LKA  TUR  GEO','GBR  ITA  ZAF  ETH  ARG  COL']],64,430,1152,125,[180,486,486],{size:22});
text(s,'Population · urban share · selected-country region totals',64,587,1140,45,28,{bold:true});
source(s,'World Bank WDI · CC BY 4.0. Country subsets and derived percentages; source estimates are not independently validated.');

// 11 Schema compliance is explicitly distinct from complete correctness.
s=slide('Schema validity improves; complete correctness stays zero','Source: results/study/qwen2.5-1.5b/study.json, groups json/initial/all and schema/initial/all. Initial schema validity 20/24 versus 23/24. Complete correctness 0/24 in both. Paired schema-validity contrast: 3 improve, 0 regress, exact two-sided McNemar p=0.25. One schema-mode initial response truncates and remains scored. A zero complete score is a floor effect, not proof of equivalence.');
chart(s,['JSON mode','Schema mode'],[{name:'Schema valid',values:[stat('json','initial','schema_valid'),stat('schema','initial','schema_valid')],fill:C.blue},{name:'Complete correct',values:[stat('json','initial','correct'),stat('schema','initial','correct')],fill:C.cyan}],45,208,820,385,{max:24,step:6,legend:true});
text(s,'+3',925,238,285,110,80,{bold:true,color:C.cyan});
text(s,'schema-valid reports\n0 gained complete reports',930,375,285,120,28,{color:C.dim});
source(s,'Qwen2.5 1.5B extension · 24 paired tasks per format · p=0.25 for initial schema-validity contrast.');

// 12 Numerical endpoint: honest counts from retained responses.
s=slide('Feedback repairs numerical mappings in both formats','Source: results/study/qwen2.5-1.5b/study.json. Numerical mapping requires matching metric keys and values within abs/relative tolerance 1e-6. JSON: initial 0, self-review 0, feedback 19. Schema: 0,0,18. This secondary endpoint excludes units, row counts and chart consistency. Expected values are supplied by the executable feedback, so this is not unaided model reasoning.');
chart(s,['Initial','Self-review','Feedback'],[{name:'JSON mode',values:['initial','self_review','feedback_repair'].map(c=>stat('json',c,'numeric')),fill:C.blue},{name:'Schema mode',values:['initial','self_review','feedback_repair'].map(c=>stat('schema',c,'numeric')),fill:C.cyan}],45,217,1165,360,{max:24,step:6,legend:true});
text(s,'19/24 JSON     18/24 schema',64,602,1120,45,31,{bold:true,color:C.cyan});
source(s,'Secondary outcome. All tasks remain scored, including three truncated schema-mode completions.');

// 13 Native field-compliance heatmap.
s=slide('Chart consistency remains the main output failure','Source: results/study/qwen2.5-1.5b/study.json. Each field count is independent, denominator 24. Complete correctness requires schema compliance and simultaneous metric, unit, rows and chart agreement. Narrative meaning is excluded. JSON feedback chart 1/24; schema feedback chart 1/24; all complete-report outcomes 0.');
const fieldRows=[['Format / condition','Schema','Numeric','Unit','Rows','Chart','Complete']];
for(const f of ['json','schema'])for(const c of ['initial','self_review','feedback_repair'])fieldRows.push([`${f==='json'?'JSON':'Schema'} / ${{initial:'initial',self_review:'review',feedback_repair:'feedback'}[c]}`,...['schema_valid','numeric','unit','rows','chart','correct'].map(k=>`${stat(f,c,k)}/24`)]);
table(s,fieldRows,64,216,1152,365,[306,141,141,141,141,141,141],{size:23,heat:true});
text(s,'Only one of 24 charts agrees after feedback in either format',64,600,1135,43,29,{bold:true,color:C.amber});
source(s,'The structural schema does not enforce chart–metric equality or the approved calculation.');

// 14 Native public/synthetic stratified numerical counts.
s=slide('The public-data stratum preserves the same distinction','Source: extension study groups */feedback_repair/synthetic and */feedback_repair/public. Numeric correctness: JSON synthetic 10/12, public 9/12; schema synthetic 10/12, public 8/12. Complete correctness is zero in all four cells. Shared countries/templates make these descriptive strata, not independent populations.');
chart(s,['Synthetic tasks','Public-data tasks'],[{name:'JSON feedback',values:[stat('json','feedback_repair','numeric','synthetic'),stat('json','feedback_repair','numeric','public')],fill:C.blue},{name:'Schema feedback',values:[stat('schema','feedback_repair','numeric','synthetic'),stat('schema','feedback_repair','numeric','public')],fill:C.cyan}],45,211,820,385,{max:12,step:3,legend:true});
text(s,'0/12',922,252,290,105,75,{bold:true,color:C.amber});
text(s,'complete reports\nin every stratum',928,385,285,100,28,{color:C.dim});
source(s,'Qwen2.5 1.5B feedback condition · 12 tasks per stratum · curated cohorts and fixed operations.');

// 15 A real retained error pair, as editable code excerpts.
s=slide('The metric changes; the chart still describes the input','Actual retained response pair: mean-06, schema mode, Qwen2.5 1.5B. Raw logs under results/study/qwen2.5-1.5b/raw/mean-06-schema-{initial,feedback_repair}.json. Initial metric 5.6; after feedback 14.3. The chart keeps label x and the twelve original observations, rather than one value metric. Excerpts omit the unit, row count and narrative; ellipsis abbreviates the observed array.');
editor(s,'initial.json · excerpt',['"metrics": {"value": 5.6},','"chart": {','  "labels": ["x"],','  "values": [19, 4, 22, ...]','}'],64,232,550,290,{size:23,lineHeight:41});
editor(s,'feedback.json · excerpt',['"metrics": {"value": 14.3},','"chart": {','  "labels": ["x"],','  "values": [19, 4, 22, ...]','}'],664,232,550,290,{size:23,lineHeight:41});
text(s,'Mean corrected to 14.3',64,567,530,50,31,{bold:true,color:C.cyan});
text(s,'Chart–metric mismatch persists',664,567,550,50,30,{bold:true,color:C.amber});
source(s,'Actual model outputs, abbreviated. The array contains original observations, not the approved aggregate.');

// 16 Replayable evidence is a concrete software contribution.
s=slide('Portable receipts preserve the verification evidence','Implementation: trustverify/audit.py. Shipped example: demo/receipt-example/. CSV x=10,20, missing; weights 1,3,5. Complete-case weighted mean is (10×1+20×3)/(1+3)=17.5. Candidate reports 18. Receipt verdict fails and replay reproduces that failure. It records hashes, contract, report, engine and findings. Hashes are not signatures or proof of authorship.');
editor(s,'receipt.json · excerpt',['"verification": {','  "status": "fail",','  "findings": [{','    "field": "metrics.value",','    "expected": 17.5,','    "actual": 18','  }]','}'],64,235,620,334,{size:25,lineHeight:31});
text(s,'Replay checks',761,233,440,45,30,{bold:true});
for(const [i,v] of ['Exact CSV bytes','Approved contract and report','Recorded engine and verdict'].entries()){
 rule(s,761,305+i*91,445);text(s,v,761,322+i*91,445,65,26);
}
source(s,'Excerpt omits other fields and findings. Receipt hashes detect changes; they do not authenticate authorship.');

// 17 Scope is demonstrated with an actual controlled counterexample.
s=slide('A structured pass can carry an unsupported causal claim','Controlled causal_claim mutation, demo/examples.json. Correct fields are preserved. Narrative says These observational data prove that group membership causes the outcome. The structured checker passes because it does not evaluate narrative meaning. A wrong but approved analysis contract can also pass. Source: tests/test_verifier.py.');
text(s,'“These observational data prove that\ngroup membership causes the outcome.”',64,224,1140,170,43,{bold:true});
rule(s,64,444,1152);text(s,'Structured fields',64,488,650,45,29,{color:C.dim});
text(s,'PASS',821,480,390,65,46,{bold:true,color:C.cyan});
text(s,'Causal conclusion',64,575,650,45,29,{color:C.dim});
text(s,'UNCHECKED',821,573,390,60,34,{bold:true,color:C.amber});
source(s,'A pass concerns selected fields under the approved contract. Data quality and scientific intent remain unchecked.');

// 18 Main-deck closing conclusion.
s=slide('Computational evidence needs a precise assurance claim','Measured conclusions: controlled full verification detects 288/288 supported structured faults, with 0/48 clean false alarms. Extension initial schema compliance is 23/24 in schema mode, full correctness 0/24. JSON-mode feedback repairs 19/24 numeric mappings. Deterministic computation matches the independent oracle on all 60 synthetic and 12 public tasks. These findings are bounded by fixed operations, small local models, one seed and adaptive study design.');
text(s,'288/288',64,214,460,95,69,{bold:true,color:C.cyan});
text(s,'supported structured faults detected',579,238,630,68,29);
rule(s,64,341,1152);
text(s,'23/24',64,371,460,95,69,{bold:true,color:C.blue});
text(s,'schema-valid initial reports\n0/24 complete reports',579,389,630,100,29);
text(s,'Compute supported statistics. Validate every reported field.',64,539,1140,85,35,{bold:true});
source(s,'github.com/naazzarov/trustverify-ai-analysis · Code, raw calls, public data, manuscript and editable slides.');

// 19 Appendix: recent literature with distinctions, not an inflated novelty claim.
s=slide('Recent research and the project’s position','Primary references verified 20 November 2026: Gou et al., CRITIC, ICLR 2024, https://arxiv.org/abs/2305.11738v4; Huang et al., ICLR 2024, https://arxiv.org/abs/2310.01798v2; Geng et al., JSONSchemaBench, 2025v3, https://arxiv.org/abs/2501.10868v3; Jing et al., DSBench, 2025v3, https://arxiv.org/abs/2409.07703v3; Chen et al., ScienceAgentBench, 2025v3, https://arxiv.org/abs/2410.05080v3; Shi et al., TrustDABench, 2026, https://arxiv.org/abs/2608.24145v1; Zhang et al., CausalVerify, 2026v2, https://arxiv.org/abs/2609.07944v2. This project does not reproduce their benchmark scores.');
table(s,[['Research','Year','Design implication'],['CRITIC / intrinsic correction','2024','Compare external feedback with self-review'],['JSONSchemaBench','2025','Separate structure from output quality'],['DSBench / ScienceAgentBench','2025','Evaluate artifacts; add real observations'],['TrustDABench / CausalVerify','2026','State evidence and scientific-validity boundaries']],64,222,1152,342,[400,125,627],{size:24});
text(s,'Contribution: an inspectable verifier with replayable evidence',64,596,1140,43,29,{bold:true,color:C.cyan});
source(s,'Appendix · Full primary references and exact archived versions in paper/refs.bib and docs/literature_review.md.');

// 20 Appendix: raw paired counts and the acquisition limitation.
s=slide('Paired comparisons and realized scope','Source: extension study paired_comparisons and docs/extension_execution_note.md. Initial schema-validity change: 3 improve, 0 regress, p=.25. JSON numeric feedback vs review:19 improve,0 regress,p=.000003814697265625. Schema numeric:18 improve,0 regress,p=.00000762939453125. Tests are exact two-sided McNemar; descriptive secondary comparisons, no multiplicity correction and dependent templates. Planned 3B model could not be fully downloaded/verified; no 3B results are claimed.');
table(s,[['Paired outcome','Improved','Regressed','Exact p'],['Initial schema validity: schema vs JSON','3','0','0.25'],['Numeric: JSON feedback vs review','19','0','0.00000381'],['Numeric: schema feedback vs review','18','0','0.00000763']],64,225,1152,268,[628,162,162,200],{size:23});
text(s,'Planned 3B acquisition did not complete',64,539,1140,43,31,{bold:true,color:C.amber});
text(s,'Realized extension: one capacity, 144 calls. All failures retained.',64,592,1140,43,27,{color:C.dim});
source(s,'Appendix · Small constructed samples and multiple related endpoints limit inference.');

// 21 Appendix: editable reproducibility commands.
s=slide('Reproduction and the live demonstration','All commands run from repository root. Core package, tests, local demo and receipt replay have no third-party runtime dependencies. Optional Matplotlib regenerates figures. python3 scripts/check_study.py verifies all 144 extension requests/responses and recomputes scores offline. python3 scripts/check_results.py checks original pilot evidence. The local service binds 127.0.0.1:8765. No model weights or lecturer-owned slides are redistributed.');
editor(s,'terminal · offline checks',['python3 -m unittest discover -s tests -v','python3 scripts/check_results.py','python3 scripts/check_study.py','python3 -m trustverify.server'],64,225,1152,255,{size:25,lineHeight:44});
text(s,'Custom CSV → approved contract → candidate report → evidence receipt',64,536,1130,88,32,{bold:true,color:C.cyan});
source(s,'Appendix · Open http://127.0.0.1:8765/#theme=dark after starting the local server.');

// 22 Appendix: formulas keep the implementation’s scope inspectable.
s=slide('Supported operations and interpretation','Source: trustverify/core.py and public data task specifications. All operations exclude rows missing required numeric observations. Grouped sums additionally exclude missing groups. Weights must be nonnegative with a positive sum; ratio aggregate denominator must be nonzero. Percentage change follows CSV order. Numeric comparisons use absolute/relative tolerance1e-6, so population counts are not integer-exact. Narrative and analysis intent are not verified.');
table(s,[['Operation','Calculation / required roles'],['Sum / mean','Σx  /  Σx ÷ count; nonmissing x'],['Weighted mean','Σ(x × w) ÷ Σw; complete x and w'],['Percentage ratio','100 × Σx ÷ Σn; complete x and n'],['Grouped sum','Σx for each nonempty group label'],['Percentage change','100 × (last x − first x) ÷ first x']],64,218,1152,344,[330,822],{size:25});
text(s,'A supported calculation can be reproduced and checked precisely',64,593,1140,43,29,{bold:true,color:C.cyan});
source(s,'Appendix · Units are explicit strings; data quality, causal meaning and the choice of method remain outside scope.');

await fs.mkdir(path.join(dir,'renders'),{recursive:true});
for(const [i,s] of P.slides.items.entries()){
 const b=await P.export({slide:s,format:'png',scale:1.5});
 await fs.writeFile(path.join(dir,'renders',`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await b.arrayBuffer()));
}
const candidate=path.join(dir,'candidate.pptx');await(await PresentationFile.exportPptx(P)).save(candidate);
execFileSync('python3',[path.join(root,'presentation/source/metadata.py'),candidate]);
const skill=process.env.PRESENTATION_SKILL;
if(skill){
 const {finalizePresentation}=await import(path.join(skill,'container_tools/artifact_tool_utils.mjs'));
 const owners=[5,7,8,10,13,19,20,22];
 await finalizePresentation({workspaceDir:root,candidatePath:candidate,finalPath,
  pythonExecutable:process.env.PYTHON || 'python3',
  integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
  layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
  layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--validate-bullet-geometry',...owners.flatMap(n=>['--require-native-table-slide',String(n)])],
  explicitTotalSlideCount:22,requiredNativeChartOwnerSlides:[6,11,12,14],requiredNativeTableOwnerSlides:owners,
  materializeLiteralChartWorkbooks:true,verifyArtifactToolImport:true,
  fontPolicy:{basis:'design',families:['Avenir Next','Menlo']},receiptPath:path.join(dir,'validation.json')});
}else{
 await fs.copyFile(candidate,finalPath);
 console.log('Draft exported. Full release validation and chart workbook materialization require PRESENTATION_SKILL.');
}
await fs.writeFile(path.join(dir,'slide-text.json'),JSON.stringify(P.slides.items.map(s=>({notes:s.speakerNotes.text,texts:s.shapes.items.filter(a=>a.text).map(a=>String(a.text))})),null,2));
console.log('Created 22 slides with editable evidence and highlighted code.');
