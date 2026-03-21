import pytest
from decimal import Decimal
from tracebench.values import number,parse_value,accepts
from tracebench.sql import identifier,placeholders
from tracebench.errors import InputError

def test_retain_decimal_precision_beyond_binary_float_representation(dataset_factory,tmp_path):
    assert number('0.12345678901234567890') == Decimal('0.12345678901234567890')
