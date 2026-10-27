import json

import pytest

from tracebench.artifacts import load_profile, report_json, write_atomic
from tracebench.cli_support import guard_outputs
from tracebench.errors import ArtifactError
from tracebench.html_report import render_html
from tracebench.markdown_report import escape_markdown
from tracebench.profile import profile


def test_publish_and_reload_a_fingerprint_verified_profile_artifact(dataset_factory, tmp_path):
    p = profile(dataset_factory("x\na\nb\n"))
    out = tmp_path / "profile.json"
    write_atomic(out, report_json(p))
    assert load_profile(out).content_fingerprint == p.content_fingerprint


def test_refuse_silent_report_overwrites(dataset_factory, tmp_path):
    out = tmp_path / "report.txt"
    out.write_text("original")
    with pytest.raises(ArtifactError):
        write_atomic(out, "replacement")
    assert out.read_text() == "original"


def test_atomically_replace_an_output_only_with_explicit_permission(dataset_factory, tmp_path):
    out = tmp_path / "report.txt"
    write_atomic(out, "first")
    write_atomic(out, "second", overwrite=True)
    assert out.read_text() == "second"
    assert not list(tmp_path.glob(".tracebench-*"))


def test_reject_modified_json_profile_content(dataset_factory, tmp_path):
    p = profile(dataset_factory("x\na\n"))
    data = json.loads(report_json(p))
    data["source"]["rows"] = 99
    out = tmp_path / "changed.json"
    out.write_text(json.dumps(data))
    with pytest.raises(ArtifactError, match="fingerprint"):
        load_profile(out)


def test_reject_symbolic_link_output_destinations(dataset_factory, tmp_path):
    target = tmp_path / "target"
    target.write_text("keep")
    link = tmp_path / "link"
    link.symlink_to(target)
    with pytest.raises(ArtifactError):
        write_atomic(link, "replace", overwrite=True)
    assert target.read_text() == "keep"


def test_escape_html_payloads_in_dataset_column_names(dataset_factory, tmp_path):
    p = profile(dataset_factory("id,<script>alert(1)</script>\n1,x\n"))
    page = render_html(p)
    assert "<script>alert(1)</script>" not in page
    assert "&lt;script&gt;" in page
    assert "default-src" in page


def test_escape_markdown_links_table_pipes_and_newlines(dataset_factory, tmp_path):
    value = escape_markdown("[click](javascript:bad)|new\nline")
    assert r"\[" in value and r"\|" in value and "\n" not in value


def test_protect_source_paths_and_conflicting_report_destinations(dataset_factory, tmp_path):
    source = tmp_path / "source.csv"
    source.write_text("x\n1")
    with pytest.raises(ArtifactError):
        guard_outputs([source], [source], True)
    with pytest.raises(ArtifactError):
        guard_outputs([], [tmp_path / "a", tmp_path / "a"], True)


def test_reject_forged_negative_deviation_even_with_a_new_content_hash(dataset_factory, tmp_path):
    from tracebench.fingerprint import canonical_digest

    report = profile(dataset_factory("amount\n1\n2\n"))
    report.columns[0].numeric["stddev"] = -1.0
    report.content_fingerprint = canonical_digest(
        report.model_dump(mode="json", exclude={"generated_at", "content_fingerprint"})
    )
    path = tmp_path / "forged-numeric.json"
    path.write_text(report_json(report))
    with pytest.raises(ArtifactError, match="negative"):
        load_profile(path)


def test_reject_invalid_category_keys_even_after_rehashing(dataset_factory, tmp_path):
    from tracebench.fingerprint import canonical_digest

    report = profile(dataset_factory("region\nnorth\n"))
    report.columns[0].categories[0]["key"] = "not-a-digest"
    report.content_fingerprint = canonical_digest(
        report.model_dump(mode="json", exclude={"generated_at", "content_fingerprint"})
    )
    path = tmp_path / "forged-category.json"
    path.write_text(report_json(report))
    with pytest.raises(ArtifactError, match="category"):
        load_profile(path)
