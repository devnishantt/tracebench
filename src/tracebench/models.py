from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from . import __version__


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Source(Model):
    filename: str
    sha256: str = Field(pattern=r"^[a-f0-9]{64}$")
    bytes: int = Field(ge=0)
    rows: int = Field(ge=0)
    columns: list[str]
    format: Literal["csv", "jsonl", "parquet"]


class Finding(Model):
    code: str
    column: str | None = None
    severity: Literal["error", "warning"] = "error"
    failures: int = Field(ge=0)
    checked: int = Field(ge=0)
    message: str
    sample_rows: list[int] = Field(default_factory=list)


class ColumnProfile(Model):
    name: str
    inferred_kind: str
    rows: int = Field(ge=0)
    nulls: int = Field(ge=0)
    distinct: int = Field(ge=0)
    null_fraction: float = Field(ge=0, le=1)
    length_min: int | None = None
    length_max: int | None = None
    numeric: dict[str, float | None] | None = None
    categories: list[dict[str, Any]] = Field(default_factory=list)
    categories_truncated: bool = False


class ProfileReport(Model):
    schema_version: Literal[1] = 1
    tool_version: str = __version__
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    source: Source
    columns: list[ColumnProfile]
    content_fingerprint: str = ""


class QualityReport(Model):
    schema_version: Literal[1] = 1
    tool_version: str = __version__
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    source: Source
    contract_name: str
    contract_fingerprint: str
    findings: list[Finding]
    passed: bool
    errors: int = Field(ge=0)
    warnings: int = Field(ge=0)
    content_fingerprint: str = ""


class DriftMetric(Model):
    column: str
    metric: str
    value: float | None = None
    threshold: float | None = None
    status: Literal["pass", "warn", "incomparable"]
    message: str


class DriftReport(Model):
    schema_version: Literal[1] = 1
    tool_version: str = __version__
    generated_at: str = Field(default_factory=lambda: datetime.now(UTC).isoformat())
    baseline_fingerprint: str
    candidate_fingerprint: str
    metrics: list[DriftMetric]
    drifted: bool
    content_fingerprint: str = ""
