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
