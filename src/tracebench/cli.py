import json
from pathlib import Path
from typing import Annotated

import typer

from . import __version__
from .artifacts import load_profile, write_atomic
from .cli_support import console, emit, guard_outputs, guarded
from .compare import compare
from .contracts import DatasetSpec, load_contract
from .dataset import load_dataset
from .draft import draft_contract
from .drift_policy import DriftPolicy
from .errors import ContractError
from .limits import Limits
from .profile import profile as make_profile
from .quality import check as run_checks

app = typer.Typer(
    no_args_is_help=True,
    help="Local-first dataset contracts, profiles, and drift reports.",
    pretty_exceptions_enable=False,
)


@app.command("version")
def version() -> None:
    """Print the installed tool version."""
    typer.echo(__version__)


@app.command("profile")
@guarded
def profile_command(
    source: Path,
    json_out: Annotated[Path | None, typer.Option("--json")] = None,
    html_out: Annotated[Path | None, typer.Option("--html")] = None,
    markdown_out: Annotated[Path | None, typer.Option("--markdown")] = None,
    max_rows: Annotated[int, typer.Option(min=1, max=1000000)] = 100000,
    max_bytes: Annotated[int, typer.Option(min=1, max=500000000)] = 50000000,
    category_limit: Annotated[int, typer.Option(min=1, max=1000)] = 50,
    delimiter: str | None = None,
    include_values: bool = False,
    overwrite: bool = False,
) -> None:
    """Profile a bounded local CSV, JSONL, or Parquet snapshot."""
    guard_outputs([source], [json_out, html_out, markdown_out], overwrite)
    with load_dataset(
        source, limits=Limits(max_rows=max_rows, max_bytes=max_bytes), delimiter=delimiter
    ) as dataset:
        report = make_profile(dataset, category_limit=category_limit, include_values=include_values)
    emit(report, json_out, html_out, markdown_out, overwrite)
    console.print(f"Profiled {report.source.rows} records across {len(report.columns)} columns.")
    console.print("Content fingerprint: " + report.content_fingerprint)


@app.command("check")
@guarded
def check_command(
    source: Path,
    contract: Annotated[Path, typer.Option("--contract", "-c")],
    json_out: Annotated[Path | None, typer.Option("--json")] = None,
    html_out: Annotated[Path | None, typer.Option("--html")] = None,
    markdown_out: Annotated[Path | None, typer.Option("--markdown")] = None,
    fail_on_warning: bool = False,
    max_rows: Annotated[int, typer.Option(min=1, max=1000000)] = 100000,
    delimiter: str | None = None,
    overwrite: bool = False,
) -> None:
    """Validate a source against a reviewed JSON dataset contract."""
    guard_outputs([source, contract], [json_out, html_out, markdown_out], overwrite)
    spec = load_contract(contract)
    with load_dataset(
        source, limits=Limits(max_rows=max_rows), null_tokens=spec.null_tokens, delimiter=delimiter
    ) as dataset:
        report = run_checks(dataset, spec)
    emit(report, json_out, html_out, markdown_out, overwrite)
    console.print(
        f"{'PASSED' if report.passed else 'FAILED'}: {report.errors} failed error checks; {report.warnings} failed warning checks."
    )
    raise typer.Exit(1 if report.errors or (fail_on_warning and report.warnings) else 0)


@app.command("compare")
@guarded
def compare_command(
    baseline: Path,
    candidate: Path,
    json_out: Annotated[Path | None, typer.Option("--json")] = None,
    html_out: Annotated[Path | None, typer.Option("--html")] = None,
    markdown_out: Annotated[Path | None, typer.Option("--markdown")] = None,
    policy: Path | None = None,
    overwrite: bool = False,
) -> None:
    """Compare two fingerprint-verified profile JSON artifacts."""
    guard_outputs(
        [baseline, candidate, *([policy] if policy else [])],
        [json_out, html_out, markdown_out],
        overwrite,
    )
    settings = DriftPolicy()
    if policy is not None:
        if policy.stat().st_size > 1000000:
            raise ContractError("Drift policy exceeds 1 MB")
        settings = DriftPolicy.model_validate_json(policy.read_text(encoding="utf-8"))
    report = compare(load_profile(baseline), load_profile(candidate), settings)
    emit(report, json_out, html_out, markdown_out, overwrite)
    console.print(
        f"{'ATTENTION' if report.drifted else 'STABLE'}: {len(report.metrics)} drift observations."
    )
    raise typer.Exit(1 if report.drifted else 0)


@app.command("infer")
@guarded
def infer_command(
    source: Path,
    output: Annotated[Path, typer.Option("--output", "-o")],
    name: str | None = None,
    overwrite: bool = False,
) -> None:
    """Draft a JSON contract for human review; inferred rules are not authoritative."""
    guard_outputs([source], [output], overwrite)
    with load_dataset(source) as dataset:
        draft = draft_contract(make_profile(dataset), name)
    write_atomic(output, draft.model_dump_json(indent=2) + "\n", overwrite=overwrite)
    console.print(
        "Draft contract written. Review semantic kinds, null policy, keys, and thresholds before use."
    )


@app.command("schema")
@guarded
def schema_command(
    output: Annotated[Path | None, typer.Option("--output", "-o")] = None, overwrite: bool = False
) -> None:
    """Export the machine-readable JSON Schema for dataset contracts."""
    text = json.dumps(DatasetSpec.model_json_schema(), indent=2) + "\n"
    if output is None:
        typer.echo(text, nl=False)
    else:
        guard_outputs([], [output], overwrite)
        write_atomic(output, text, overwrite=overwrite)
