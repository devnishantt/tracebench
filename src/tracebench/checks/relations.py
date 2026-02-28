import operator
from ..contracts import DatasetSpec
from ..dataset import Dataset
from ..models import Finding
from ..values import parse_value
from .common import finding

OPERATORS = {'eq': operator.eq, 'ne': operator.ne, 'lt': operator.lt, 'le': operator.le, 'gt': operator.gt, 'ge': operator.ge}

def relation_checks(dataset: Dataset, spec: DatasetSpec) -> list[Finding]:
    kinds = {column.name: column.kind for column in spec.columns}
    result = []
    for rule in spec.relations:
        if rule.left not in dataset.source.columns or rule.right not in dataset.source.columns:
            continue
        left, right = dataset.values(rule.left), dataset.values(rule.right)
        bad = []
        checked = 0
        for (row, a), (_, b) in zip(left, right, strict=True):
            if a is None or b is None:
                if not rule.ignore_nulls:
                    checked += 1
                    bad.append(row)
                continue
            try:
                x, y = parse_value(a, kinds[rule.left]), parse_value(b, kinds[rule.right])
            except (ValueError, OverflowError):
                continue
            checked += 1
            if not OPERATORS[rule.op](x, y):
                bad.append(row)
        result.append(finding('relation.' + rule.op, f'{rule.left} → {rule.right}', bad, checked, 'Declared cross-column comparison must hold', rule.severity, spec.sample_limit))
    return result
