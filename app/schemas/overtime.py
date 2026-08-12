from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional

class OvertimeApprovalBase(BaseModel):
    worker_id: int
    work_date: date
    approved_hours: float
    reason: Optional[str] = None

class OvertimeApprovalCreate(OvertimeApprovalBase):
    pass

class OvertimeApprovalResponse(OvertimeApprovalBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
