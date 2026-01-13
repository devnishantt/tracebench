from dataclasses import dataclass
from pathlib import Path
from .errors import InputError
from .sql import identifier

@dataclass(frozen=True)
class Limits:
    max_bytes: int = 50_000_000
    max_rows: int = 100_000
    max_columns: int = 200
    max_cells: int = 2_000_000
    max_cell_length: int = 100_000

    def __post_init__(self) -> None:
        if any(v < 1 for v in (self.max_bytes, self.max_rows, self.max_columns, self.max_cells, self.max_cell_length)):
            raise InputError('All ingestion limits must be positive')

    def source(self, path: Path) -> None:
        if not path.is_file():
            raise InputError('Source must be an existing local regular file')
        if path.stat().st_size > self.max_bytes:
            raise InputError(f'Source exceeds the {self.max_bytes} byte budget')

    def shape(self, rows: int, columns: int) -> None:
        if rows > self.max_rows or columns > self.max_columns or rows * columns > self.max_cells:
            raise InputError('Dataset exceeds configured row, column, or cell budget')

def headers(values: list[str], limits: Limits) -> list[str]:
    result = [value.lstrip('\ufeff').strip() for value in values]
    limits.shape(0, len(result))
    if not result:
        raise InputError('Source must declare at least one column')
    for value in result:
        identifier(value)
    # DuckDB identifiers are case-insensitive even when quoted.
    lowered = [name.casefold() for name in result]
    if len(set(lowered)) != len(lowered):
        raise InputError('Duplicate or case-colliding column names')
    if '__tb_row' in lowered:
        raise InputError('__tb_row is reserved for source row tracking')
    return result

def cell(value: str | None, limits: Limits) -> str | None:
    if value is not None and (len(value) > limits.max_cell_length or '\x00' in value):
        raise InputError('Source cell exceeds length budget or contains NUL')
    return value
