import fs from 'node:fs/promises';
import path from 'node:path';
import {fileURLToPath} from 'node:url';
import {execFileSync} from 'node:child_process';
import {Presentation, PresentationFile} from '@oai/artifact-tool';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '../..');
const dir = path.resolve(root, '.build/redesign');
const finalPath = path.resolve(process.env.SLIDE_OUTPUT || path.join(dir, 'TrustVerify-Research-Defense.pptx'));
const P = Presentation.create({slideSize:{width:1280, height:720}});
const fromRepo = name => path.join(root, name);
const readJson = async name => JSON.parse(await fs.readFile(fromRepo(name), 'utf8'));
const evidence = await readJson('presentation/evidence.json');
const study = await readJson('presentation/study_evidence.json');
const initial = await readJson('paper/case_initial.json');
const feedback = await readJson('paper/case_feedback_repair.json');

const repoUrl = 'https://github.com/naazzarov/trustverify-ai-analysis';
const C = {
  charcoal:'#111C21', spruce:'#102827', blueblack:'#111F2B', olive:'#222824',
  paper:'#F5F1E7', muted:'#C6D0CC', fine:'#AEBDB9', grid:'#354944',
  mint:'#81DFC0', amber:'#F9CC85', lilac:'#C1B8FF',
  darkAmber:'#453626',
  code:'#1E1E1E', codeHeader:'#303033', codeBorder:'#51565A',
};
const heading = 'Georgia', font = 'Arial', mono = 'Courier New';
const X = 72, W = 1136;
const backgrounds = new WeakMap();
const groups = study.groups['qwen2.5:1.5b'];
function score(mode, condition, field, population='all') {
  return groups[`${mode}/${condition}/${population}`][field];
}
function box(s, x, y, w, h, fill, border='none') {
  return s.shapes.add({
    geometry:'rect', position:{left:x, top:y, width:w, height:h}, fill,
    line:{fill:border, width:border==='none' ? 0 : 1},
  });
}
function text(s, value, x, y, w, h, size=28, {color=C.paper, face=font, bold=false, italic=false, align='left'}={}) {
  const shape = s.shapes.add({
    name:String(value).slice(0,52), geometry:'textbox',
    position:{left:x, top:y, width:w, height:h}, fill:'none', line:{fill:'none', width:0},
  });
  shape.text = value;
  shape.text.style = {typeface:face, fontSize:size, color, bold, italic, alignment:align};
  shape.text.insets = 0;
  return shape;
}
function rule(s, x, y, w=W, color=C.grid) { box(s,x,y,w,1,color); }
function slide(title, {bg=C.charcoal, footer='', href, size=46}={}) {
  const s = P.slides.add();
  s.background.fill = bg;
  backgrounds.set(s,bg);
  if (title) {
    text(s,title,X,56,W,75,size,{face:heading,bold:true});
    rule(s,X,145);
    rule(s,X,145,61,C.mint);
    rule(s,X,658);
    const footerText=text(s,footer,X,675,href?400:1065,24,16,{color:href?C.mint:C.fine});
    if (href) footerText.hyperlink={uri:href,isExternal:true};
    text(s,String(P.slides.items.length).padStart(2,'0'),1153,674,55,24,16,{color:C.fine,align:'right'});
  }
  return s;
}
function caption(s, value, x, y, w, {color=C.muted, size=23}={}) {
  return text(s,value,x,y,w,73,size,{color});
}
function metric(s, value, label, x,y,w,{color=C.mint,size=92}={}) {
  text(s,value,x,y,w,size+31,size,{face:heading,bold:true,color});
  caption(s,label,x+3,y+size+30,w-3,{size:24});
}
async function img(s, file, alt, x,y,w,h, options={}) {
  const blob = await fs.readFile(fromRepo(file));
  s.images.add({
    blob:blob.buffer.slice(blob.byteOffset,blob.byteOffset+blob.byteLength),
    contentType:'image/png', alt, position:{left:x,top:y,width:w,height:h},
    fit:'contain', ...options,
  });
}
function table(s, values, x,y,w,h,widths,{heat=false,size=25,header=true}={}) {
  const t = s.tables.add({
    rows:values.length, columns:values[0].length, left:x, top:y, width:w, height:h,
    values, columnWidths:widths,
  });
  const bg = backgrounds.get(s);
  t.borders.assign({fill:bg,width:2,style:'solid'});
  t.cells.block({row:0,column:0,rowCount:values.length,columnCount:values[0].length}).assign({
    anchor:'center',
  });
  for (let row=0; row<values.length; row++) {
    for (let col=0; col<values[row].length; col++) {
      const cell=t.getCell(row,col), top=header&&row===0;
      let fill=top ? '#31534A' : row%2 ? '#1B332F' : '#203B35';
      let color=top||col===0 ? C.paper : C.muted;
      if (heat && !top && col>0) {
        const [n,d]=String(values[row][col]).split('/').map(Number);
        const fraction=n/d;
        fill=fraction===0 ? '#1D292C' : fraction<.5 ? '#263A40' : fraction<.9 ? '#30504D' : '#32644F';
        color=fraction===0 ? C.fine : fraction>=.9 ? '#F0FFF6' : C.paper;
        if (col===values[0].length-1 && fraction===0) { fill=C.darkAmber; color=C.amber; }
      }
      cell.fill=fill;
      cell.text.style={typeface:font,fontSize:size,color,bold:top||col===0||(heat&&col>0),
        alignment:heat&&col>0?'center':'left'};
    }
  }
  return t;
}
function chart(s,categories,series,x,y,w,h,{horizontal=false,max=24,step=6,legend=false,gap=108}={}) {
  const bg=backgrounds.get(s);
  const line={fill:C.grid,width:1};
  return s.charts.add('bar',{
    position:{left:x,top:y,width:w,height:h}, categories, series,
    chartFill:bg, plotAreaFill:bg, chartLine:{fill:'none',width:0}, plotAreaLine:{fill:'none',width:0},
    barOptions:{direction:horizontal?'bar':'column',grouping:'clustered',gapWidth:gap},
    hasLegend:legend, legend:{position:'bottom',textStyle:{typeface:font,fontSize:21,fill:C.paper}},
    xAxis:{textStyle:{typeface:font,fontSize:22,fill:C.paper},line,majorGridlines:null},
    yAxis:{min:0,max,majorUnit:step,numberFormatCode:'0',textStyle:{typeface:font,fontSize:18,fill:C.muted},
      line:{fill:'none',width:0},majorGridlines:line},
    dataLabels:{showValue:true,position:'outEnd',numberFormatCode:'0',
      textStyle:{typeface:font,fontSize:24,fill:C.paper,bold:true}},
  });
}
function linkArrow(s,x,y,w=44) {
  s.shapes.add({geometry:'rightArrow',position:{left:x,top:y,width:w,height:17},fill:C.mint,line:{fill:'none',width:0}});
}
function stage(s,title,detail,x,y,w) {
  rule(s,x,y,w,C.mint);
  text(s,title,x,y+22,w,45,30,{bold:true});
  caption(s,detail,x,y+76,w,{size:23});
}

