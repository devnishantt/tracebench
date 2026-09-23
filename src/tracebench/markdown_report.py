import html
import re

from .artifacts import Report
from .presentation import presentation


def escape_markdown(value: object) -> str:
    text = html.escape(str(value), quote=False).replace("\n", " ").replace("\r", " ")
    return re.sub(r"([\\`*_{}\[\]()#+.!|>-])", r"\\\1", text)


def render_markdown(report: Report) -> str:
    view = presentation(report)
    lines = [
        f"# {escape_markdown(view['kind'])}: {escape_markdown(view['title'])}",
        "",
        f"**State:** {view['status']}",
        "",
        escape_markdown(view["subtitle"]),
        "",
        "| Measure | Value |",
        "| --- | --- |",
    ]
    lines.extend(
        f"| {escape_markdown(label)} | {escape_markdown(value)} |"
        for label, value in view["metrics"]
    )
    lines.extend(
        [
            "",
            "| " + " | ".join(view["headers"]) + " |",
            "| " + " | ".join("---" for _ in view["headers"]) + " |",
        ]
    )
    lines.extend(
        "| " + " | ".join(escape_markdown(value) for value in row) + " |" for row in view["rows"]
    )
    lines.extend(
        [
            "",
            "Content fingerprint: `" + report.content_fingerprint + "`",
            "",
            "A passing contract is not proof of correctness. Drift metrics are heuristics, not statistical significance tests.",
            "",
        ]
    )
    return "\n".join(lines)
