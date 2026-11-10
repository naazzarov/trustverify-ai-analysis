"""Actual Ollama calls with raw logs and equal second-call budgets."""
from __future__ import annotations
import argparse
import hashlib
import json
import random
import statistics
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from .benchmark import dump, environment, gold_correct, load_tasks, wilson
from .core import load_rows, repair, verify

SYSTEM = '''You are a careful data analyst. Follow the approved contract exactly.
Return ONLY a JSON object with these five fields:
metrics: an object of numeric answers. Use key "value" for a single answer, or group labels for grouped answers.
unit: the exact string in the contract.
rows_used: integer count of rows actually used after complete-case exclusion.
chart: an object with labels (array of metric keys) and values (matching numeric values).
narrative: one short descriptive sentence. Do not claim causation.
Blank CSV cells are missing, not zero. Do not round intermediate calculations.
Output numeric results to at least six decimal places when fractional. No extra commentary.'''
OPTIONS = {"temperature": 0, "seed": 31415, "num_ctx": 4096, "num_predict": 384}
BRANCHES = {"self_review": "Review your initial answer independently. Check the arithmetic, missing values, row count, unit and chart. Return a corrected complete JSON report.",
            "feedback_repair": "Use the executable checker findings below to repair your initial answer. Return a corrected complete JSON report. Checker findings: "}


