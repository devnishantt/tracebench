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

def test_normalize_equivalent_timezone_offsets(dataset_factory,tmp_path):
    assert parse_value('2026-10-01T13:00:00+01:00','datetime') == parse_value('2026-10-01T12:00:00Z','datetime')

def test_require_canonical_uuid_punctuation(dataset_factory,tmp_path):
    assert accepts('00000000-0000-4000-8000-000000000001','uuid')
    assert not accepts('00000000000040008000000000000001','uuid')

def test_apply_a_deliberately_simple_email_shape_check(dataset_factory,tmp_path):
    assert accepts('person@example.test','email')
    assert not accepts('person@@example.test','email')
    assert not accepts('a b@example.test','email')

def test_preserve_string_whitespace_rather_than_silently_cleaning_values(dataset_factory,tmp_path):
    assert parse_value('  original  ','string') == '  original  '

def test_reject_numeric_magnitudes_outside_finite_profiling_range(dataset_factory,tmp_path):
    assert not accepts('1e309','number')
    assert not accepts('1e-309','number')

def test_bound_the_length_of_integer_and_number_inputs(dataset_factory,tmp_path):
    assert not accepts('1'*129,'integer')
    assert not accepts('1'*129,'number')

def test_accept_only_the_documented_boolean_spellings(dataset_factory,tmp_path):
    assert parse_value(' TRUE ','boolean') is True
    assert parse_value('0','boolean') is False
    assert not accepts('yes','boolean')
