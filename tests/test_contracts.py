import pytest
import json
from pydantic import ValidationError
from tracebench.columns import ColumnSpec
from tracebench.contracts import DatasetSpec,Relation,load_contract
from tracebench.errors import ContractError

def test_reject_inverted_numeric_bounds(dataset_factory,tmp_path):
    with pytest.raises(ValidationError): ColumnSpec(name='x',kind='number',minimum=5,maximum=4)
