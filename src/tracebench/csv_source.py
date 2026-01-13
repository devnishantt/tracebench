import csv
from pathlib import Path
from .errors import InputError
from .limits import Limits, cell, headers

def read_csv(path: Path, limits: Limits, delimiter: str | None = None) -> tuple[list[str], list[list[str | None]]]:
    if delimiter is not None and delimiter not in (',', ';', '\t', '|'):
        raise InputError('Delimiter must be comma, semicolon, tab, or pipe')
    try:
        with path.open(encoding='utf-8-sig', newline='') as handle:
            if delimiter is None:
                sample = handle.read(4096)
                handle.seek(0)
                try:
                    delimiter = csv.Sniffer().sniff(sample, delimiters=',;\t|').delimiter
                except csv.Error:
                    delimiter = '\t' if path.suffix.lower() == '.tsv' else ','
            reader = csv.reader(handle, delimiter=delimiter, strict=True)
            raw_headers = next(reader, None)
            if raw_headers is None:
                raise InputError('CSV is empty')
            names = headers(raw_headers, limits)
            rows: list[list[str | None]] = []
            for physical_row, values in enumerate(reader, start=2):
                if not values:
                    continue
                if len(values) != len(names):
                    raise InputError(f'CSV record {physical_row} has a different column count')
                limits.shape(len(rows) + 1, len(names))
                rows.append([cell(value, limits) for value in values])
            return names, rows
    except (csv.Error, UnicodeError, OSError) as exc:
        raise InputError(f'Cannot read CSV: {exc}') from exc
