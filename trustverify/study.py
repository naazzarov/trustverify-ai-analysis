"""Frozen paired extension: JSON versus schema, synthetic versus public data.

The schema supplies structure, never gold values. Evaluation uses SQLite;
feedback uses the production checker. All content failures remain in the logs.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
import statistics
import subprocess
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .benchmark import dump, environment, gold_correct, load_tasks, wilson
from .core import close, is_numeric, load_rows, repair, verify
from .live import BRANCHES, decode, post

SCHEMA = {
    'type': 'object', 'additionalProperties': False,
    'required': ['metrics', 'unit', 'rows_used', 'chart', 'narrative'],
    'properties': {
        'metrics': {'type': 'object', 'minProperties': 1,
                    'additionalProperties': {'type': 'number'}},
        'unit': {'type': 'string'},
        'rows_used': {'type': 'integer', 'minimum': 0},
        'chart': {'type': 'object', 'additionalProperties': False,
                  'required': ['labels', 'values'], 'properties': {
                      'labels': {'type': 'array', 'minItems': 1, 'items': {'type': 'string'}},
                      'values': {'type': 'array', 'minItems': 1, 'items': {'type': 'number'}}}},
        'narrative': {'type': 'string', 'maxLength': 160}}}
SYSTEM = '''You are a careful data analyst. Follow the approved contract exactly.
Return ONLY one JSON object matching the schema below.
Use metric key "value" for a single answer, or group labels for grouped answers.
unit must equal the exact contract unit. rows_used counts complete observations.
Chart labels must be metric keys; chart values must match those metric values.
Narrative must be one short descriptive sentence. Do not claim causation.
Blank CSV cells are missing, not zero. Do not round intermediate calculations.
Output fractional numeric results to at least six decimal places.
Required JSON schema (structure only; it contains no reference answer):
''' + json.dumps(SCHEMA, sort_keys=True, separators=(',', ':'))
OPTIONS = {'temperature': 0, 'seed': 31415, 'num_ctx': 4096, 'num_predict': 512}
FORMATS = ('json', 'schema')
CONDITIONS = ('initial', 'self_review', 'feedback_repair')


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    allow_nan=False).encode()).hexdigest()


def file_digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def schema_valid(report):
    """Validate exactly the fixed SCHEMA above, without a runtime dependency."""
    if not isinstance(report, dict) or set(report) != set(SCHEMA['required']): return False
    m = report['metrics']
    if not isinstance(m, dict) or not m or not all(isinstance(k, str) and is_numeric(v) for k,v in m.items()): return False
    if not isinstance(report['unit'], str) or type(report['rows_used']) is not int or report['rows_used'] < 0: return False
    if not isinstance(report['narrative'], str) or len(report['narrative']) > 160: return False
    c = report['chart']
    return (isinstance(c, dict) and set(c) == {'labels', 'values'}
        and isinstance(c['labels'], list) and bool(c['labels']) and all(isinstance(k, str) for k in c['labels'])
        and isinstance(c['values'], list) and bool(c['values']) and all(is_numeric(v) for v in c['values']))


def fields(report, gold):
    obj = report if isinstance(report, dict) else {}
    metric = obj.get('metrics')
    numeric = isinstance(metric, dict) and set(metric) == set(gold['metrics']) and all(
        close(metric[k], v) for k,v in gold['metrics'].items())
    c = obj.get('chart'); chart = False
    if isinstance(c, dict) and isinstance(c.get('labels'), list) and isinstance(c.get('values'), list):
        labels, values = c['labels'], c['values']
        chart = (all(isinstance(k, str) for k in labels) and len(labels) == len(values)
            and len(labels) == len(set(labels)) and set(labels) == set(gold['metrics'])
            and all(close(v, gold['metrics'][k]) for k,v in zip(labels, values)))
    return {'numeric': bool(numeric), 'unit': obj.get('unit') == gold['unit'],
            'rows': type(obj.get('rows_used')) is int and obj['rows_used'] == gold['rows_used'],
            'chart': bool(chart)}


def paired(a, b):
    if not a or len(a) != len(b): raise ValueError('Equal nonempty paired samples required')
    improved = sum(not x and y for x,y in zip(a,b))
    regressed = sum(x and not y for x,y in zip(a,b))
    d = improved + regressed
    p = min(1.0, 2 * sum(math.comb(d,k) for k in range(min(improved,regressed)+1)) / 2**d) if d else 1.0
    return {'n': len(a), 'improved': improved, 'regressed': regressed,
            'both_correct': sum(x and y for x,y in zip(a,b)),
            'both_incorrect': sum(not x and not y for x,y in zip(a,b)),
            'difference': (sum(b)-sum(a))/len(a), 'exact_mcnemar_two_sided_p': p}


def tasks_and_gold(root):
    synthetic = [dict(t, domain='synthetic') for t in load_tasks(root)
                 if int(t['id'].rsplit('-',1)[1]) in (6,7)]
    public = json.loads((root/'data/public/tasks.json').read_text())
    tasks = sorted(synthetic + public, key=lambda t: (t['family'], t['domain'], t['id']))
    if len(tasks) != 24 or len({t['id'] for t in tasks}) != 24:
        raise ValueError('Frozen design requires 24 unique tasks')
    gold = json.loads((root/'data/gold.json').read_text())
    gold.update(json.loads((root/'data/public/gold.json').read_text()))
    for task in tasks:
        if file_digest(root/task['data']) != task['data_sha256']:
            raise ValueError('Dataset hash mismatch: ' + task['id'])
    return tasks, gold


def context(root, model, model_digest, tasks):
    code = ['trustverify/study.py', 'trustverify/core.py', 'trustverify/benchmark.py',
            'trustverify/live.py', 'trustverify/public_data.py']
    return {'model': model, 'model_digest': model_digest, 'options': OPTIONS,
        'schema_sha256': digest(SCHEMA), 'system_prompt_sha256': hashlib.sha256(SYSTEM.encode()).hexdigest(),
        'protocol_sha256': file_digest(root/'docs/protocol_v2.md'),
        'tasks_sha256': digest(tasks), 'code_sha256': {p:file_digest(root/p) for p in code}}


def validate_saved(result, request, frozen):
    if result.get('request_sha256') != digest(request) or result.get('request') != request:
        raise RuntimeError('Saved request differs from frozen request')
    if result.get('context_sha256') != digest(frozen):
        raise RuntimeError('Saved model, protocol, task or code context differs')
    if result.get('response_sha256') != digest(result['response']):
        raise RuntimeError('Saved response hash mismatch')


def call(base, model, messages, fmt, path, frozen):
    request = {'model': model, 'messages': messages, 'stream': False,
        'format': 'json' if fmt == 'json' else SCHEMA,
        'options': OPTIONS, 'keep_alive': '30m'}
    if path.exists():
        result = json.loads(path.read_text()); validate_saved(result, request, frozen)
        return result
    started = time.perf_counter()
    response = post(base, '/api/chat', request)
    if response.get('error') or not isinstance(response.get('message',{}).get('content'), str):
        raise RuntimeError('Operational API failure; run stopped without scoring it')
    result = {'request_sha256': digest(request), 'context_sha256': digest(frozen),
        'response_sha256': digest(response), 'request': request, 'response': response,
        'wall_seconds': time.perf_counter()-started,
        'generated_at_utc': datetime.now(timezone.utc).isoformat()}
    dump(path, result)
    return result


def record(task, fmt, condition, result, initial, rows, gold, path, root):
    response = result['response']; report = decode(response['message']['content'])
    f = fields(report, gold); valid = schema_valid(report)
    return {'id': task['id'], 'family': task['family'], 'domain': task['domain'],
        'format': fmt, 'condition': condition, 'schema_valid': valid,
        'correct': valid and gold_correct(report, gold), **f,
        'report': report, 'verification': verify(rows, task['spec'], report),
        'truncated': response.get('done_reason') == 'length',
        'done_reason': response.get('done_reason'),
        'wall_seconds': result['wall_seconds'],
        'cumulative_wall_seconds': result['wall_seconds'] + (initial['wall_seconds'] if condition != 'initial' else 0),
        'prompt_tokens': response.get('prompt_eval_count',0),
        'output_tokens': response.get('eval_count',0),
        'raw_path': str(path.relative_to(root))}


def summarize(records):
    groups = {}
    for fmt in FORMATS:
        for condition in CONDITIONS:
            for domain in ('all','synthetic','public'):
                rs = [r for r in records if r['format'] == fmt and r['condition'] == condition
                      and (domain == 'all' or r['domain'] == domain)]
                if not rs: continue
                n = len(rs); good = sum(r['correct'] for r in rs)
                groups[f'{fmt}/{condition}/{domain}'] = {'n': n, 'correct': good,
                    'accuracy': good/n, 'wilson_95': wilson(good,n),
                    **{k:sum(r[k] for r in rs) for k in ('schema_valid','numeric','unit','rows','chart','truncated')},
                    'mean_cumulative_wall_seconds': statistics.mean(r['cumulative_wall_seconds'] for r in rs),
                    'prompt_tokens': sum(r['prompt_tokens'] for r in rs),
                    'output_tokens': sum(r['output_tokens'] for r in rs),
                    'by_family': {f:{'n':sum(r['family']==f for r in rs),
                        'correct':sum(r['correct'] for r in rs if r['family']==f)} for f in sorted({r['family'] for r in rs})}}
    comparisons = {}
    def compare(key, left, right):
        a = {r['id']:r for r in left}; b = {r['id']:r for r in right}
        if set(a) != set(b): raise ValueError('Incomplete pairs: ' + key)
        for outcome in ('correct','schema_valid','numeric'):
            comparisons[key+'/'+outcome] = paired([a[k][outcome] for k in sorted(a)], [b[k][outcome] for k in sorted(a)])
    for c in CONDITIONS:
        compare('schema_minus_json/'+c, [r for r in records if r['format']=='json' and r['condition']==c],
                [r for r in records if r['format']=='schema' and r['condition']==c])
    for fmt in FORMATS:
        compare('feedback_minus_review/'+fmt, [r for r in records if r['format']==fmt and r['condition']=='self_review'],
                [r for r in records if r['format']==fmt and r['condition']=='feedback_repair'])
    return {'groups':groups, 'paired_comparisons':comparisons}


def run(root, model, base, output):
    tasks, gold = tasks_and_gold(root)
    with urllib.request.urlopen(base+'/api/tags', timeout=30) as response: tags = json.load(response)['models']
    tag = next((t for t in tags if t.get('name') == model or t.get('model') == model), None)
    if not tag: raise RuntimeError('Requested exact model tag is not installed')
    frozen = context(root, model, tag['digest'], tasks)
    metadata_path = output/'metadata.json'
    if metadata_path.exists():
        metadata = json.loads(metadata_path.read_text())
        if metadata['context'] != frozen: raise RuntimeError('Resume context changed. Use a new directory.')
    else:
        commit = subprocess.check_output(['git','rev-parse','HEAD'], cwd=root, text=True).strip()
        info = post(base, '/api/show', {'model': model})
        metadata = {'experiment': 'structure_and_public_data_extension', 'context': frozen,
            'code_commit': commit, 'generated_at_utc': datetime.now(timezone.utc).isoformat(),
            'system_prompt': SYSTEM, 'schema': SCHEMA, 'task_manifest': tasks,
            'model_details': info.get('details'), 'model_info': info.get('model_info'),
            'environment': environment(), 'expected_calls': 144}
        dump(metadata_path, metadata)
    records = []
    for index, task in enumerate(tasks):
        rows = load_rows(root/task['data'])
        prompt = 'Question: '+task['question']+'\nApproved contract: '+json.dumps(task['spec'])+'\nCSV:\n'+(root/task['data']).read_text()
        messages = [{'role':'system','content':SYSTEM}, {'role':'user','content':prompt}]
        for fmt in (FORMATS if index%2 == 0 else FORMATS[::-1]):
            path = output/f"raw/{task['id']}-{fmt}-initial.json"
            initial = call(base, model, messages, fmt, path, frozen)
            text = initial['response']['message']['content']
            verdict = verify(rows, task['spec'], decode(text))
            outputs = {'initial': (initial,path)}
            branches = list(BRANCHES) if index%2 == 0 else list(BRANCHES)[::-1]
            for branch in branches:
                instruction = BRANCHES[branch] + (json.dumps(verdict, allow_nan=False) if branch == 'feedback_repair' else '')
                branch_messages = messages + [{'role':'assistant','content':text}, {'role':'user','content':instruction}]
                path = output/f"raw/{task['id']}-{fmt}-{branch}.json"
                outputs[branch] = (call(base, model, branch_messages, fmt, path, frozen),path)
            for condition in CONDITIONS:
                result,path = outputs[condition]
                records.append(record(task,fmt,condition,result,initial,rows,gold[task['id']],path,root))
        print(f"{index+1}/24 {task['id']}: " + ', '.join(f"{r['format']}/{r['condition']}={int(r['correct'])}" for r in records[-6:]), flush=True)
        dump(output/'progress.json', {'completed_tasks':index+1,'records':records})
    # Deterministic software is a separate comparator, not a model repair score.
    deterministic = [schema_valid(repair(load_rows(root/t['data']),t['spec'],None))
                     and gold_correct(repair(load_rows(root/t['data']),t['spec'],None), gold[t['id']]) for t in tasks]
    result = {'metadata':metadata, **summarize(records), 'records':records,
              'deterministic':{'n':len(tasks),'correct':sum(deterministic)}}
    dump(output/'study.json',result)
    return result['groups']


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('--root',type=Path,default=Path.cwd())
    p.add_argument('--model',required=True); p.add_argument('--base-url',default='http://127.0.0.1:11434')
    p.add_argument('--output',type=Path,required=True)
    args = p.parse_args()
    print(json.dumps(run(args.root.resolve(),args.model,args.base_url,args.output.resolve()),indent=2))
