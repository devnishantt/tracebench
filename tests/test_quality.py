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
