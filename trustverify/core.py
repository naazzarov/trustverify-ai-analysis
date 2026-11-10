"""Recompute a human-approved contract; never execute model-generated code.

This module knows neither benchmark gold answers nor mutation labels.
Only explicit structured fields are verified. Free text is outside scope.
"""
from __future__ import annotations

import csv
import math
from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation, localcontext
from pathlib import Path
from typing import Any

OPERATIONS = {"sum", "mean", "weighted_mean", "ratio", "group_sum", "pct_change"}
REQUIRED = {"metrics", "unit", "rows_used", "chart", "narrative"}
PROFILES = {"numeric", "schema_numeric", "full"}


class ContractError(ValueError):
    """The trusted input is unsupported, ambiguous or undefined."""


@dataclass(frozen=True)
class Finding:
    code: str
    field: str
    message: str
    expected: Any = None
    actual: Any = None


def number(value: Any) -> Decimal | None:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        raise ContractError("Boolean is not a numeric observation")
    try:
        x = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ContractError(f"Non-numeric observation: {value!r}") from exc
    if not x.is_finite():
        raise ContractError("Non-finite observations are unsupported")
    return x


def load_rows(path: str | Path) -> list[dict[str, str]]:
    with open(path, newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        if not reader.fieldnames or not all(reader.fieldnames) or len(set(reader.fieldnames)) != len(reader.fieldnames):
            raise ContractError("CSV needs unique, nonempty column headers")
        rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ContractError("CSV row width does not match its header")
    return rows


def calculate(rows: list[dict], spec: dict) -> dict:
    """Complete-case arithmetic. Change uses input order, never inferred dates."""
    if not isinstance(spec, dict) or spec.get("op") not in OPERATIONS:
        raise ContractError("Unsupported operation; human review required")
    if not isinstance(spec.get("unit"), str) or not spec["unit"]:
        raise ContractError("An explicit output unit is required")
    op = spec["op"]
    keys = [spec.get("column")]
    if op in {"weighted_mean", "ratio"}:
        keys.append(spec.get("weight") if op == "weighted_mean" else spec.get("denominator"))
    if any(not isinstance(k, str) or not k for k in keys):
        raise ContractError("Explicit numeric columns are required")
    group = spec.get("group")
    if op == "group_sum" and (not isinstance(group, str) or not group):
        raise ContractError("An explicit grouping column is required")
    required = keys + ([group] if op == "group_sum" else [])
    if not rows:
        raise ContractError("Empty dataset")
    if any(any(k not in row for k in required) for row in rows):
        raise ContractError("A contract column is missing from the data")
    valid = []
    for row in rows:
        vals = [number(row[k]) for k in keys]
        if any(v is None for v in vals):
            continue
        if op == "group_sum" and row[group] in {None, ""}:
            continue
        valid.append((row, vals))
    if not valid:
        raise ContractError("No complete observations")
    with localcontext() as ctx:
        ctx.prec = 40
        xs = [vals[0] for _, vals in valid]
        if op == "sum":
            metrics = {"value": sum(xs)}
        elif op == "mean":
            metrics = {"value": sum(xs) / len(xs)}
        elif op == "weighted_mean":
            weights = [v[1] for _, v in valid]
            if any(w < 0 for w in weights) or sum(weights) == 0:
                raise ContractError("Weights must be nonnegative with positive total")
            metrics = {"value": sum(x * w for x, w in zip(xs, weights)) / sum(weights)}
        elif op == "ratio":
            denominator = sum(v[1] for _, v in valid)
            if denominator == 0:
                raise ContractError("Zero aggregate denominator")
            metrics = {"value": Decimal(100) * sum(xs) / denominator}
        elif op == "pct_change":
            if len(xs) < 2 or xs[0] == 0:
                raise ContractError("Change needs two observations and nonzero first value")
            metrics = {"value": Decimal(100) * (xs[-1] - xs[0]) / xs[0]}
        else:
            metrics = {}
            for row, vals in valid:
                label = str(row[group])
                metrics[label] = metrics.get(label, Decimal(0)) + vals[0]
    metrics = {k: float(v) for k, v in sorted(metrics.items())}
    if not all(math.isfinite(v) for v in metrics.values()):
        raise ContractError("Result is outside the supported finite float range")
    return {"metrics": metrics, "unit": spec["unit"], "rows_used": len(valid),
            "chart": {"labels": list(metrics), "values": list(metrics.values())},
            "narrative": "Computed from the approved contract; free text is not verified."}


def is_numeric(value: Any) -> bool:
    try:
        return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)
    except OverflowError:
        return False


