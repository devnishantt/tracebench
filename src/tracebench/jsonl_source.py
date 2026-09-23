import json
import math
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path

from .errors import InputError
from .limits import Limits, cell, headers


def scalar(value: object, limits: Limits) -> str | None:
    if value is None:
        return None
    if isinstance(value, bool):
        result = "true" if value else "false"
    elif isinstance(value, (str, int, Decimal)):
        result = str(value)
    elif isinstance(value, float) and math.isfinite(value):
        result = str(value)
    elif isinstance(value, (date, datetime)):
        result = value.isoformat()
    else:
        raise InputError("Only finite scalar JSONL/Parquet values are supported")
    return cell(result, limits)


def reject_constant(_: str) -> None:
    raise InputError("JSONL numbers must be finite")


def unique_object(pairs: list[tuple[str, object]]) -> dict[str, object]:
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError("JSONL contains a duplicate object key")
        result[key] = value
    return result


def read_jsonl(path: Path, limits: Limits) -> tuple[list[str], list[list[str | None]]]:
    records: list[dict[str, str | None]] = []
    names: list[str] = []
    try:
        with path.open(encoding="utf-8-sig") as handle:
            for line_number, line in enumerate(handle, start=1):
                if not line.strip():
                    continue
                data = json.loads(
                    line,
                    parse_float=Decimal,
                    parse_constant=reject_constant,
                    object_pairs_hook=unique_object,
                )
                if not isinstance(data, dict) or not data:
                    raise InputError(f"JSONL line {line_number} must be a nonempty object")
                for key in data:
                    if key not in names:
                        names.append(key)
                limits.shape(len(records) + 1, len(names))
                records.append({key: scalar(value, limits) for key, value in data.items()})
        validated = headers(names, limits)
        if validated != names:
            raise InputError("JSONL keys cannot contain surrounding whitespace")
        return names, [[record.get(name) for name in names] for record in records]
    except (json.JSONDecodeError, UnicodeError, OSError) as exc:
        raise InputError(f"Cannot read JSONL: {exc}") from exc
