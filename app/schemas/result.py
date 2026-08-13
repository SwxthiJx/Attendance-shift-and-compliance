from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import List, Optional
from app.schemas.exception import ExceptionResponse, ComplianceFlagResponse

class PayableResultResponse(BaseModel):
    id: int
    worker_id: int
    work_date: date
    pay_period_id: str
    rostered_hours: float
    actual_worked_hours: float
    payable_hours: float
    approved_overtime_hours: float
    unapproved_overtime_hours: float
    status: str
    processed_at: datetime
    
    flags: List[ComplianceFlagResponse] = []
    exceptions: List[ExceptionResponse] = []

    model_config = ConfigDict(from_attributes=True)
