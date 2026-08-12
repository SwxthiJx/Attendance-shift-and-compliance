from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class WorkerBase(BaseModel):
    worker_code: str
    name: str
    department: Optional[str] = None

class WorkerCreate(WorkerBase):
    pass

class WorkerResponse(WorkerBase):
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
