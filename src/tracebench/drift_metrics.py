import math
from .models import ColumnProfile, DriftMetric

def category_distance(a: ColumnProfile, b: ColumnProfile, threshold: float) -> DriftMetric:
    if a.categories_truncated or b.categories_truncated:
        return DriftMetric(column=a.name, metric='category.total_variation', status='incomparable', message='A truncated category distribution cannot be compared reliably')
    x = {row['key']: row['count'] for row in a.categories}
    y = {row['key']: row['count'] for row in b.categories}
    nx, ny = sum(x.values()), sum(y.values())
    if not nx or not ny:
        return DriftMetric(column=a.name, metric='category.total_variation', status='incomparable', message='Both profiles need non-null observations')
    distance = min(1.0, sum(abs(x.get(key, 0) / nx - y.get(key, 0) / ny) for key in x.keys() | y.keys()) / 2)
    return DriftMetric(column=a.name, metric='category.total_variation', value=distance, threshold=threshold, status='warn' if distance > threshold else 'pass', message='Total variation of complete non-null categorical frequencies')

def mean_shift(a: ColumnProfile, b: ColumnProfile, threshold: float) -> DriftMetric:
    x, y = a.numeric, b.numeric
    if not x or not y or any(x.get(key) is None for key in ['mean', 'stddev']) or y.get('mean') is None:
        return DriftMetric(column=a.name, metric='numeric.mean_shift', status='incomparable', message='Comparable finite numeric summaries are required')
    before, after, scale = x['mean'], y['mean'], x['stddev']
    if scale == 0:
        if before == after:
            return DriftMetric(column=a.name, metric='numeric.mean_shift', value=0, threshold=threshold, status='pass', message='Constant baseline and candidate means agree')
        return DriftMetric(column=a.name, metric='numeric.mean_shift', status='warn', threshold=threshold, message='Mean changed from a zero-variance baseline; normalized shift is undefined')
    shift = abs(after / scale - before / scale)
    if not math.isfinite(shift):
        return DriftMetric(column=a.name, metric='numeric.mean_shift', status='incomparable', message='Normalized shift exceeds finite reporting range')
    return DriftMetric(column=a.name, metric='numeric.mean_shift', value=shift, threshold=threshold, status='warn' if shift > threshold else 'pass', message='Absolute mean shift in baseline standard-deviation units; not a hypothesis test')
