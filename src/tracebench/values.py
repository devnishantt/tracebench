import re
from datetime import UTC, date, datetime
from decimal import Decimal, InvalidOperation
from uuid import UUID

from .columns import Kind

INTEGER = re.compile(r"^[+-]?[0-9]+$")
NUMBER = re.compile(r"^[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)(?:[eE][+-]?[0-9]+)?$")
EMAIL = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")


def number(value: str) -> Decimal:
    if len(value) > 128 or not NUMBER.fullmatch(value):
        raise ValueError("Not a bounded decimal number")
    try:
        result = Decimal(value)
    except InvalidOperation as exc:
        raise ValueError("Invalid decimal number") from exc
    if not result.is_finite() or abs(result.adjusted()) > 308:
        raise ValueError("Number exceeds finite profiling range")
    return result


def parse_value(value: str, kind: Kind) -> object:
    stripped = value.strip()
    if kind == "string":
        return value
    if kind == "integer":
        if len(stripped) > 128 or not INTEGER.fullmatch(stripped):
            raise ValueError("Not an integer")
        return int(stripped)
    if kind == "number":
        return number(stripped)
    if kind == "boolean":
        if stripped.lower() not in {"true", "false", "1", "0"}:
            raise ValueError("Not a boolean")
        return stripped.lower() in {"true", "1"}
    if kind == "date":
        if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", stripped):
            raise ValueError("Not an ISO calendar date")
        return date.fromisoformat(stripped)
    if kind == "datetime":
        result = datetime.fromisoformat(stripped.replace("Z", "+00:00"))
        if result.tzinfo is None:
            raise ValueError("Datetime requires an explicit timezone")
        return result.astimezone(UTC)
    if kind == "uuid":
        uuid_value = UUID(stripped)
        if str(uuid_value) != stripped.lower():
            raise ValueError("UUID must use canonical hyphenated form")
        return uuid_value
    if kind == "email":
        if len(stripped) > 320 or not EMAIL.fullmatch(stripped):
            raise ValueError("Not a simple email address")
        return stripped
    raise ValueError("Unsupported kind")


def accepts(value: str, kind: Kind) -> bool:
    try:
        parse_value(value, kind)
        return True
    except (ValueError, OverflowError):
        return False
