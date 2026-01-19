from .columns import Kind
from .values import accepts

def infer_kind(values: list[str]) -> str:
    if not values:
        return 'unknown'
    candidates: list[Kind] = ['integer', 'number', 'boolean', 'date', 'datetime', 'uuid', 'email']
    for kind in candidates:
        if all(accepts(value, kind) for value in values):
            return kind
    return 'string'