const tokens = {key:'#A0D9FF', string:'#F3AD8D', number:'#C9E9A5', bracket:'#F6D36C', plain:'#E7E7E7'};
function highlightJson(line) {
  const pattern=/("[^"\\]*(?:\\.[^"\\]*)*"(?=\s*:))|("[^"\\]*(?:\\.[^"\\]*)*")|(-?\d+(?:\.\d+)?)|([{}\[\]])/g;
  const runs=[];
  let start=0;
  for (const match of line.matchAll(pattern)) {
    if (match.index>start) runs.push({run:line.slice(start,match.index)});
    const color=match[1]?tokens.key:match[2]?tokens.string:match[3]?tokens.number:tokens.bracket;
    runs.push({run:match[0],style:{color}});
    start=match.index+match[0].length;
  }
  if(start<line.length) runs.push({run:line.slice(start)});
  return runs;
}
function highlightShell(line) {
  const [command,...segments]=line.split(' ');
  return [
    {run:command,style:{color:tokens.key}},
    ...segments.map(segment=>({run:` ${segment}`,style:{color:segment[0]==='-'?C.lilac:segment.endsWith('.py')?tokens.string:tokens.plain}})),
  ];
}
function editor(s,name,lines,x,y,w,{size=25,step=40,focus=[],language='json'}={}) {
  const pad=16, header=48, gutter=60, h=header+2*pad+lines.length*step;
  box(s,x,y,w,h,C.code,C.codeBorder);
  box(s,x+1,y+1,w-2,header,C.codeHeader);
  text(s,name,x+20,y+13,w-40,28,19,{face:mono,color:'#F0F0EE',bold:true});
  box(s,x+gutter-11,y+header+pad,1,lines.length*step,'#45454B');
  for (const [i,line] of lines.entries()) {
    const rowY=y+header+pad+i*step;
    if (focus.includes(i)) {
      box(s,x+gutter-4,rowY-2,w-gutter-9,step,'#2C3B34');
      box(s,x+gutter-4,rowY-2,3,step,C.mint);
    }
    text(s,String(i+1),x+10,rowY+3,27,28,17,{face:mono,color:'#A5ADB0',align:'right'});
    const code=text(s,'',x+gutter+7,rowY,w-gutter-23,step,size,{face:mono,color:tokens.plain});
    code.text={runs:language==='shell'?highlightShell(line):highlightJson(line)};
  }
}

let s = slide('',{bg:C.spruce});
await img(s,'presentation/assets/verification-cover.png','Conceptual artwork of layered analysis evidence',630,0,650,720,
  {fit:'cover',crop:{left:.39,top:0,right:.04,bottom:0}});
box(s,0,0,650,720,C.spruce);
box(s,X,61,171,56,'#FFFFFF');
await img(s,'paper/figures/SCU_TITLE.png','Official Sichuan University wordmark',X+8,67,155,44);
text(s,'Sichuan University',266,75,355,38,24,{bold:true});
rule(s,X,146,515);
text(s,'TrustVerify',X,204,554,128,84,{face:heading,bold:true});
text(s,'Executable verification of\nAI-generated data analysis',X+4,335,518,105,35,{color:C.paper});
rule(s,X,541,515);
text(s,'BAHODIR KODIRJON UGLI NAZAROV',X,570,560,38,23,{bold:true});
text(s,'New Software Technology  /  November 2026',X,618,540,35,20,{color:C.muted});

s = slide('One report, two different values',{bg:C.olive,footer:'Controlled fault in ratio-02. Both percentages are rounded to two decimals.'});
metric(s,'266.71%','Value in the candidate report',X,208,510,{color:C.amber,size:101});
metric(s,'263.46%','Value from independent computation',678,208,530,{size:101});
rule(s,X,430);
text(s,'3.25 percentage points',X,460,1130,77,50,{face:heading,bold:true});
caption(s,'Both values are evaluated against the same CSV and approved contract.\nThe verifier recomputes 100 × 137 ÷ 52 from nine complete rows.',X+3,550,W,{size:25});

s = slide('The analysis contract',{bg:C.blueblack,footer:'The verifier excludes rows missing any value required by the selected operation.'});
editor(s,'contract.json',['{','  "op": "ratio",','  "column": "x",','  "denominator": "n",','  "unit": "%"','}'],X,202,616,{size:29,step:49,focus:[1]});
text(s,'What gets checked',763,218,445,54,31,{face:heading,bold:true});
for (const [i,[main,sub]] of [['Metrics','Labels and computed values'],['Unit and rows','Unit string and valid-row count'],['Chart data','Labels and reported values']].entries()) {
  const y=287+i*101;
  rule(s,763,y,445);
  text(s,main,763,y+13,445,37,27,{bold:true,color:C.mint});
  caption(s,sub,763,y+50,445,{size:22});
}

s = slide('How TrustVerify checks a report',{bg:C.spruce,footer:'Verification follows the approved contract. Review the choice of analysis separately.'});
stage(s,'Approved inputs','Source CSV\nand analysis contract',X,230,280);
linkArrow(s,376,267);
stage(s,'Recompute','Python Decimal\nreference fields',455,230,280);
linkArrow(s,758,267);
stage(s,'Compare','Check each candidate field.\nPass, fail or abstain.',836,230,372);
rule(s,X,435);
text(s,'Independent evaluation',X,474,512,55,36,{face:heading,bold:true});
text(s,'Separate SQLite queries generate the study’s reference answers.',X,546,W,56,28,{color:C.muted});

s = slide('Three sources of evidence',{footer:'The controlled benchmark uses designed faults. The two model studies preserve actual responses.'});
table(s,[
  ['Study','Tasks and comparisons','Evidence retained'],
  ['Controlled benchmark','48 held-out synthetic tasks','48 clean + 336 faulty reports'],
  ['Initial model pilot','Qwen2.5 0.5B and 1.5B','144 calls across both models'],
  ['Paired extension','24 new tasks at Qwen2.5 1.5B','144 calls across both formats'],
],X,208,W,276,[295,444,397],{size:25});
text(s,'288',X,518,236,110,77,{face:heading,bold:true,color:C.mint});
text(s,'recorded model calls across the pilot and extension',321,553,870,65,29,{color:C.paper});

s = slide('Detection across three checking layers',{bg:C.spruce,footer:'The 336 faults include 48 unsupported causal claims. All counts come from controlled injections.'});
text(s,'Injected faults detected',X,192,710,40,24,{bold:true});
chart(s,['Numbers only','Schema + numbers','Full verification'],[
  {name:'Detected faults',values:evidence.fault_detection.detected,fill:C.mint,
   points:[{idx:0,fill:'#708883'},{idx:1,fill:C.lilac},{idx:2,fill:C.mint}]},
],55,242,782,338,{horizontal:true,max:336,step:84,gap:86});
metric(s,'85.7%','of all injected faults',878,221,330,{size:75});
rule(s,882,393,326);
text(s,'288/288',882,415,326,50,35,{bold:true});
caption(s,'Supported structured faults detected',882,472,326,{size:23});
text(s,'0/48 false alarms',882,566,326,47,28,{bold:true,color:C.mint});

s = slide('Detection by injected fault',{footer:'Each cell represents 48 deliberate mutations. “Missing chart” removes the chart field.'});
table(s,[
 ['Checker','Number','Unit','Rows','Chart value','Missing chart','NaN','Causal prose'],
 ['Numbers only','48/48','0/48','0/48','0/48','0/48','48/48','0/48'],
 ['Schema + numeric','48/48','0/48','0/48','0/48','48/48','48/48','0/48'],
 ['Full','48/48','48/48','48/48','48/48','48/48','48/48','0/48'],
],X,218,W,290,[213,107,92,92,145,155,96,236],{heat:true,size:21});
text(s,'Causal claims sit outside all three checks',X,554,W,60,37,{face:heading,bold:true,color:C.amber});

s = slide('Original pilot results',{bg:C.blueblack,footer:'Complete correctness requires simultaneous agreement on metrics, unit, row count and chart data.'});
text(s,'Complete reports (out of 24)',X,181,W,44,24,{bold:true});
table(s,[
 ['Model','Initial','Self-review','Executable feedback'],
 ['Qwen2.5 0.5B','0/24','0/24','0/24'],
 ['Qwen2.5 1.5B','0/24','0/24','0/24'],
],X,241,W,213,[310,225,240,361],{size:27});
text(s,'19/24',X,507,340,100,73,{face:heading,bold:true,color:C.mint});
text(s,'numeric mappings agree after feedback at 1.5B',435,539,773,60,29,{bold:true});

s = slide('Paired study design',{bg:C.spruce,footer:'Identical prompts and data in both formats. Seed 31415, maximum 512 generated tokens per call.'});
text(s,'24 shared tasks',X,183,660,70,47,{face:heading,bold:true});
text(s,'12 synthetic and 12 World Bank tasks',689,206,519,50,25,{color:C.muted});
for (const [i,mode] of ['JSON mode','Schema mode'].entries()) {
  const y=306+i*137;
  rule(s,X,y-10);
  text(s,mode,X,y+22,300,54,33,{bold:true,color:i?C.lilac:C.mint});
  linkArrow(s,384,y+33,44);
  text(s,'Initial report',481,y+22,300,54,33,{bold:true});
  linkArrow(s,786,y+33,44);
  text(s,'Self-review',878,y+3,330,48,29,{bold:true});
  text(s,'Executable feedback',878,y+50,330,44,26,{color:C.muted});
}
text(s,'Both follow-ups independently start from the same initial report.',X,595,W,44,24,{color:C.muted});

s = slide('World Bank observations',{bg:C.blueblack,footer:'World Development Indicators, CC BY 4.0. The cohorts are curated subsets used for controlled comparison.'});
metric(s,'2024','Population and urban-share cross-sections',X,196,535,{size:83});
metric(s,'2013–2024','Population series for Uzbekistan and Japan',668,196,540,{color:C.lilac,size:83});
table(s,[
  ['Cohort A','CHN  IDN  IND  PAK  UZB  KAZ','DEU  FRA  NGA  KEN  BRA  MEX'],
  ['Cohort B','JPN  VNM  BGD  LKA  TUR  GEO','GBR  ITA  ZAF  ETH  ARG  COL'],
],X,421,W,126,[159,474,503],{header:false,size:23});
text(s,'Regional totals cover the selected countries in each cohort.',X,580,W,46,26,{color:C.muted});

s = slide('More reports passed the schema',{bg:C.spruce,footer:'Qwen2.5 1.5B extension. Three initial reports gained schema compliance in the paired comparison (p = 0.25).'});
text(s,'Schema-valid initial reports (out of 24)',X,182,720,42,25,{bold:true});
chart(s,['JSON mode','Schema mode'],[
 {name:'Schema-valid reports',values:['json','schema'].map(mode=>score(mode,'initial','schema_valid')),fill:C.mint,
  points:[{idx:0,fill:C.mint},{idx:1,fill:C.lilac}]},
],68,232,725,348,{max:24,step:6,gap:138});
rule(s,843,252,365);
metric(s,'0/24','complete initial reports\nin either mode',843,298,365,{color:C.amber,size:82});

s = slide('Executable feedback corrects more numbers',{footer:'Each condition uses the same 24 tasks. Numerical agreement is a secondary outcome scored within the stated tolerance.',size:45});
text(s,'Reports with correct metric labels and values (out of 24)',X,181,W,42,25,{bold:true});
const conditions=['initial','self_review','feedback_repair'];
chart(s,['Initial','Self-review','Executable feedback'],[
  {name:'JSON mode',values:conditions.map(c=>score('json',c,'numeric')),fill:C.mint},
  {name:'Schema mode',values:conditions.map(c=>score('schema',c,'numeric')),fill:C.lilac},
],70,238,1136,354,{legend:true,gap:120});
text(s,'Feedback includes values independently recomputed from the CSV.',X,603,W,40,24,{color:C.muted});

s = slide('Chart agreement stays near zero',{bg:C.blueblack,footer:'Each cell is out of 24. A complete report must satisfy every checked field simultaneously.'});
const fieldRows=[['Mode and condition','Schema','Metrics','Unit','Rows','Chart','Complete']];
for (const mode of ['json','schema']) {
  for (const condition of conditions) {
    const tag={initial:'initial',self_review:'review',feedback_repair:'feedback'}[condition];
    fieldRows.push([
      `${mode==='json'?'JSON':'Schema'} / ${tag}`,
      ...['schema_valid','numeric','unit','rows','chart','correct'].map(key=>`${score(mode,condition,key)}/24`),
    ]);
  }
}
table(s,fieldRows,X,201,W,366,[291,139,140,127,125,137,177],{heat:true,size:23});
text(s,'Only one chart agrees after feedback in each mode.',X,592,W,52,30,{bold:true,color:C.amber});

s = slide('Numerical repair on public and synthetic data',{bg:C.spruce,footer:'Feedback condition only. Each stratum has 12 tasks from six fixed operations.',size:44});
text(s,'Correct metric labels and values after feedback (out of 12)',X,183,1136,43,25,{bold:true});
chart(s,['Synthetic tasks','World Bank tasks'],[
  {name:'JSON mode',values:['synthetic','public'].map(p=>score('json','feedback_repair','numeric',p)),fill:C.mint},
  {name:'Schema mode',values:['synthetic','public'].map(p=>score('schema','feedback_repair','numeric',p)),fill:C.lilac},
],66,238,766,356,{max:12,step:3,legend:true,gap:84});
rule(s,861,274,347);
metric(s,'0/12','complete reports in\nevery group shown',858,311,350,{color:C.amber,size:73});

s = slide('The mean is fixed. The chart still fails.',{bg:C.olive,footer:'Recorded response pair for mean-06 in schema mode. Excerpts abbreviate the chart array.'});
const excerpt = candidate => [
  `"metrics": {"value": ${candidate.metrics.value}},`,
  '"chart": {',
  `  "labels": ${JSON.stringify(candidate.chart.labels)},`,
  `  "values": [${candidate.chart.values.slice(0,3).join(', ')}, …]`,
  '}',
];
text(s,'Initial model report',X,177,546,38,24,{color:C.muted,bold:true});
text(s,'After executable feedback',662,177,546,38,24,{color:C.muted,bold:true});
editor(s,'initial.json',excerpt(initial),X,227,546,{size:26,step:45,focus:[0]});
editor(s,'feedback.json',excerpt(feedback),662,227,546,{size:26,step:45,focus:[0]});
text(s,'The mean changes to 14.3',X,565,546,51,30,{face:heading,bold:true,color:C.mint});
text(s,'The chart keeps the input values',662,565,546,59,29,{face:heading,bold:true,color:C.amber});

s = slide('A verification receipt can be replayed',{bg:C.blueblack,footer:'The excerpt shows one recorded finding. The receipt also records input hashes, the contract and the checker version.'});
const receipt=await readJson('demo/receipt-example/receipt.json');
const finding=receipt.verification.findings[0];
editor(s,'receipt.json',[
 '"verification": {',
 `  "status": "${receipt.verification.status}",`,
 '  "findings": [{',
 `    "field": "${finding.field}",`,
 `    "expected": ${finding.expected},`,
 `    "actual": ${finding.actual}`,
 '  }]',
 '}',
],X,191,622,{size:25,step:43,focus:[4,5]});
text(s,'Weighted mean',756,221,452,58,39,{face:heading,bold:true});
text(s,'17.5 expected',756,304,452,59,37,{bold:true,color:C.mint});
text(s,'18 reported',756,371,452,55,34,{bold:true,color:C.amber});
rule(s,756,463,452);
caption(s,'Replaying the receipt reproduces\nthe failed check.',756,504,452,{size:26});

s = slide('What a pass leaves unchecked',{bg:C.olive,footer:'Controlled narrative-only mutation. The verified metrics, units, row count and chart data stay correct.'});
text(s,'“These observational data prove that group\nmembership causes the outcome.”',X,224,W,150,45,{face:heading,italic:true});
rule(s,X,435);
text(s,'Structured fields',X,465,560,50,29,{color:C.muted});
text(s,'PASS',773,452,435,59,44,{bold:true,color:C.mint});
text(s,'Causal conclusion',X,557,560,50,29,{color:C.muted});
text(s,'UNCHECKED',773,548,435,59,37,{bold:true,color:C.amber});

s = slide('What the experiments establish',{bg:C.spruce,footer:repoUrl.replace('https://',''),href:repoUrl});
for (const [i,[n,description,color]] of [
  ['288/288','Supported structured faults detected',C.mint],
  ['19/24','Correct numerical mappings after JSON-mode feedback',C.paper],
  ['0/24','Complete reports in each extension condition',C.amber],
].entries()) {
  const y=182+i*126;
  text(s,n,X,y,378,104,67,{face:heading,bold:true,color});
  text(s,description,485,y+28,723,64,27,{color:C.paper});
  rule(s,X,y+107);
}
text(s,'A corrected number still needs a matching chart, unit and row count.',X,588,W,55,27,{bold:true});

s = slide('Recent research and design choices',{footer:'References and archived versions are listed in the report and repository.'});
table(s,[
  ['Research','Year','Influence on TrustVerify'],
  ['CRITIC / intrinsic correction','2024','Compare executable feedback with self-review'],
  ['JSONSchemaBench','2025','Measure format and numerical agreement separately'],
  ['DSBench / ScienceAgentBench','2025','Evaluate actual outputs and add public observations'],
  ['TrustDABench / CausalVerify','2026','Define the limits of structured verification'],
],X,202,W,357,[386,110,640],{size:23});
text(s,'TrustVerify adds a working verifier and replayable evidence.',X,596,W,45,29,{bold:true,color:C.mint});

s = slide('Paired comparisons and study scope',{footer:'Exact two-sided McNemar comparisons. Correlated tasks and endpoints limit inference.'});
table(s,[
  ['Comparison','Improved','Regressed','Exact p'],
  ['Schema validity: schema vs JSON initially','3','0','0.25'],
  ['Metrics: JSON feedback vs review','19','0','0.00000381'],
  ['Metrics: schema feedback vs review','18','0','0.00000763'],
],X,201,W,285,[565,165,165,241],{size:25});
text(s,'The completed extension tests Qwen2.5 1.5B only.',X,533,W,47,33,{face:heading,bold:true,color:C.amber});
text(s,'The planned 3B model download failed before testing.',X,591,W,38,24,{color:C.muted});

s = slide('Reproducing the results',{bg:C.blueblack,footer:'Run from the repository root. The local demo opens at http://127.0.0.1:8765/#theme=dark.'});
editor(s,'Terminal',[
 'python3 -m unittest discover -s tests -v',
 'python3 scripts/check_results.py',
 'python3 scripts/check_study.py',
 'python3 -m trustverify.server',
],X,203,W,{size:30,step:52,focus:[2],language:'shell'});
text(s,'The study check recalculates scores from the archived requests and responses.',X,538,W,63,29,{color:C.muted});

s = slide('Supported operations',{footer:'The analysis contract specifies the relevant columns and output unit. Missing required values are excluded.'});
table(s,[
  ['Operation','Calculation'],
  ['Sum','Σx'],
  ['Mean','Σx ÷ count'],
  ['Weighted mean','Σ(x × w) ÷ Σw'],
  ['Percentage ratio','100 × Σx ÷ Σn'],
  ['Grouped sum','Σx for each nonempty group label'],
  ['Percentage change','100 × (last x − first x) ÷ first x'],
],X,194,W,410,[400,736],{size:25});

const notes = [
  "TrustVerify. Executable Verification of AI-Generated Data Analysis. BAHODIR KODIRJON UGLI NAZAROV, Software Engineering, Sichuan University. New Software Technology, Dr. Hu Dasha. November 2026. University wordmark: unchanged SCU_TITLE.png supplied in the course-paper template. Background: conceptual verification artwork, not an experimental image.",
  "Controlled ratio-02 example, demo/examples.json. 100 × 137 / 52 = 263.46153846153845%; nine complete observations. The deliberately injected metric adds 3.25 percentage points. This is not a natural model output.",
  "The contract is human approved. It fixes operation, columns, unit and missing-value semantics. The ratio is a ratio of sums, not an average of row ratios. The checker cannot infer whether this is the right research question. Source: trustverify/core.py, data/tasks.jsonl.",
  "Production: trustverify/core.py uses Decimal with a 40-digit context and never reads evaluator gold files. Evaluation: trustverify/benchmark.py uses independently implemented SQLite queries. No model-generated code executes. Both follow the approved contract, so a shared specification error remains possible.",
  "Sources: results/fault_injection.json, results/live_pilot.json, results/qwen-1.5b/live_pilot.json, results/study/qwen2.5-1.5b/study.json. The original pilot has 144 calls; the extension adds 144. The planned 3B download failed and produced no scored run; it must not be counted as 432 calls.",
  "Source: results/fault_injection.json. Numeric-only detects 96, schema+numeric 144, full 288. All 288 supported structured mutations are detected. Causal prose is outside scope. Every profile has zero false alarms on 48 clean reports. Counts describe designed coverage, not natural LLM error prevalence.",
  "Source: results/fault_injection.json. Forty-eight cases per cell. Full structured checking adds unit, row-count and chart validation; no profile checks the meaning of a narrative.",
  "Sources: both original live_pilot.json files and results/secondary_diagnostics.json. Every generated condition scores 0/24 on full structured correctness. Qwen2.5 1.5B feedback nevertheless repairs 19/24 numerical mappings. The numerical endpoint is exploratory. The capacity check followed inspection of the 0.5B pilot.",
  "Frozen protocol: docs/protocol_v2.md; realized scope: docs/extension_execution_note.md. Twenty-four new tasks: twelve previously uncalled synthetic variants and twelve public tasks. Identical system prompt and schema text; only API format differs. Each second call starts from the same initial response. Counterbalanced order. Actual 1.5B run: 144 calls. Planned 3B run was not realized.",
  "Source: World Bank WDI, population SP.POP.TOTL and urban population SP.URB.TOTL. Official bulk exports updated 11 November 2026; accessed 20 November 2026. Original ZIPs, JSON metadata, transformations and hashes are retained under data/public/source. CC BY 4.0, attribution World Bank. National urban definitions differ. Country subsets are curated and not representative global samples.",
  "Source: results/study/qwen2.5-1.5b/study.json, groups json/initial/all and schema/initial/all. Initial schema validity 20/24 versus 23/24. Complete correctness 0/24 in both. Paired schema-validity contrast: 3 improve, 0 regress, exact two-sided McNemar p=0.25. One schema-mode initial response truncates and remains scored. A zero complete score is a floor effect, not proof of equivalence.",
  "Source: results/study/qwen2.5-1.5b/study.json. Numerical mapping requires matching metric keys and values within abs/relative tolerance 1e-6. JSON: initial 0, self-review 0, feedback 19. Schema: 0,0,18. This secondary endpoint excludes units, row counts and chart consistency. Expected values are supplied by the executable feedback, so this is not unaided model reasoning.",
  "Source: results/study/qwen2.5-1.5b/study.json. Each field count is independent, denominator 24. Complete correctness requires schema compliance and simultaneous metric, unit, rows and chart agreement. Narrative meaning is excluded. JSON feedback chart 1/24; schema feedback chart 1/24; all complete-report outcomes 0.",
  "Source: extension study groups */feedback_repair/synthetic and */feedback_repair/public. Numeric correctness: JSON synthetic 10/12, public 9/12; schema synthetic 10/12, public 8/12. Complete correctness is zero in all four cells. Shared countries/templates make these descriptive strata, not independent populations.",
  "Actual retained response pair: mean-06, schema mode, Qwen2.5 1.5B. Raw logs under results/study/qwen2.5-1.5b/raw/mean-06-schema-{initial,feedback_repair}.json. Initial metric 5.6; after feedback 14.3. The chart keeps label x and the twelve original observations, rather than one value metric. Excerpts omit the unit, row count and narrative; ellipsis abbreviates the observed array.",
  "Implementation: trustverify/audit.py. Shipped example: demo/receipt-example/. CSV x=10,20, missing; weights 1,3,5. Complete-case weighted mean is (10×1+20×3)/(1+3)=17.5. Candidate reports 18. Receipt verdict fails and replay reproduces that failure. It records hashes, contract, report, engine and findings. Hashes are not signatures or proof of authorship.",
  "Controlled causal_claim mutation, demo/examples.json. Correct fields are preserved. Narrative says These observational data prove that group membership causes the outcome. The structured checker passes because it does not evaluate narrative meaning. A wrong but approved analysis contract can also pass. Source: tests/test_verifier.py.",
  "Measured conclusions: controlled full verification detects 288/288 supported structured faults, with 0/48 clean false alarms. Extension initial schema compliance is 23/24 in schema mode, full correctness 0/24. JSON-mode feedback repairs 19/24 numeric mappings. Deterministic computation matches the independent oracle on all 60 synthetic and 12 public tasks. These findings are bounded by fixed operations, small local models, one seed and adaptive study design.",
  "Primary references verified 20 November 2026: Gou et al., CRITIC, ICLR 2024, https://arxiv.org/abs/2305.11738v4; Huang et al., ICLR 2024, https://arxiv.org/abs/2310.01798v2; Geng et al., JSONSchemaBench, 2025v3, https://arxiv.org/abs/2501.10868v3; Jing et al., DSBench, 2025v3, https://arxiv.org/abs/2409.07703v3; Chen et al., ScienceAgentBench, 2025v3, https://arxiv.org/abs/2410.05080v3; Shi et al., TrustDABench, 2026, https://arxiv.org/abs/2608.24145v1; Zhang et al., CausalVerify, 2026v2, https://arxiv.org/abs/2609.07944v2. This project does not reproduce their benchmark scores.",
  "Source: extension study paired_comparisons and docs/extension_execution_note.md. Initial schema-validity change: 3 improve, 0 regress, p=.25. JSON numeric feedback vs review:19 improve,0 regress,p=.000003814697265625. Schema numeric:18 improve,0 regress,p=.00000762939453125. Tests are exact two-sided McNemar; descriptive secondary comparisons, no multiplicity correction and dependent templates. Planned 3B model could not be fully downloaded/verified; no 3B results are claimed.",
  "All commands run from repository root. Core package, tests, local demo and receipt replay have no third-party runtime dependencies. Optional Matplotlib regenerates figures. python3 scripts/check_study.py verifies all 144 extension requests/responses and recomputes scores offline. python3 scripts/check_results.py checks original pilot evidence. The local service binds 127.0.0.1:8765. No model weights or lecturer-owned slides are redistributed.",
  "Source: trustverify/core.py and public data task specifications. All operations exclude rows missing required numeric observations. Grouped sums additionally exclude missing groups. Weights must be nonnegative with a positive sum; ratio aggregate denominator must be nonzero. Percentage change follows CSV order. Numeric comparisons use absolute/relative tolerance1e-6, so population counts are not integer-exact. Narrative and analysis intent are not verified."
];
for (const [index,page] of P.slides.items.entries()) page.speakerNotes.text=notes[index];

const renders=path.join(dir,'renders');
await fs.mkdir(renders,{recursive:true});
await fs.mkdir(path.dirname(finalPath),{recursive:true});
for (const [i,page] of P.slides.items.entries()) {
  const preview=await P.export({slide:page,format:'png',scale:1.5});
  await fs.writeFile(path.join(renders,`slide-${String(i+1).padStart(2,'0')}.png`),new Uint8Array(await preview.arrayBuffer()));
}
const candidate=path.join(dir,'candidate.pptx');
await (await PresentationFile.exportPptx(P)).save(candidate);
execFileSync('python3',[fromRepo('presentation/source/metadata.py'),candidate]);

const skill=process.env.PRESENTATION_SKILL;
if (skill) {
  const {finalizePresentation}=await import(path.join(skill,'container_tools/artifact_tool_utils.mjs'));
  const tables=[5,7,8,10,13,19,20,22];
  await finalizePresentation({
    workspaceDir:root,candidatePath:candidate,finalPath,
    pythonExecutable:process.env.PYTHON || 'python3',
    integrityValidatorPath:path.join(skill,'container_tools/inspect_presentation_package_integrity.py'),
    layoutValidatorPath:path.join(skill,'container_tools/inspect_presentation_layout_geometry.py'),
    layoutArgs:['--expected-slide-size-emu','12192000,6858000','--validate-heading-fit','--validate-bullet-geometry',
      ...tables.flatMap(n=>['--require-native-table-slide',String(n)])],
    explicitTotalSlideCount:22,requiredNativeChartOwnerSlides:[6,11,12,14],requiredNativeTableOwnerSlides:tables,
    materializeLiteralChartWorkbooks:true,verifyArtifactToolImport:true,
    fontPolicy:{basis:'design',families:[heading,font,mono]},
    receiptPath:path.join(dir,path.basename(finalPath)+'.validation.json'),
  });
} else {
  await fs.copyFile(candidate,finalPath);
  console.log('Draft exported. Final validation and chart workbooks require PRESENTATION_SKILL.');
}
