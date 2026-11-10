from __future__ import annotations
import argparse
import json
from pathlib import Path
from . import __version__
from .benchmark import generate, run_faults
from .core import ContractError, load_rows, repair, verify


def main():
    parser = argparse.ArgumentParser(description="Verify structured analysis against an approved contract")
    parser.add_argument("--version", action="version", version=__version__)
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ["generate", "benchmark"]:
        p = sub.add_parser(name); p.add_argument("--root", type=Path, default=Path.cwd())
    for name in ["verify", "repair"]:
        p = sub.add_parser(name)
        p.add_argument("--csv", type=Path, required=True)
        p.add_argument("--spec", type=Path, required=True)
        p.add_argument("--report", type=Path, required=True)
        if name == "verify": p.add_argument("--profile", choices=["numeric", "schema_numeric", "full"], default="full")
    args = parser.parse_args()
    if args.command == "generate":
        tasks, _ = generate(args.root)
        print(json.dumps({"tasks": len(tasks), "development": 12, "test": 48}))
    elif args.command == "benchmark":
        print(json.dumps(run_faults(args.root), indent=2))
    else:
        try:
            rows = load_rows(args.csv)
            spec = json.loads(args.spec.read_text())
            report = json.loads(args.report.read_text())
            result = verify(rows, spec, report, args.profile) if args.command == "verify" else repair(rows, spec, report)
            print(json.dumps(result, indent=2, allow_nan=False))
            if args.command == "verify" and result["status"] != "pass": raise SystemExit(1)
        except (ContractError, ValueError, OSError) as exc:
            parser.exit(2, f"Input error: {exc}\n")


if __name__ == "__main__": main()
