from decimal import Decimal
from typing import Literal
from pydantic import BaseModel, ConfigDict, Field, model_validator

Kind = Literal['string', 'integer', 'number', 'boolean', 'date', 'datetime', 'uuid', 'email']

class ColumnSpec(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    name: str = Field(min_length=1, max_length=128)
    kind: Kind = 'string'
    required: bool = True
    nullable: bool = False
    unique: bool = False
    minimum: Decimal | None = None
    maximum: Decimal | None = None
    min_length: int | None = Field(default=None, ge=0, le=100000)
    max_length: int | None = Field(default=None, ge=0, le=100000)
    pattern: str | None = Field(default=None, min_length=1, max_length=256)
    allowed: list[str] | None = Field(default=None, min_length=1, max_length=1000)
    max_null_fraction: float | None = Field(default=None, ge=0, le=1)
    severity: Literal['error', 'warning'] = 'error'

    @model_validator(mode='after')
    def coherent(self) -> 'ColumnSpec':
        if not self.name.strip() or '\x00' in self.name:
            raise ValueError('Column name cannot be blank or contain NUL')
        if self.minimum is not None and self.maximum is not None and self.minimum > self.maximum:
            raise ValueError('minimum cannot exceed maximum')
        if self.min_length is not None and self.max_length is not None and self.min_length > self.max_length:
            raise ValueError('min_length cannot exceed max_length')
        if (self.minimum is not None or self.maximum is not None) and self.kind not in ('integer', 'number'):
            raise ValueError('Numeric bounds require integer or number kind')
        if self.allowed is not None and len(set(self.allowed)) != len(self.allowed):
            raise ValueError('allowed values must be distinct')
        return self
