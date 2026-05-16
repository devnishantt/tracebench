import pytest
from tracebench.errors import InputError
from tracebench.limits import Limits

def test_preserve_quoted_comma_fields(dataset_factory,tmp_path):
    data=dataset_factory('id,name\n1,"North, West"\n')
    assert data.values('name') == [(1,'North, West')]

def test_read_crlf_records_and_utf8_bom_headers(dataset_factory,tmp_path):
    data=dataset_factory('\ufeffid,value\r\n1,2\r\n')
    assert data.source.columns == ['id','value']
    assert data.source.rows == 1

def test_preserve_line_breaks_inside_quoted_cells(dataset_factory,tmp_path):
    data=dataset_factory('id,note\n1,"line one\nline two"\n')
    assert data.values('note')[0][1] == 'line one\nline two'

def test_reject_ragged_csv_records(dataset_factory,tmp_path):
    with pytest.raises(InputError,match='column count'): dataset_factory('id,value\n1,2,3\n')

def test_reject_duplicate_normalized_headers(dataset_factory,tmp_path):
    with pytest.raises(InputError,match='Duplicate'): dataset_factory('id, id \n1,2\n')

def test_reject_case_colliding_duckdb_column_names(dataset_factory,tmp_path):
    with pytest.raises(InputError,match='case-colliding'): dataset_factory('ID,id\n1,2\n')

def test_reserve_the_internal_record_number_column(dataset_factory,tmp_path):
    with pytest.raises(InputError,match='reserved'): dataset_factory('__tb_row,value\n1,2\n')

def test_enforce_source_byte_limits_before_analytical_loading(dataset_factory,tmp_path):
    with pytest.raises(InputError,match='byte budget'): dataset_factory('value\n123456789\n',limits=Limits(max_bytes=5))
