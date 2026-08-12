from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class ApprovedLeave(Base):
    __tablename__ = "approved_leaves"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    leave_date = Column(Date, nullable=False, index=True)
    leave_type = Column(String(50), default="ANNUAL", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    worker = relationship("Worker", back_populates="leaves")

    __table_args__ = (
        UniqueConstraint("worker_id", "leave_date", name="uq_worker_leave_date"),
    )
