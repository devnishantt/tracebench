from .errors import InputError


def identifier(name: str) -> str:
    if not name or "\x00" in name or len(name) > 128:
        raise InputError("Column names must contain 1–128 non-NUL characters")
    return '"' + name.replace('"', '""') + '"'


def placeholders(count: int) -> str:
    if count < 1 or count > 201:
        raise InputError("Unsupported SQL parameter shape")
    return ",".join("?" for _ in range(count))
