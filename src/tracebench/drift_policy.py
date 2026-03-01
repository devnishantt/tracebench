from pydantic import BaseModel, ConfigDict, Field

class DriftPolicy(BaseModel):
    model_config = ConfigDict(extra='forbid', allow_inf_nan=False)
    null_fraction_delta: float = Field(default=0.1, ge=0, le=1)
    category_distance: float = Field(default=0.2, ge=0, le=1)
    mean_shift: float = Field(default=2.0, ge=0)
    row_count_delta: float = Field(default=0.25, ge=0)
    fail_on_incomparable: bool = True
