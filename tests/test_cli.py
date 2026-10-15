import json

from typer.testing import CliRunner

from tracebench.cli import app

runner = CliRunner()


def test_profile_json_stdout_is_machine_readable(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text("id,amount\n1,1.25\n2,2.75\n")
    result = runner.invoke(app, ["profile", str(source), "--json", "-"])
    assert result.exit_code == 0, result.output
    payload = json.loads(result.stdout)
    assert payload["source"]["rows"] == 2
    assert "Profiled" not in result.stdout
    assert "Profiled" in result.stderr


def test_check_fails_with_usable_json_artifact(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text("id\nnot-an-integer\n")
    contract = tmp_path / "contract.json"
    contract.write_text(json.dumps({"name": "IDs", "columns": [{"name": "id", "kind": "integer"}]}))
    output = tmp_path / "quality.json"
    result = runner.invoke(app, ["check", str(source), "-c", str(contract), "--json", str(output)])
    assert result.exit_code == 1, result.output
    report = json.loads(output.read_text())
    assert report["errors"] == 1 and not report["passed"]
    assert "not-an-integer" not in output.read_text()


def test_warning_exit_policy_is_explicit(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text("id,extra\n1,x\n")
    contract = tmp_path / "contract.json"
    contract.write_text(
        json.dumps({"name": "IDs", "columns": [{"name": "id"}], "extra_columns": "warn"})
    )
    assert runner.invoke(app, ["check", str(source), "-c", str(contract)]).exit_code == 0
    assert (
        runner.invoke(
            app, ["check", str(source), "-c", str(contract), "--fail-on-warning"]
        ).exit_code
        == 1
    )


def test_compare_cli_detects_a_numeric_shift(tmp_path):
    for name, values in [("baseline", "1\n2"), ("candidate", "100\n101")]:
        source = tmp_path / (name + ".csv")
        source.write_text("value\n" + values + "\n")
        result = runner.invoke(
            app, ["profile", str(source), "--json", str(tmp_path / (name + ".json"))]
        )
        assert result.exit_code == 0, result.output
    output = tmp_path / "drift.json"
    result = runner.invoke(
        app,
        [
            "compare",
            str(tmp_path / "baseline.json"),
            str(tmp_path / "candidate.json"),
            "--json",
            str(output),
        ],
    )
    assert result.exit_code == 1, result.output
    assert json.loads(output.read_text())["drifted"]


def test_infer_drafts_rules_but_protects_source(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text("id\n1\n2\n")
    output = tmp_path / "draft.json"
    assert runner.invoke(app, ["infer", str(source), "-o", str(output)]).exit_code == 0
    assert json.loads(output.read_text())["columns"][0]["kind"] == "integer"
    before = source.read_bytes()
    assert (
        runner.invoke(app, ["infer", str(source), "-o", str(source), "--overwrite"]).exit_code == 2
    )
    assert source.read_bytes() == before


def test_invalid_source_is_an_actionable_cli_failure(tmp_path):
    source = tmp_path / "data.csv"
    source.write_text("id,value\n1,2,3\n")
    result = runner.invoke(app, ["profile", str(source)])
    assert result.exit_code == 2
    assert "column count" in result.output
    assert "Traceback" not in result.output
