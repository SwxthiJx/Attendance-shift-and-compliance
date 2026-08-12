from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional

class ApprovedLeaveBase(BaseModel):
    worker_id: int
    leave_date: date
    leave_type: str = "ANNUAL"

class ApprovedLeaveCreate(ApprovedLeaveBase):
    pass

class ApprovedLeaveResponse(ApprovedLeaveBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
