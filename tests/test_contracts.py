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

def test_require_primary_keys_to_reference_declared_columns(dataset_factory,tmp_path):
    with pytest.raises(ValidationError): DatasetSpec(name='d',columns=[ColumnSpec(name='x')],primary_key=['missing'])

def test_reject_relations_between_incompatible_kinds(dataset_factory,tmp_path):
    with pytest.raises(ValidationError): DatasetSpec(name='d',columns=[ColumnSpec(name='x',kind='date'),ColumnSpec(name='y',kind='number')],relations=[Relation(left='x',op='le',right='y')])

def test_reject_relations_with_missing_fields(dataset_factory,tmp_path):
    with pytest.raises(ValidationError): DatasetSpec(name='d',columns=[ColumnSpec(name='x')],relations=[Relation(left='x',op='eq',right='missing')])

def test_require_coherent_dataset_row_limits(dataset_factory,tmp_path):
    with pytest.raises(ValidationError): DatasetSpec(name='d',columns=[ColumnSpec(name='x')],min_rows=5,max_rows=4)

def test_fingerprint_equivalent_json_contract_mappings_deterministically(dataset_factory,tmp_path):
    a=DatasetSpec(name='d',columns=[ColumnSpec(name='x')])
    b=DatasetSpec.model_validate(json.loads(a.model_dump_json()))
    assert a.fingerprint == b.fingerprint
    assert len(a.fingerprint) == 64

def test_reject_unsupported_contract_schema_versions(dataset_factory,tmp_path):
    with pytest.raises(ValidationError): DatasetSpec.model_validate({'version':2,'name':'d','columns':[{'name':'x'}]})

def test_wrap_malformed_contract_files_as_actionable_errors(dataset_factory,tmp_path):
    path=tmp_path/'broken.json';path.write_text('{bad')
    with pytest.raises(ContractError): load_contract(path)
