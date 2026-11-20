"""Portable verification receipts and offline replay; no signatures or gold data."""
from __future__ import annotations
import argparse
import csv
import hashlib
import io
import json
import platform
from datetime import datetime, timezone
from pathlib import Path
from . import __version__
from .core import ContractError, verify


def canonical(value):
    return json.dumps(value,sort_keys=True,ensure_ascii=False,allow_nan=False,
                      separators=(',',':')).encode('utf-8')


def sha(body):
    return hashlib.sha256(body).hexdigest()


def parse_csv(body: bytes):
    """Accept UTF-8, optionally with BOM, and enforce unambiguous row widths."""
    try: text = body.decode('utf-8-sig')
    except UnicodeDecodeError as exc: raise ContractError('CSV must be UTF-8') from exc
    reader = csv.DictReader(io.StringIO(text,newline=''))
    if not reader.fieldnames or not all(reader.fieldnames) or len(set(reader.fieldnames)) != len(reader.fieldnames):
        raise ContractError('CSV needs unique, nonempty column headers')
    rows = list(reader)
    if any(None in row or any(v is None for v in row.values()) for row in rows):
        raise ContractError('CSV row width does not match its header')
    return rows


def create_receipt(body: bytes, spec, report, profile='full'):
    rows = parse_csv(body)
    result = verify(rows,spec,report,profile)
    payload = {'receipt_version':1,'created_at_utc':datetime.now(timezone.utc).isoformat(),
        'producer':{'name':'TrustVerify','version':__version__,'python':platform.python_version(),
                    'engine_sha256':sha(Path(__file__).with_name('core.py').read_bytes())},
        'input':{'csv_sha256':sha(body),'csv_bytes':len(body),'rows':len(rows),
                 'contract_sha256':sha(canonical(spec)),'report_sha256':sha(canonical(report))},
        'contract':spec,'report':report,'profile':profile,'verification':result,
        'scope':'Checks selected structured fields under the supplied contract. Narrative meaning, data quality and contract intent are not verified.',
        'integrity':'SHA-256 detects changes against this receipt. It is not a digital signature or proof of authorship.'}
    return dict(payload,receipt_sha256=sha(canonical(payload)))


def replay_receipt(body: bytes, receipt):
    if not isinstance(receipt,dict) or receipt.get('receipt_version') != 1:
        raise ValueError('Unsupported receipt version')
    payload = {k:v for k,v in receipt.items() if k != 'receipt_sha256'}
    if sha(canonical(payload)) != receipt.get('receipt_sha256'):
        raise ValueError('Receipt integrity check failed')
    inp = receipt['input']
    if sha(body) != inp['csv_sha256'] or len(body) != inp['csv_bytes']:
        raise ValueError('CSV differs from the recorded input')
    if sha(canonical(receipt['contract'])) != inp['contract_sha256'] or sha(canonical(receipt['report'])) != inp['report_sha256']:
        raise ValueError('Contract or report differs from recorded hashes')
    if sha(Path(__file__).with_name('core.py').read_bytes()) != receipt['producer']['engine_sha256']:
        raise ValueError('Verification engine differs; replay with the recorded code revision')
    rows = parse_csv(body)
    result = verify(rows,receipt['contract'],receipt['report'],receipt['profile'])
    if len(rows) != inp['rows'] or result != receipt['verification']:
        raise ValueError('Recomputed verdict differs from the receipt')
    return {'replayed':True,'status':result['status'],'receipt_sha256':receipt['receipt_sha256'],
            'scope':receipt['scope'],'integrity':receipt['integrity']}


def main():
    p = argparse.ArgumentParser(description='Record or replay structured verification evidence')
    sub = p.add_subparsers(dest='action',required=True)
    record = sub.add_parser('record'); record.add_argument('--csv',type=Path,required=True)
    record.add_argument('--spec',type=Path,required=True); record.add_argument('--report',type=Path,required=True)
    record.add_argument('--profile',choices=['numeric','schema_numeric','full'],default='full')
    record.add_argument('--out',type=Path,required=True)
    replay = sub.add_parser('replay'); replay.add_argument('--csv',type=Path,required=True)
    replay.add_argument('--receipt',type=Path,required=True)
    args = p.parse_args()
    try:
        if args.action == 'record':
            result = create_receipt(args.csv.read_bytes(),json.loads(args.spec.read_text()),
                                    json.loads(args.report.read_text()),args.profile)
            # Avoid silently replacing a previous evidence record.
            with args.out.open('x') as stream: json.dump(result,stream,indent=2,ensure_ascii=False,allow_nan=False)
            print(json.dumps({'saved':str(args.out),'status':result['verification']['status']}))
        else:
            print(json.dumps(replay_receipt(args.csv.read_bytes(),json.loads(args.receipt.read_text())),indent=2))
    except (OSError,ValueError,TypeError,KeyError) as exc: p.exit(2,f'Input error: {exc}\n')


if __name__ == '__main__': main()
