from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Worker(Base):
    __tablename__ = "workers"

    id = Column(Integer, primary_key=True, index=True)
    worker_code = Column(String(50), unique=True, index=True, nullable=False)
    name = Column(String(100), nullable=False)
    department = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    rosters = relationship("ShiftRoster", back_populates="worker", cascade="all, delete-orphan")
    punches = relationship("Punch", back_populates="worker", cascade="all, delete-orphan")
    leaves = relationship("ApprovedLeave", back_populates="worker", cascade="all, delete-orphan")
    overtimes = relationship("OvertimeApproval", back_populates="worker", cascade="all, delete-orphan")
    payable_results = relationship("PayableResult", back_populates="worker", cascade="all, delete-orphan")
