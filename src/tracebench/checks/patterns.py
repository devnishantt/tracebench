import duckdb
from ..columns import ColumnSpec
from ..dataset import Dataset
from ..errors import ContractError
from ..models import Finding
from ..sql import identifier
from .common import finding

def pattern_check(dataset: Dataset, column: ColumnSpec, sample_limit: int) -> list[Finding]:
    if column.pattern is None:
        return []
    name = identifier(column.name)
    try:
        # RE2 evaluates patterns without Python-style catastrophic backtracking.
        dataset.connection.execute('SELECT regexp_full_match('', ?)', [column.pattern])
        bad = dataset.connection.execute(f'SELECT "__tb_row" FROM data WHERE {name} IS NOT NULL AND NOT regexp_full_match({name}, ?) ORDER BY "__tb_row"', [column.pattern]).fetchall()
        count = dataset.connection.execute(f'SELECT COUNT({name}) FROM data').fetchone()[0]
    except duckdb.Error as exc:
        raise ContractError(f'Invalid or unsupported RE2 pattern for column {column.name}') from exc
    return [finding('value.pattern', column.name, [row[0] for row in bad], count, 'Values must fully match the configured RE2 pattern', column.severity, sample_limit)]
