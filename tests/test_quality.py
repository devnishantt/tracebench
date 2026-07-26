import pytest
from decimal import Decimal
from tracebench.columns import ColumnSpec
from tracebench.contracts import DatasetSpec,Relation
from tracebench.quality import check
from tracebench.errors import ContractError

def test_enforce_nonnullable_fields_without_printing_the_failing_cell(dataset_factory,tmp_path):
    data=dataset_factory('x\n""\n')
    report=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='x')]))
    assert any(f.code=='value.null' and f.failures==1 for f in report.findings)
    assert not report.passed

def test_accept_a_null_fraction_exactly_at_its_declared_threshold(dataset_factory,tmp_path):
    data=dataset_factory('x\n1\n""\n')
    r=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='x',nullable=True,max_null_fraction=0.5)]))
    assert r.passed

def test_report_invalid_types_separately_from_numeric_bounds(dataset_factory,tmp_path):
    data=dataset_factory('x\ninvalid\n5\n')
    r=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='x',kind='number',minimum=1)]))
    assert next(f for f in r.findings if f.code=='value.type').failures==1
    assert next(f for f in r.findings if f.code=='value.minimum').checked==1

def test_apply_decimal_bounds_without_binary_float_rounding(dataset_factory,tmp_path):
    data=dataset_factory('x\n0.29\n0.30\n')
    r=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='x',kind='number',minimum=Decimal('0.30'))]))
    assert next(f for f in r.findings if f.code=='value.minimum').sample_rows==[1]

def test_enforce_maximum_numeric_and_unicode_text_lengths(dataset_factory,tmp_path):
    data=dataset_factory('x,y\n12,ééé\n9,é\n')
    spec=DatasetSpec(name='d',columns=[ColumnSpec(name='x',kind='integer',maximum=10),ColumnSpec(name='y',min_length=2,max_length=2)])
    r=check(data,spec)
    assert sum(f.failures for f in r.findings if f.code.startswith('value.') and f.code!='value.type')==3

def test_compare_categorical_allowlists_case_sensitively(dataset_factory,tmp_path):
    data=dataset_factory('status\nactive\nACTIVE\n')
    r=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='status',allowed=['active'])]))
    assert next(f for f in r.findings if f.code=='value.allowed').sample_rows==[2]

def test_require_complete_re2_matches_rather_than_substring_matches(dataset_factory,tmp_path):
    data=dataset_factory('code\nAB12\nxAB12x\n')
    r=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='code',pattern='[A-Z]{2}[0-9]{2}')]))
    assert next(f for f in r.findings if f.code=='value.pattern').sample_rows==[2]

def test_reject_unsupported_backtracking_regex_features_as_contract_errors(dataset_factory,tmp_path):
    data=dataset_factory('code\na\n')
    with pytest.raises(ContractError): check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='code',pattern='(?=a)a')]))

def test_count_every_row_in_a_duplicate_group(dataset_factory,tmp_path):
    data=dataset_factory('id\n1\n1\n2\n')
    r=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='id',unique=True)]))
    assert next(f for f in r.findings if f.code=='value.unique').sample_rows==[1,2]

def test_enforce_composite_primary_key_nullability_and_uniqueness(dataset_factory,tmp_path):
    data=dataset_factory('a,b\n1,x\n1,x\n2,\n')
    r=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='a'),ColumnSpec(name='b',nullable=True)],primary_key=['a','b']))
    assert next(f for f in r.findings if f.code=='key.unique').failures==2
    assert next(f for f in r.findings if f.code=='key.null').sample_rows==[3]

def test_compare_integer_and_decimal_relation_operands_numerically(dataset_factory,tmp_path):
    data=dataset_factory('low,high\n9,10.0\n11,10.0\n')
    r=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='low',kind='integer'),ColumnSpec(name='high',kind='number')],relations=[Relation(left='low',op='le',right='high')]))
    assert next(f for f in r.findings if f.code=='relation.le').sample_rows==[2]

def test_compare_date_relations_as_real_calendar_dates(dataset_factory,tmp_path):
    data=dataset_factory('start,end\n2026-10-01,2026-10-02\n2026-10-03,2026-10-02\n')
    r=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='start',kind='date'),ColumnSpec(name='end',kind='date')],relations=[Relation(left='start',op='le',right='end')]))
    assert next(f for f in r.findings if f.code=='relation.le').sample_rows==[2]

def test_allow_explicitly_optional_absent_columns(dataset_factory,tmp_path):
    data=dataset_factory('x\n1\n')
    r=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='x'),ColumnSpec(name='optional',required=False)]))
    assert r.passed

def test_preserve_warning_only_extra_columns_without_failing_the_report(dataset_factory,tmp_path):
    data=dataset_factory('x,extra\n1,2\n')
    r=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='x')],extra_columns='warn'))
    assert r.passed and r.warnings==1 and r.errors==0

def test_enforce_both_minimum_and_maximum_record_counts(dataset_factory,tmp_path):
    data=dataset_factory('x\n1\n2\n')
    r=check(data,DatasetSpec(name='d',columns=[ColumnSpec(name='x')],max_rows=1))
    assert next(f for f in r.findings if f.code=='rows.maximum').failures==1
