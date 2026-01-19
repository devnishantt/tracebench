from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import duckdb
from .csv_source import read_csv
from .errors import InputError
from .fingerprint import file_digest
from .jsonl_source import read_jsonl
from .limits import Limits
from .models import Source
from .parquet_source import read_parquet
from .sql import identifier, placeholders

@dataclass
class Dataset:
    source: Source
    connection: duckdb.DuckDBPyConnection

    def values(self, column: str) -> list[tuple[int, str | None]]:
        if column not in self.source.columns:
            raise InputError('Unknown dataset column')
        return self.connection.execute(f'SELECT "__tb_row", {identifier(column)} FROM data ORDER BY "__tb_row"').fetchall()

    def close(self) -> None:
        self.connection.close()

    def __enter__(self) -> 'Dataset':
        return self

    def __exit__(self, *_: object) -> None:
        self.close()

def load_dataset(path: Path, *, limits: Limits | None = None, null_tokens: list[str] | None = None, delimiter: str | None = None, format: Literal['csv', 'jsonl', 'parquet'] | None = None) -> Dataset:
    limits = limits or Limits()
    path = path.expanduser().resolve()
    try:
        limits.source(path)
        before = path.stat()
        fingerprint = file_digest(path)
        suffix = path.suffix.lower()
        kind = format or ({'.csv': 'csv', '.tsv': 'csv', '.jsonl': 'jsonl', '.ndjson': 'jsonl', '.parquet': 'parquet', '.pq': 'parquet'}.get(suffix))
        if kind == 'csv':
            names, rows = read_csv(path, limits, delimiter)
        elif kind == 'jsonl':
            names, rows = read_jsonl(path, limits)
        elif kind == 'parquet':
            names, rows = read_parquet(path, limits)
        else:
            raise InputError('Unsupported source extension; use CSV, JSONL, or Parquet')
        after = path.stat()
        if (before.st_size, before.st_mtime_ns, before.st_ino) != (after.st_size, after.st_mtime_ns, after.st_ino):
            raise InputError('Source changed while being read; retry from a stable snapshot')
        tokens = set(null_tokens if null_tokens is not None else ['', 'NULL', 'null'])
        connection = duckdb.connect(config={'threads': 1, 'memory_limit': '128MB', 'enable_external_access': 'false'})
        try:
            schema = ','.join(identifier(name) + ' VARCHAR' for name in names)
            connection.execute(f'CREATE TABLE data ("__tb_row" BIGINT, {schema})')
            statement = f'INSERT INTO data VALUES ({placeholders(len(names) + 1)})'
            for start in range(0, len(rows), 1000):
                batch = [[i + 1, *(None if v in tokens else v for v in row)] for i, row in enumerate(rows[start:start + 1000], start=start)]
                connection.executemany(statement, batch)
            source = Source(filename=path.name, sha256=fingerprint, bytes=before.st_size, rows=len(rows), columns=names, format=kind)
            return Dataset(source, connection)
        except Exception:
            connection.close()
            raise
    except OSError as exc:
        raise InputError(f'Cannot access source: {type(exc).__name__}') from exc
