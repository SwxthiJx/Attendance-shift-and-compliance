from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class OvertimeApproval(Base):
    __tablename__ = "overtime_approvals"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    work_date = Column(Date, nullable=False, index=True)
    approved_hours = Column(Float, nullable=False, default=0.0)
    reason = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    worker = relationship("Worker", back_populates="overtimes")

    __table_args__ = (
        UniqueConstraint("worker_id", "work_date", name="uq_worker_overtime_date"),
    )
