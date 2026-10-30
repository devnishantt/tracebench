# Tracebench

[![CI](https://github.com/devnishantt/tracebench/actions/workflows/ci.yml/badge.svg)](https://github.com/devnishantt/tracebench/actions/workflows/ci.yml)

Local-first dataset contracts, profiling, and drift comparisons—with reproducible evidence instead of a reassuring green badge alone.

**Python · Typer · Pydantic · DuckDB · Jinja2 · pytest**

Tracebench is a CLI and Python library, not a hosted application. It reads bounded local CSV, JSONL, and Parquet files, validates explicit expectations, and produces JSON, Markdown, and self-contained HTML reports. No server, API account, or cloud database is required.

## Completed features

- Strict UTF-8 CSV ingestion with quoted/multiline fields, BOM handling, delimiter detection, and ragged-record rejection.
- Sparse scalar JSONL ingestion with decimal preservation, duplicate-key detection, and nested/nonfinite-value rejection.
- Bounded scalar Parquet loading with native date, decimal, and boolean handling; nested fields and glob-like filenames are rejected.
- Explicit file, row, column, cell-count, and cell-length budgets; isolated in-memory DuckDB relations with one query thread.
- Pydantic contracts for required/optional columns, semantic types, nullability, exact decimal bounds, lengths, allowed values, RE2 patterns, uniqueness, composite keys, and cross-column relations.
- Population moments, interpolated quantiles, completeness, cardinality, conservative kind inference, and bounded categorical summaries.
- SHA-256 category keys by default; raw labels require explicit opt-in.
- Schema, volume, null-fraction, categorical total-variation, and baseline-normalized mean-shift comparisons.
- Explicit incomparable outcomes for truncated distributions, empty populations, or unsupported comparisons. No silent stability claims.
- Fingerprinted artifacts, atomic per-file output, source-path protection, versioned JSON Schemas, offline HTML, and escaped Markdown.
- Installed CLI and `python -m tracebench` entry points, typed-package metadata, synthetic examples, regression coverage, and GitHub Actions CI.

## Repository and status

- Source: https://github.com/devnishantt/tracebench
- Package version: `0.1.0`
- Runtime: Python **3.11+**; locally verified with Python **3.13**.
- Deployment: **not applicable**—this is a local CLI, not a web service.
- Distribution: wheel and source archive build locally; no PyPI publication is claimed.
- Storage: source files remain local; the analytical relation is ephemeral; reports are written only to paths you select.

## Install

```sh
python3 -m venv .venv
. .venv/bin/activate
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
tracebench version
tracebench --help
```

On Windows, activate with `.venv\Scripts\Activate.ps1` in PowerShell instead of the POSIX activation command. A runtime-only installation from the checkout is also possible with `python -m pip install .`; the lock file includes development tools for reproducible verification.

The wheel was installed into a separate clean environment and its packaged HTML template and CLI contract-check workflow were verified. An editable-checkout run alone is not the packaging check.

## Quick tour

The example inputs are **synthetic fixtures**, not customer or production data.

### 1. Profile a baseline

```sh
tracebench profile examples/orders-baseline.csv \
  --json reports/baseline.profile.json \
  --html reports/baseline.html \
  --markdown reports/baseline.md
```

### 2. Validate an explicit contract

```sh
tracebench check examples/orders-baseline.csv \
  --contract examples/orders.contract.json \
  --json reports/quality.json \
  --html reports/quality.html
```

The baseline passes. The candidate fixture intentionally violates numeric, missing-value, categorical, date, and relational expectations:

```sh
tracebench check examples/orders-candidate.csv \
  --contract examples/orders.contract.json \
  --html reports/candidate-quality.html
# Expected exit code: 1. The report is still written.
```

### 3. Compare two profiles

```sh
tracebench profile examples/orders-candidate.csv --json reports/candidate.profile.json
tracebench compare reports/baseline.profile.json reports/candidate.profile.json \
  --policy examples/drift-policy.json \
  --json reports/drift.json \
  --html reports/drift.html
# Expected exit code: 1 because the synthetic candidate changes materially.
```

### 4. Draft and review a contract

```sh
tracebench infer examples/events.jsonl --output reports/events.draft.json
```

Inference examines all bounded non-null observations, not just a majority or a preview. A mixed-type field remains text. Integer-looking identifiers may be inferred as integers; review identifiers, leading-zero semantics, nullability, and keys yourself. Inference does not invent authoritative business bounds from one observed range.

### 5. Export JSON Schemas

```sh
tracebench schema --kind contract --output reports/contract.schema.json
tracebench schema --kind profile --output reports/profile.schema.json
tracebench schema --kind quality --output reports/quality.schema.json
tracebench schema --kind drift --output reports/drift.schema.json
tracebench schema --kind policy --output reports/policy.schema.json
```

A reference [contract schema](examples/contract.schema.json), [quality HTML report](examples/quality-preview.html), and [drift HTML report](examples/drift-preview.html) are included. Download an HTML file and open it locally; GitHub's source viewer is not an HTML application preview.

## Command reference

| Command | Input | Important options |
| --- | --- | --- |
| `version` | none | Prints installed version |
| `profile SOURCE` | local CSV, TSV, JSONL/NDJSON, Parquet/PQ | `--json`, `--html`, `--markdown`, `--max-rows`, `--max-bytes`, `--category-limit`, `--delimiter`, `--include-values`, `--overwrite` |
| `check SOURCE` | source plus reviewed contract | `--contract/-c`, report outputs, `--fail-on-warning`, `--max-rows`, `--delimiter`, `--overwrite` |
| `compare BASELINE CANDIDATE` | two profile JSON artifacts | `--policy`, report outputs, `--overwrite` |
| `infer SOURCE` | bounded local source | `--output/-o`, `--name`, `--overwrite` |
| `schema` | selected model | `--kind contract/profile/quality/drift/policy`, `--output/-o`, `--overwrite` |

Only `--json -` streams a report to stdout. Status messages and errors go to stderr, so JSON output can be piped into another tool. HTML and Markdown outputs require filenames.

### Exit codes

- **0:** operation succeeded; a quality report has no failed error checks, or a comparison has no blocking changes.
- **1:** quality errors, requested warning failures, drift warnings, or blocking incomparable metrics. Reports are still available.
- **2:** invalid input, contract, policy, artifact, resource limit, or output-path error.

Warnings do not fail `check` unless `--fail-on-warning` is supplied. Incomparable drift metrics block `compare` by default; set `fail_on_incomparable` to false in an explicit policy if your workflow treats them as nonblocking. This does not turn those metrics into passing comparisons.

## Contract semantics

```json
{
  "version": 1,
  "name": "Order feed",
  "primary_key": ["order_id"],
  "columns": [
    {"name": "order_id", "kind": "string", "pattern": "ORD-[0-9]{3}"},
    {"name": "amount", "kind": "number", "minimum": "0"},
    {"name": "opened", "kind": "date"},
    {"name": "closed", "kind": "date"}
  ],
  "relations": [{"left": "opened", "op": "le", "right": "closed"}]
}
```

Kinds: `string`, `integer`, `number`, `boolean`, `date`, `datetime`, `uuid`, and `email`.

- Numeric quality bounds use decimal arithmetic, not binary floats. Integer inputs must be integer spellings; decimal/scientific representations do not satisfy an integer contract.
- Numeric strings are bounded to 128 characters and finite profiling magnitudes. NaN, infinity, and magnitudes outside the supported range are rejected as numeric values.
- Boolean spellings are `true`, `false`, `1`, and `0`, ignoring case and surrounding whitespace. There is no automatic truthiness coercion.
- Dates are real padded `YYYY-MM-DD` days. Datetimes require a timezone and normalize to UTC for comparisons.
- UUIDs require canonical hyphenated form. Email validation is deliberately a simple shape check, not deliverability verification or full RFC validation.
- Text is not silently trimmed. Header whitespace is normalized for CSV/Parquet; JSONL keys with surrounding whitespace are rejected. SQL identifiers are quoted and case-colliding columns are rejected.
- Default null tokens are exact strings `""`, `"NULL"`, and `"null"`, plus native nulls. Contract checks load the contract's null policy; profile comparison rejects mismatched recorded null policies.
- `allowed` and uniqueness compare non-null raw normalized strings, not a coercively canonicalized semantic representation. All rows in a duplicate group count as failures, not only later occurrences.
- Primary-key fields must be declared and required. Composite keys also enforce non-nullness independently of column nullability.
- Regex rules are full matches using DuckDB's RE2 engine. Python-specific backreferences/lookaround are unsupported; patterns never execute as Python expressions.
- Relations allow `eq`, `ne`, `lt`, `le`, `gt`, and `ge` on compatible kinds. Missing optional operands skip the relation. Invalid typed values are reported by the type check; null comparison behavior is explicit.
- A finding's `failures` counts failed records for value checks; structural checks count failed expectations. Report-level `errors` and `warnings` count failed checks, not unique bad records. Samples are 1-based logical data-record numbers, not physical CSV lines; multiline cells and headers make those different.

## Profiling and drift boundaries

Numeric summaries expose population standard deviation and linearly interpolated quantiles. Decimal accumulation reduces avoidable intermediate rounding, but serialized numeric profile summaries are finite binary floats—not exact financial accounting outputs.

Categorical total variation is half the sum of absolute probability differences over the complete union of category keys. It ranges from zero to one. A distribution truncated at the category budget is marked incomparable instead of comparing only the popular values.

Mean shift is the absolute mean change in baseline-standard-deviation units. A changed zero-variance baseline produces a warning with no infinite numeric score. Empty populations, incompatible kinds, and nonfinite normalized shifts are explicit incomparable cases.

These are transparent heuristics, **not p-values, causal conclusions, or proof of a production incident**. High-cardinality identifiers can be unhelpful drift dimensions; review observations in context and choose appropriate budgets/policies. There is no automated feature exclusion or multiple-testing correction.

## Privacy, safety, and reproducibility

- Sources are local regular files. No network upload, telemetry, API key, remote SQL execution, or automatic DuckDB extension download is part of the workflow.
- Default profile category labels are SHA-256 keys. This is pseudonymization, not anonymity: small domains can be guessed. Counts, schema names, row numbers, source basenames, and fingerprints can still be sensitive.
- `--include-values` deliberately places categorical labels into profile JSON. Only use it on approved data. Full raw rows and failing cell values are not included in quality findings.
- Default input budgets: **50,000,000 bytes, 100,000 rows, 200 columns, 2,000,000 cells, and 100,000 characters per cell**. Selected CLI options can raise row/byte budgets, but the other limits remain. DuckDB uses one thread and a 128 MB query-memory budget; this is not a hard cap on total Python/native process memory.
- Nested JSON/Parquet values are rejected rather than flattened. Compressed Parquet size alone is not a memory guarantee; row and cell budgets also apply. Treat native file parsers as an additional trust boundary; this is not a sandbox for malicious files.
- Source SHA-256 plus size/mtime/inode checks detect ordinary input changes while reading. Use stable, privately controlled snapshots; this is not a forensic locking guarantee against a malicious local writer.
- Content fingerprints exclude generation timestamps. They detect modifications and bind normalization semantics; they are **not signatures** and cannot stop a privileged actor from rewriting data and hashes together.
- Profile artifacts are size-limited and checked for fingerprint, schema, count, and category consistency before CLI comparison. The public Python `compare` function assumes already validated model inputs; use `load_profile` for untrusted artifact files.
- Outputs are atomic per file, require explicit overwrite, reject symlinks, and cannot replace selected input files. Multiple output formats are not one cross-file transaction. Use a local filesystem supporting atomic replacement and hard links; concurrent hostile filesystem writers are outside the guarantee.
- HTML is escaped, self-contained, and script-free, with a restrictive embedded CSP and no external assets. Markdown escapes link/table/control syntax. Review report-sharing permissions yourself.

## Development and verification

```sh
ruff check src tests
ruff format --check src tests
mypy src/tracebench
pytest --cov=tracebench --cov-report=term-missing
python -m build
python -m pip check
```

Locally verified: semantic/ingestion/contract/profile/drift/artifact/CLI tests, strict configured static checks, wheel and source distribution builds, clean wheel installation, actual CSV/JSONL/Parquet workflows, and expected success/failure exit codes. Offline HTML was checked in Chromium at desktop and mobile widths with no page errors or external requests. Test counts and final coverage are recorded by the verification run rather than inferred from commit count.

GitHub Actions runs [`.github/workflows/ci.yml`](.github/workflows/ci.yml) on pushes to `main`, pull requests, and manual dispatch. On Python 3.11 and 3.13 it installs from `requirements.lock`, runs ruff lint and format checks, mypy, pytest with coverage, builds the wheel and source archive, and runs the example contract check. No PyPI release is claimed.

## Not implemented / recommended next steps

1. Benchmark larger real datasets and document peak resident memory across formats.
2. Add streaming/external-memory execution for datasets beyond the deliberate local bounds.
3. Add approved feature exclusions and configurable statistical tests with explicit assumptions.
4. Add artifact signing or independently controlled checkpoint storage where provenance needs authentication.
5. Add optional retention/redaction policy tooling and audited report-sharing workflows.

Not implemented: hosted dashboards, remote object stores, databases as data sources, background scheduling, arbitrary SQL checks, model training, nested-data flattening, or automated data repair.

## History provenance

The **149 implementation and regression-test commits** use assigned historical timestamps within the reserved **January–October 29, 2026 (UTC)** portfolio calendar. Tracebench's reserved slots begin January 2 and end October 27. These timestamps are organizational metadata, not actual development dates. Each commit changes source, configuration, tests, examples, or documentation. The shared reservation leaves room for Ledgerline and Pactrail without exceeding eight combined commits on an active day.
