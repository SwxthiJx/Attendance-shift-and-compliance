from pydantic import BaseModel
from datetime import date
from typing import Optional, List

class ProcessPeriodRequest(BaseModel):
    start_date: Optional[date] = None
    end_date: Optional[date] = None

class PeriodProcessSummary(BaseModel):
    pay_period_id: str
    total_records_processed: int
    total_payable_hours: float
    total_flags: int
    total_exceptions: int
    message: str
