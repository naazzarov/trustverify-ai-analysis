# Portable verification evidence

The local demo accepts the synthetic examples, twelve attributed World Bank tasks,
or a user-selected UTF-8 CSV. A user supplies the operation, columns and unit. The
candidate report is editable; verification and deterministic recomputation are
separate actions. No generated Python or shell code executes.

**Download evidence receipt** records the source CSV's SHA-256 and byte count,
canonical JSON hashes of the contract/report, engine hash, profile, verdict and
field findings. The receipt embeds the contract and candidate report. It contains
no local file path, student number or model-service credential. Uploaded CSVs are
held in the request/session and are not saved to the repository.

Record and replay from the command line:

```bash
python3 -m trustverify.audit record --csv observations.csv --spec contract.json \
  --report candidate.json --out receipt.json
python3 -m trustverify.audit replay --csv observations.csv --receipt receipt.json
```

Replay requires matching CSV bytes and verification-engine code. It verifies the
receipt's content hashes and recomputes the verdict. A `pass`, `fail` or `abstain`
can all be replayed successfully; replay success means the stored check reproduces,
not that the report is correct. Recording refuses to overwrite an existing file.

This is a modest software contribution: a portable link from a bounded claim to
its checkable inputs and result. SHA-256 is **not a signature**. Someone who can
rewrite both a receipt and its hashes can replace it. It does not authenticate
authorship, establish source measurement quality, verify narrative meaning or
prove the approved contract matches the original research intent.

Tests exercise clean/faulty/unsupported contracts, altered source data and altered
receipts, UTF-8 BOM and quoted CSVs, custom uploads, origin rejection and input-size
limits. Public population examples inject at least a 1% numeric error to exceed
the documented relative tolerance; this demo choice does not modify the original
fixed controlled benchmark.
