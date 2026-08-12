from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, Literal

class PunchBase(BaseModel):
    worker_id: int
    punch_timestamp: datetime
    punch_type: Literal["IN", "OUT"]
    raw_device_id: Optional[str] = None

    @field_validator("punch_type")
    def validate_punch_type(cls, v):
        v_upper = v.upper()
        if v_upper not in ("IN", "OUT"):
            raise ValueError("punch_type must be either 'IN' or 'OUT'")
        return v_upper

class PunchCreate(PunchBase):
    pass

class PunchResponse(PunchBase):
    id: int
    is_deduplicated: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
