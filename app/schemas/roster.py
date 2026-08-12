from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from typing import Optional

class ShiftRosterBase(BaseModel):
    worker_id: int
    work_date: date
    start_time: datetime
    end_time: datetime
    break_minutes: float = 0.0

class ShiftRosterCreate(ShiftRosterBase):
    pass

class ShiftRosterResponse(ShiftRosterBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
