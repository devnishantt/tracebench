import json
from typer.testing import CliRunner
from tracebench.cli import app

runner = CliRunner()


def test_profile_json_stdout_is_machine_readable(tmp_path):
    source=tmp_path/'data.csv';source.write_text('id,amount\n1,1.25\n2,2.75\n')
    result=runner.invoke(app,['profile',str(source),'--json','-'])
    assert result.exit_code==0, result.output
    payload=json.loads(result.stdout)
    assert payload['source']['rows']==2
    assert 'Profiled' not in result.stdout
    assert 'Profiled' in result.stderr
