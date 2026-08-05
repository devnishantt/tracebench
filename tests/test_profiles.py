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