def post(base, route, payload):
    request = urllib.request.Request(base.rstrip("/") + route,
        data=json.dumps(payload).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(request, timeout=180) as response:
        return json.load(response)


def decode(text):
    try:
        return json.loads(text, parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
    except (ValueError, TypeError):
        return None


def call(base, model, messages, path):
    request = {"model": model, "messages": messages, "stream": False,
               "format": "json", "options": OPTIONS, "keep_alive": "30m"}
    digest = hashlib.sha256(json.dumps(request, sort_keys=True).encode()).hexdigest()
    if path.exists():
        result = json.loads(path.read_text())
        if result["request_sha256"] != digest:
            raise RuntimeError("Saved call does not match frozen request: " + str(path))
        return result
    start = time.perf_counter()
    response = post(base, "/api/chat", request)  # operational errors stop the run
    elapsed = time.perf_counter() - start
    result = {"request_sha256": digest, "request": request, "response": response,
              "wall_seconds": elapsed, "generated_at_utc": datetime.now(timezone.utc).isoformat()}
    dump(path, result)
    return result


def paired_bootstrap(a, b, repeats=10000):
    if len(a) != len(b) or not a: raise ValueError("Paired equal nonempty inputs required")
    delta = [int(y)-int(x) for x,y in zip(a,b)]
    rng = random.Random(20261110)
    samples = sorted(sum(delta[rng.randrange(len(delta))] for _ in delta)/len(delta) for _ in range(repeats))
    return [samples[int(.025*repeats)], samples[int(.975*repeats)]]


def run(root: Path, base="http://127.0.0.1:11434", model="qwen2.5:0.5b", output: Path | None = None):
    output = output or root / "results"
    tasks = [t for t in load_tasks(root) if t["split"] == "test" and 2 <= int(t["id"].rsplit("-",1)[1]) <= 5]
    gold = json.loads((root / "data/gold.json").read_text())
    records, summaries = [], {}
    model_info = post(base, "/api/show", {"model": model})
    with urllib.request.urlopen(base + "/api/tags", timeout=20) as response: tags = json.load(response)
    metadata = {"experiment": "actual_local_model_pilot", "model": model, "options": OPTIONS,
        "system_prompt": SYSTEM, "system_prompt_sha256": hashlib.sha256(SYSTEM.encode()).hexdigest(),
        "protocol_sha256": hashlib.sha256((root/"docs/protocol.md").read_bytes()).hexdigest(),
        "task_file_sha256": hashlib.sha256((root/"data/tasks.jsonl").read_bytes()).hexdigest(),
        "model_details": model_info.get("details"), "model_info": model_info.get("model_info"),
        "model_tags": tags, "environment": environment(), "task_count": len(tasks),
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "calls_per_task": 3}
    dump(output / "live_metadata.json", metadata)
    for index, task in enumerate(tasks):
        rows = load_rows(root / task["data"])
        if hashlib.sha256((root/task["data"]).read_bytes()).hexdigest() != task["data_sha256"]:
            raise RuntimeError("Dataset changed after task freeze")
        prompt = "Question: " + task["question"] + "\nApproved contract: " + json.dumps(task["spec"]) + "\nCSV:\n" + (root/task["data"]).read_text()
        messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}]
        initial = call(base, model, messages, output/f"raw/{task['id']}-initial.json")
        text = initial["response"]["message"]["content"]
        initial_report = decode(text)
        verdict = verify(rows, task["spec"], initial_report)
        outputs = {"initial": initial}
        for branch, instruction in BRANCHES.items():
            if branch == "feedback_repair": instruction += json.dumps(verdict, allow_nan=False)
            branch_messages = messages + [{"role": "assistant", "content": text}, {"role": "user", "content": instruction}]
            outputs[branch] = call(base, model, branch_messages, output/f"raw/{task['id']}-{branch}.json")
        for condition, call_result in outputs.items():
            response = call_result["response"]
            report = decode(response["message"]["content"])
            cumulative_seconds = call_result["wall_seconds"] + (initial["wall_seconds"] if condition != "initial" else 0)
            records.append({"id": task["id"], "family": task["family"], "condition": condition,
                "correct": gold_correct(report, gold[task["id"]]), "valid_json_object": isinstance(report, dict),
                "report": report, "verification": verify(rows, task["spec"], report),
                "wall_seconds": call_result["wall_seconds"], "cumulative_wall_seconds": cumulative_seconds,
                "prompt_tokens": response.get("prompt_eval_count",0), "output_tokens": response.get("eval_count",0),
                "raw_path": str((output/f"raw/{task['id']}-{condition}.json").relative_to(root))})
        start = time.perf_counter(); deterministic = repair(rows, task["spec"], initial_report)
        records.append({"id": task["id"], "family": task["family"], "condition": "deterministic_recompute",
            "correct": gold_correct(deterministic, gold[task["id"]]), "valid_json_object": True,
            "report": deterministic, "wall_seconds": time.perf_counter()-start,
            "cumulative_wall_seconds": time.perf_counter()-start, "prompt_tokens": 0, "output_tokens": 0})
        print(f"{index+1}/{len(tasks)} {task['id']}: " + ", ".join(f"{r['condition']}={int(r['correct'])}" for r in records[-4:]), flush=True)
        dump(output/"live_progress.json", {"completed_tasks": index+1, "records": records})
    for condition in ["initial", "self_review", "feedback_repair", "deterministic_recompute"]:
        rs = [r for r in records if r["condition"] == condition]; n = len(rs); good = sum(r["correct"] for r in rs)
        summaries[condition] = {"n":n, "correct":good, "accuracy":good/n, "wilson_95":wilson(good,n),
            "valid_json_objects":sum(r["valid_json_object"] for r in rs),
            "mean_cumulative_wall_seconds":statistics.mean(r["cumulative_wall_seconds"] for r in rs),
            "completion_tokens_second_call_only":sum(r["output_tokens"] for r in rs),
            "by_family":{f:sum(r["correct"] for r in rs if r["family"] == f) for f in sorted({r["family"] for r in rs})}}
    a = [r["correct"] for r in records if r["condition"] == "self_review"]
    b = [r["correct"] for r in records if r["condition"] == "feedback_repair"]
    comparison = {"feedback_minus_self_review":(sum(b)-sum(a))/len(a), "paired_bootstrap_95":paired_bootstrap(a,b),
                  "improved":sum(not x and y for x,y in zip(a,b)), "regressed":sum(x and not y for x,y in zip(a,b))}
    dump(output/"live_pilot.json", {"metadata":metadata, "summary":summaries, "paired_comparison":comparison, "records":records})
    return summaries


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("--root", type=Path, default=Path.cwd())
    p.add_argument("--base-url", default="http://127.0.0.1:11434"); p.add_argument("--model", default="qwen2.5:0.5b")
    p.add_argument("--output",type=Path)
    args = p.parse_args(); print(json.dumps(run(args.root.resolve(), args.base_url, args.model, args.output.resolve() if args.output else None), indent=2))
