from hashlib import sha256
from .dataset import Dataset
from .sql import identifier

def category_summary(dataset: Dataset, column: str, *, limit: int = 50, include_values: bool = False) -> tuple[list[dict[str, object]], bool]:
    if not 1 <= limit <= 1000:
        raise ValueError('Category limit must be between 1 and 1000')
    name = identifier(column)
    rows = dataset.connection.execute(f'SELECT {name}, COUNT(*) AS n FROM data WHERE {name} IS NOT NULL GROUP BY {name} ORDER BY n DESC, {name} LIMIT ?', [limit + 1]).fetchall()
    result = []
    for value, count in rows[:limit]:
        item: dict[str, object] = {'key': sha256(value.encode('utf-8')).hexdigest(), 'count': count}
        if include_values:
            item['label'] = value
        result.append(item)
    return result, len(rows) > limit
