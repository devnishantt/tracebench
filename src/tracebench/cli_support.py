from collections.abc import Callable
from functools import wraps
from pathlib import Path

import duckdb
import typer
from pydantic import ValidationError
from rich.console import Console

from .artifacts import Report, report_json, write_atomic
from .errors import ArtifactError, TracebenchError
from .html_report import render_html
from .markdown_report import render_markdown

console = Console(stderr=True, markup=False, highlight=False)


def safe_text(message: str) -> str:
    return "".join(
        character if ord(character) >= 32 and ord(character) != 127 else f"\\x{ord(character):02x}"
        for character in message
    )


def guarded(function: Callable) -> Callable:
    @wraps(function)
    def wrapped(*args: object, **kwargs: object) -> object:
        try:
            return function(*args, **kwargs)
        except (TracebenchError, ValidationError) as exc:
            console.print("Error: " + safe_text(str(exc)))
            raise typer.Exit(2) from exc
        except (OSError, duckdb.Error) as exc:
            console.print("Error: local I/O or query failed (" + type(exc).__name__ + ")")
            raise typer.Exit(2) from exc

    return wrapped


def guard_outputs(inputs: list[Path], outputs: list[Path | None], overwrite: bool) -> None:
    protected = {path.expanduser().resolve() for path in inputs}
    selected = [
        path.expanduser().resolve() for path in outputs if path is not None and str(path) != "-"
    ]
    if len(selected) != len(set(selected)):
        raise ArtifactError("Each report output must use a distinct path")
    if protected & set(selected):
        raise ArtifactError("Output cannot replace a source, contract, or baseline input")
    for path in outputs:
        if path is not None and str(path) != "-":
            if path.is_symlink():
                raise ArtifactError("Report output cannot be a symbolic link")
            if path.exists() and not overwrite:
                raise ArtifactError("Output exists; choose another path or pass --overwrite")


def emit(
    report: Report,
    json_out: Path | None,
    html_out: Path | None,
    markdown_out: Path | None,
    overwrite: bool,
) -> None:
    if json_out is not None:
        if str(json_out) == "-":
            typer.echo(report_json(report), nl=False)
        else:
            write_atomic(json_out, report_json(report), overwrite=overwrite)
    if html_out is not None:
        write_atomic(html_out, render_html(report), overwrite=overwrite)
    if markdown_out is not None:
        write_atomic(markdown_out, render_markdown(report), overwrite=overwrite)
