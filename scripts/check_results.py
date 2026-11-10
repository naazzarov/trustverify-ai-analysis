"""Re-evaluate persisted evidence without making model calls."""
import json
import hashlib
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from trustverify.benchmark import gold_correct, load_tasks
from trustverify.core import load_rows, repair, verify
from trustverify.live import decode

root=Path(__file__).resolve().parents[1]
faults=json.loads((root/"results/fault_injection.json").read_text())
assert faults["test_tasks"]==48
assert len(faults["records"])==48*8*3
assert faults["profiles"]["full"]["detected"]==288
assert faults["profiles"]["full"]["false_positives"]==0
assert faults["profiles"]["full"]["by_fault"]["causal_claim"]==0
gold=json.loads((root/"data/gold.json").read_text())
tasks={t["id"]:t for t in load_tasks(root)}
for task in tasks.values():
    assert hashlib.sha256((root/task['data']).read_bytes()).hexdigest()==task['data_sha256']
for path in [root/"results/live_pilot.json",root/"results/qwen-1.5b/live_pilot.json"]:
    if not path.exists():continue
    result=json.loads(path.read_text());counts={k:0 for k in result["summary"]}
    for record in result["records"]:
        assert record["correct"]==gold_correct(record["report"],gold[record["id"]])
        counts[record["condition"]]+=record["correct"]
        if "raw_path" in record:
            raw=json.loads((root/record["raw_path"]).read_text())
            assert hashlib.sha256(json.dumps(raw['request'],sort_keys=True).encode()).hexdigest()==raw['request_sha256']
            assert decode(raw['response']['message']['content'])==record['report']
            assert raw['request']['model']==result['metadata']['model']
            assert len(raw["request"]["messages"])==(2 if record["condition"]=="initial" else 4)
            assert raw["request"]["options"]["num_predict"]==384
    for condition,count in counts.items():assert count==result["summary"][condition]["correct"]
    assert len(result["records"])==24*4
    print(path.relative_to(root),counts)
print("Persisted evidence is internally consistent.")
