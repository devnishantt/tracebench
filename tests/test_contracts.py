import pytest
import json
from pydantic import ValidationError
from tracebench.columns import ColumnSpec
from tracebench.contracts import DatasetSpec,Relation,load_contract
from tracebench.errors import ContractError

def test_reject_inverted_numeric_bounds(dataset_factory,tmp_path):
    with pytest.raises(ValidationError): ColumnSpec(name='x',kind='number',minimum=5,maximum=4)

def test_reject_inverted_and_negative_text_lengths(dataset_factory,tmp_path):
    with pytest.raises(ValidationError): ColumnSpec(name='x',min_length=5,max_length=4)
    with pytest.raises(ValidationError): ColumnSpec(name='x',min_length=-1)

def test_reject_unknown_column_contract_fields(dataset_factory,tmp_path):
    with pytest.raises(ValidationError): ColumnSpec.model_validate({'name':'x','execute':'DROP TABLE data'})

def test_reject_numeric_bounds_on_text_columns(dataset_factory,tmp_path):
    with pytest.raises(ValidationError): ColumnSpec(name='x',kind='string',minimum=1)

def test_reject_duplicate_declared_column_names(dataset_factory,tmp_path):
    with pytest.raises(ValidationError): DatasetSpec(name='d',columns=[ColumnSpec(name='x'),ColumnSpec(name='x')])
