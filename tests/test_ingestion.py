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
