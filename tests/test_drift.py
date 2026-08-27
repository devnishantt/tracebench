import pytest
from tracebench.profile import profile
from tracebench.compare import compare
from tracebench.drift_metrics import category_distance,mean_shift
from tracebench.drift_policy import DriftPolicy
from tracebench.errors import ArtifactError

def test_keep_identical_complete_profiles_stable(dataset_factory,tmp_path):
    p=profile(dataset_factory('x\na\na\nb\n'))
    assert not compare(p,p).drifted