def close(a: Any, b: Any) -> bool:
    return is_numeric(a) and is_numeric(b) and math.isclose(a, b, rel_tol=1e-6, abs_tol=1e-6)


def verify(rows: list[dict], spec: dict, report: Any, profile: str = "full") -> dict:
    if profile not in PROFILES:
        raise ValueError(f"Unknown profile: {profile}")
    try:
        expected = calculate(rows, spec)
    except ContractError as exc:
        return {"status": "abstain", "profile": profile, "findings": [asdict(Finding(
            "CONTRACT", "spec", str(exc)))], "scope": "structured fields only"}
    findings = []
    def add(code, field, message, want=None, got=None):
        findings.append(asdict(Finding(code, field, message, want, got)))
    if not isinstance(report, dict):
        add("SCHEMA", "$", "Report must be a JSON object")
        return {"status": "fail", "profile": profile, "findings": findings,
                "scope": "structured fields only"}
    if profile != "numeric":
        for key in sorted(REQUIRED - report.keys()):
            add("SCHEMA", key, "Required field is missing")
        if not isinstance(report.get("narrative"), str):
            add("SCHEMA", "narrative", "Narrative must be a string; its meaning is unchecked")
        if type(report.get("rows_used")) is not int:
            add("SCHEMA", "rows_used", "rows_used must be an integer")
        if not isinstance(report.get("unit"), str):
            add("SCHEMA", "unit", "unit must be a string")
    actual = report.get("metrics")
    if not isinstance(actual, dict) or set(actual) != set(expected["metrics"]):
        add("METRIC_KEYS", "metrics", "Metric labels differ", list(expected["metrics"]), actual)
    else:
        for key, want in expected["metrics"].items():
            if not close(actual[key], want):
                add("NUMERIC", f"metrics.{key}", "Incorrect or non-finite numeric result", want, actual[key])
    if profile == "full":
        if report.get("unit") != expected["unit"]:
            add("UNIT", "unit", "Output unit differs from approved contract", expected["unit"], report.get("unit"))
        if type(report.get("rows_used")) is not int or report["rows_used"] != expected["rows_used"]:
            add("ROWS", "rows_used", "Complete-case count differs", expected["rows_used"], report.get("rows_used"))
        chart = report.get("chart")
        if not isinstance(chart, dict):
            add("CHART", "chart", "Chart must contain labels and values")
        else:
            labels, values = chart.get("labels"), chart.get("values")
            if (not isinstance(labels, list) or not isinstance(values, list)
                or len(labels) != len(values) or not all(isinstance(k, str) for k in labels)
                or len(set(labels)) != len(labels) or set(labels) != set(expected["metrics"])):
                add("CHART", "chart", "Chart labels must uniquely cover the metrics")
            else:
                for label, val in zip(labels, values):
                    if not close(val, expected["metrics"][label]):
                        add("CHART", f"chart.{label}", "Chart data disagrees with recomputation", expected["metrics"][label], val)
    return {"status": "fail" if findings else "pass", "profile": profile,
            "findings": findings, "scope": "structured fields only; narrative and contract intent unchecked"}


def repair(rows: list[dict], spec: dict, report: Any) -> dict:
    """Deterministic recomputation, NOT model self-correction.

    Replace unsupported prose with a scope disclosure; do not preserve causal claims.
    """
    result = calculate(rows, spec)
    result["narrative"] = "Structured fields recomputed from the approved contract. No causal conclusion established."
    return result
