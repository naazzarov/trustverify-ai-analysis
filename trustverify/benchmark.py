"""Synthetic benchmark and an independent SQLite evaluation oracle."""
from __future__ import annotations

import copy
import csv
import hashlib
import json
import platform
import random
import sqlite3
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from .core import calculate, close, load_rows, repair, verify

OPS = ["sum", "mean", "weighted_mean", "ratio", "group_sum", "pct_change"]
FAULTS = ["numeric", "unit", "rows", "chart", "missing_field", "nonfinite", "causal_claim"]


def dump(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def oracle(rows, spec):
    """SQL arithmetic is independent of the Decimal production implementation."""
    db = sqlite3.connect(":memory:")
    try:
        db.execute("create table observations (i integer, x real, n real, g text)")
        db.executemany("insert into observations values (?, ?, ?, ?)",
                       [(i, None if r["x"] == "" else float(r["x"]),
                         None if r["n"] == "" else float(r["n"]), r["g"]) for i, r in enumerate(rows)])
        queries = {"sum": "select sum(x) from observations where x is not null",
                   "mean": "select avg(x) from observations where x is not null",
                   "weighted_mean": "select sum(x*n)/sum(n) from observations where x is not null and n is not null",
                   "ratio": "select 100.0*sum(x)/sum(n) from observations where x is not null and n is not null"}
        op = spec["op"]
        if op in queries:
            metrics = {"value": db.execute(queries[op]).fetchone()[0]}
        elif op == "group_sum":
            metrics = dict(db.execute("select g, sum(x) from observations where x is not null and g != '' group by g order by g"))
        else:
            vals = [r[0] for r in db.execute("select x from observations where x is not null order by i")]
            metrics = {"value": 100.0 * (vals[-1] - vals[0]) / vals[0]}
        predicate = "x is not null" + (" and n is not null" if op in {"weighted_mean", "ratio"} else "")
        if op == "group_sum":
            predicate += " and g != ''"
        count = db.execute("select count(*) from observations where " + predicate).fetchone()[0]
        return {"metrics": metrics, "unit": spec["unit"], "rows_used": count,
                "chart": {"labels": list(metrics), "values": list(metrics.values())},
                "narrative": "Reference values from an independent SQLite oracle."}
    finally:
        db.close()


def generate(root: Path):
    tasks, gold = [], {}
    for op_index, op in enumerate(OPS):
        for variant in range(10):
            task_id = f"{op}-{variant:02d}"
            rng = random.Random(20261110 + 1000 * op_index + variant)
            rows = [{"x": str(rng.randint(2, 28)), "n": str(rng.randint(1, 9)),
                     "g": ["A", "B", "C"][i % 3]} for i in range(12)]
            rows[3]["x"] = ""
            rows[8]["x"] = ""
            rows[4]["n"] = ""
            if op == "pct_change" and variant % 2:
                rows[-1]["x"] = str(int(rows[0]["x"]) + rng.randint(1, 15))
            spec = {"op": op, "column": "x", "unit": "%" if op in {"ratio", "pct_change"} else "points"}
            if op == "weighted_mean": spec["weight"] = "n"
            if op == "ratio": spec["denominator"] = "n"
            if op == "group_sum": spec["group"] = "g"
            instructions = {
                "sum": "Sum nonmissing x values.",
                "mean": "Compute the arithmetic mean of nonmissing x values.",
                "weighted_mean": "Compute sum(x*n)/sum(n), using only rows with both x and n present.",
                "ratio": "Compute 100*sum(x)/sum(n), using only rows with both x and n present.",
                "group_sum": "Sum nonmissing x by g, excluding empty groups; sort labels alphabetically.",
                "pct_change": "Compute 100*(last x - first x)/first x, preserving CSV order and skipping missing x."}
            relative = f"data/csv/{task_id}.csv"
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("w", newline="") as stream:
                writer = csv.DictWriter(stream, fieldnames=["x", "n", "g"])
                writer.writeheader(); writer.writerows(rows)
            task = {"id": task_id, "split": "development" if variant < 2 else "test",
                    "family": op, "data": relative, "spec": spec, "question": instructions[op],
                    "data_sha256": hashlib.sha256(path.read_bytes()).hexdigest()}
            tasks.append(task)
            gold[task_id] = oracle(rows, spec)
    (root / "data/tasks.jsonl").write_text("".join(json.dumps(t) + "\n" for t in tasks))
    dump(root / "data/gold.json", gold)
    return tasks, gold


def load_tasks(root):
    return [json.loads(line) for line in (root / "data/tasks.jsonl").read_text().splitlines()]


def mutate(report, fault):
    out = copy.deepcopy(report)
    key = next(iter(out["metrics"]))
    if fault == "numeric": out["metrics"][key] += 3.25
    elif fault == "unit": out["unit"] = "fraction" if out["unit"] == "%" else "USD"
    elif fault == "rows": out["rows_used"] += 1
    elif fault == "chart": out["chart"]["values"][0] += 5
    elif fault == "missing_field": del out["chart"]
    elif fault == "nonfinite": out["metrics"][key] = "NaN"
    elif fault == "causal_claim": out["narrative"] = "These observational data prove that group membership causes the outcome."
    else: raise ValueError(fault)
    return out


def gold_correct(report, gold):
    """Independent final evaluator. A pass says nothing about narrative truth."""
    if not isinstance(report, dict) or not isinstance(report.get("metrics"), dict): return False
    if set(report["metrics"]) != set(gold["metrics"]): return False
    if not all(close(report["metrics"][k], v) for k, v in gold["metrics"].items()): return False
    if report.get("unit") != gold["unit"] or type(report.get("rows_used")) is not int or report["rows_used"] != gold["rows_used"]: return False
    chart = report.get("chart")
    if not isinstance(chart, dict) or not isinstance(chart.get("labels"), list) or not isinstance(chart.get("values"), list): return False
    labels, values = chart["labels"], chart["values"]
    if not all(isinstance(k, str) for k in labels) or len(labels) != len(set(labels)) or set(labels) != set(gold["metrics"]) or len(labels) != len(values): return False
    return all(close(v, gold["metrics"][k]) for k, v in zip(labels, values))


def wilson(successes, n):
    if not n: return [None, None]
    z = 1.96; p = successes / n; d = 1 + z*z/n
    center = (p + z*z/(2*n))/d
    margin = z*((p*(1-p)/n + z*z/(4*n*n))**0.5)/d
    return [max(0, center-margin), min(1, center+margin)]


def run_faults(root):
    tasks = load_tasks(root)
    gold = json.loads((root / "data/gold.json").read_text())
    records, summaries, examples = [], {}, []
    for task in tasks:
        if task["split"] != "test": continue
        rows = load_rows(root / task["data"])
        base = gold[task["id"]]
        computed = calculate(rows, task["spec"])
        if not gold_correct(computed, base): raise AssertionError("Oracle disagreement: " + task["id"])
        for fault in ["clean"] + FAULTS:
            report = base if fault == "clean" else mutate(base, fault)
            for profile in ["numeric", "schema_numeric", "full"]:
                verdict = verify(rows, task["spec"], report, profile)
                record = {"id": task["id"], "family": task["family"], "fault": fault,
                          "profile": profile, "detected": verdict["status"] == "fail",
                          "structured_correct_after_recompute": gold_correct(repair(rows, task["spec"], report), base)}
                records.append(record)
            if task["id"] == "ratio-02" and fault in {"clean", "numeric", "causal_claim"}:
                examples.append({"task": task, "rows": rows, "fault": fault,
                                 "report": report, "verification": verify(rows, task["spec"], report),
                                 "repaired": repair(rows, task["spec"], report)})
    for profile in ["numeric", "schema_numeric", "full"]:
        rs = [r for r in records if r["profile"] == profile]
        bad = [r for r in rs if r["fault"] != "clean"]
        supported = [r for r in bad if r["fault"] != "causal_claim"]
        clean = [r for r in rs if r["fault"] == "clean"]
        count = sum(r["detected"] for r in bad)
        summaries[profile] = {"faults": len(bad), "detected": count, "recall_all_faults": count / len(bad),
            "supported_faults": len(supported), "supported_detected": sum(r["detected"] for r in supported),
            "clean_reports": len(clean), "false_positives": sum(r["detected"] for r in clean),
            "by_fault": {f: sum(r["detected"] for r in bad if r["fault"] == f) for f in FAULTS}}
    dump(root / "results/fault_injection.json", {"experiment": "controlled_fault_injection",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(), "test_tasks": 48,
        "faults_per_task": len(FAULTS), "profiles": summaries, "records": records})
    dump(root / "demo/examples.json", examples)
    return summaries


def environment():
    return {"python": sys.version, "platform": platform.platform(), "machine": platform.machine()}
