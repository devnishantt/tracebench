import pytest
from tracebench.profile import profile
from tracebench.compare import compare
from tracebench.drift_metrics import category_distance,mean_shift
from tracebench.drift_policy import DriftPolicy
from tracebench.errors import ArtifactError

def test_keep_identical_complete_profiles_stable(dataset_factory,tmp_path):
    p=profile(dataset_factory('x\na\na\nb\n'))
    assert not compare(p,p).drifted

def test_flag_a_removed_column_as_schema_drift(dataset_factory,tmp_path):
    a=profile(dataset_factory('x,y\na,1\n'));b=profile(dataset_factory('x\na\n'))
    assert any(m.metric=='schema.removed' for m in compare(a,b).metrics)

def test_flag_introduced_columns_as_schema_drift(dataset_factory,tmp_path):
    a=profile(dataset_factory('x\na\n'));b=profile(dataset_factory('x,y\na,1\n'))
    assert any(m.metric=='schema.added' for m in compare(a,b).metrics)

def test_flag_shifts_in_missing_value_fractions(dataset_factory,tmp_path):
    a=profile(dataset_factory('x\na\nb\n'));b=profile(dataset_factory('x\na\n""\n'))
    assert next(m for m in compare(a,b).metrics if m.metric=='nulls.fraction_delta').status=='warn'

def test_measure_disjoint_categorical_distributions_at_full_distance(dataset_factory,tmp_path):
    a=profile(dataset_factory('x\na\n')).columns[0];b=profile(dataset_factory('x\nb\n')).columns[0]
    assert category_distance(a,b,0.2).value==1

def test_refuse_confident_comparison_of_truncated_distributions(dataset_factory,tmp_path):
    p=profile(dataset_factory('x\na\nb\n'),category_limit=1)
    r=compare(p,p)
    assert r.drifted and any(m.status=='incomparable' for m in r.metrics)
