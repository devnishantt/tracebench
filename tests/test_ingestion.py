import pytest
from tracebench.errors import InputError
from tracebench.limits import Limits

def test_preserve_quoted_comma_fields(dataset_factory,tmp_path):
    data=dataset_factory('id,name\n1,"North, West"\n')
    assert data.values('name') == [(1,'North, West')]
