"""Rebuild extension scores offline from every hashed request and raw response."""
from pathlib import Path
import json
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from trustverify.benchmark import dump, gold_correct
from trustverify.core import load_rows, repair, verify
from trustverify.live import BRANCHES, decode
from trustverify.study import (CONDITIONS, FORMATS, OPTIONS, SCHEMA, SYSTEM, context,
    record, schema_valid, summarize, tasks_and_gold, validate_saved)


def check(root, directory):
    saved=json.loads((directory/'study.json').read_text())
    metadata=saved['metadata'];frozen=metadata['context'];model=frozen['model']
    tasks,gold=tasks_and_gold(root)
    assert frozen==context(root,model,frozen['model_digest'],tasks),'Frozen code/data/protocol changed'
    assert metadata['task_manifest']==tasks
    assert metadata['schema']==SCHEMA and metadata['system_prompt']==SYSTEM
    records=[];paths=set()
    for task in tasks:
        rows=load_rows(root/task['data'])
        prompt='Question: '+task['question']+'\nApproved contract: '+json.dumps(task['spec'])+'\nCSV:\n'+(root/task['data']).read_text()
        messages=[{'role':'system','content':SYSTEM},{'role':'user','content':prompt}]
        for fmt in FORMATS:
            first=directory/f"raw/{task['id']}-{fmt}-initial.json"
            initial=json.loads(first.read_text());text=initial['response']['message']['content']
            verdict=verify(rows,task['spec'],decode(text))
            for condition in CONDITIONS:
                path=directory/f"raw/{task['id']}-{fmt}-{condition}.json";paths.add(path)
                call=json.loads(path.read_text());expected_messages=messages
                if condition!='initial':
                    instruction=BRANCHES[condition]+(json.dumps(verdict,allow_nan=False) if condition=='feedback_repair' else '')
                    expected_messages=messages+[{'role':'assistant','content':text},{'role':'user','content':instruction}]
                request={'model':model,'messages':expected_messages,'stream':False,
                    'format':'json' if fmt=='json' else SCHEMA,'options':OPTIONS,'keep_alive':'30m'}
                validate_saved(call,request,frozen)
                records.append(record(task,fmt,condition,call,initial,rows,gold[task['id']],path,root))
    # Stored order reflects counterbalancing; evaluation must be order-independent.
    key=lambda r:(r['id'],r['format'],r['condition'])
    assert sorted(records,key=key)==sorted(saved['records'],key=key),'Saved records differ from raw evidence'
    rebuilt=summarize(records)
    assert rebuilt['groups']==saved['groups']
    assert rebuilt['paired_comparisons']==saved['paired_comparisons']
    assert set((directory/'raw').glob('*.json'))==paths,'Unexpected or missing call logs'
    deterministic=sum(schema_valid(repair(load_rows(root/t['data']),t['spec'],None))
        and gold_correct(repair(load_rows(root/t['data']),t['spec'],None),gold[t['id']]) for t in tasks)
    assert saved['deterministic']=={'n':24,'correct':deterministic}
    print(f'{model}: {len(paths)} raw calls verified; all scores and paired comparisons reproduced.')


if __name__=='__main__':
    root=Path.cwd();directories=sorted((root/'results/study').glob('*/study.json'))
    if not directories:raise SystemExit('No completed extension runs found')
    for path in directories:check(root,path.parent)
