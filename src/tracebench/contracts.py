import json
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .columns import ColumnSpec
from .errors import ContractError
from .fingerprint import canonical_digest


class Relation(BaseModel):
    model_config = ConfigDict(extra="forbid")
    left: str
    op: Literal["eq", "ne", "lt", "le", "gt", "ge"]
    right: str
    ignore_nulls: bool = True
    severity: Literal["error", "warning"] = "error"


class DatasetSpec(BaseModel):
    model_config = ConfigDict(extra="forbid")
    version: Literal[1] = 1
    name: str = Field(min_length=1, max_length=100)
    columns: list[ColumnSpec] = Field(min_length=1, max_length=200)
    min_rows: int = Field(default=1, ge=0, le=1000000)
    max_rows: int | None = Field(default=None, ge=0, le=1000000)
    extra_columns: Literal["allow", "warn", "forbid"] = "forbid"
    primary_key: list[str] = Field(default_factory=list, max_length=20)
    relations: list[Relation] = Field(default_factory=list, max_length=50)
    null_tokens: list[str] = Field(default_factory=lambda: ["", "NULL", "null"], max_length=30)
    sample_limit: int = Field(default=5, ge=0, le=20)

    @model_validator(mode="after")
    def coherent(self) -> "DatasetSpec":
        names = [c.name for c in self.columns]
        if len(set(names)) != len(names):
            raise ValueError("Column specifications must have distinct names")
        if self.max_rows is not None and self.min_rows > self.max_rows:
            raise ValueError("min_rows cannot exceed max_rows")
        if len(set(self.primary_key)) != len(self.primary_key) or any(
            k not in names for k in self.primary_key
        ):
            raise ValueError("primary_key must reference distinct declared columns")
        for rule in self.relations:
            if rule.left not in names or rule.right not in names:
                raise ValueError("Relations must reference declared columns")
            kinds = {c.name: c.kind for c in self.columns}
            numeric = {"integer", "number"}
            if (
                kinds[rule.left] != kinds[rule.right]
                and not {kinds[rule.left], kinds[rule.right]} <= numeric
            ):
                raise ValueError("Relation column kinds must be compatible")
        return self

    @property
    def fingerprint(self) -> str:
        return canonical_digest(self.model_dump(mode="json"))


def load_contract(path: Path) -> DatasetSpec:
    try:
        if path.stat().st_size > 1000000:
            raise ContractError("Contract exceeds 1 MB limit")
        return DatasetSpec.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, ValidationError, json.JSONDecodeError) as exc:
        raise ContractError(f"Cannot load contract: {exc}") from exc
