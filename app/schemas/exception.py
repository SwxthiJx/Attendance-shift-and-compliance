from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional

class ExceptionResponse(BaseModel):
    id: int
    worker_id: int
    work_date: date
    pay_period_id: str
    code: str
    message: str
    severity: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

class ComplianceFlagResponse(BaseModel):
    id: int
    worker_id: int
    work_date: date
    pay_period_id: str
    rule_code: str
    message: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
