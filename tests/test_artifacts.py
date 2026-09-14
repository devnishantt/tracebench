import pytest
import json
from tracebench.profile import profile
from tracebench.artifacts import report_json,write_atomic,load_profile
from tracebench.errors import ArtifactError
from tracebench.html_report import render_html
from tracebench.markdown_report import escape_markdown
from tracebench.cli_support import guard_outputs

def test_publish_and_reload_a_fingerprint_verified_profile_artifact(dataset_factory,tmp_path):
    p=profile(dataset_factory('x\na\nb\n'));out=tmp_path/'profile.json'
    write_atomic(out,report_json(p));assert load_profile(out).content_fingerprint==p.content_fingerprint
