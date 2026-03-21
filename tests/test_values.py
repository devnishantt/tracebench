import pytest
from decimal import Decimal
from tracebench.values import number,parse_value,accepts
from tracebench.sql import identifier,placeholders
from tracebench.errors import InputError

def test_retain_decimal_precision_beyond_binary_float_representation(dataset_factory,tmp_path):
    assert number('0.12345678901234567890') == Decimal('0.12345678901234567890')

def test_reject_fractional_and_scientific_integer_values(dataset_factory,tmp_path):
    assert not accepts('1.5','integer')
    assert not accepts('1e3','integer')

def test_reject_nonfinite_numeric_spellings(dataset_factory,tmp_path):
    for value in ['NaN','Infinity','-inf']: assert not accepts(value,'number')

def test_require_explicit_datetime_timezones(dataset_factory,tmp_path):
    assert not accepts('2026-10-01T12:00:00','datetime')
    assert accepts('2026-10-01T12:00:00Z','datetime')
