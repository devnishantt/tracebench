import pytest
from tracebench.profile import profile
from tracebench.statistics import numeric_summary
from tracebench.artifacts import report_json
from tracebench.draft import draft_contract

def test_profile_header_only_datasets_without_inventing_numeric_summaries(dataset_factory,tmp_path):
    p=profile(dataset_factory('x\n'))
    assert p.source.rows==0 and p.columns[0].numeric is None
    assert p.columns[0].inferred_kind=='unknown'

def test_retain_all_null_columns_as_unknown_semantic_kinds(dataset_factory,tmp_path):
    p=profile(dataset_factory('x\n""\n'))
    assert p.columns[0].nulls==1 and p.columns[0].inferred_kind=='unknown'

def test_compute_population_moments_and_interpolated_quantiles(dataset_factory,tmp_path):
    s=numeric_summary(['1','2','3','4'])
    assert s['mean']==2.5 and s['median']==2.5 and s['p25']==1.75
    assert s['stddev']==pytest.approx(1.118033988749895)

def test_exclude_nulls_from_distinct_value_cardinality(dataset_factory,tmp_path):
    p=profile(dataset_factory('x\na\na\n""\n'))
    assert p.columns[0].distinct==1 and p.columns[0].null_fraction==pytest.approx(1/3)
