from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Float, UniqueConstraint
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class PayableResult(Base):
    __tablename__ = "payable_results"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    work_date = Column(Date, nullable=False, index=True)
    pay_period_id = Column(String(50), nullable=False, index=True)
    
    in_punch_time = Column(String(50), nullable=True)
    out_punch_time = Column(String(50), nullable=True)
    
    rostered_hours = Column(Float, default=0.0, nullable=False)
    actual_worked_hours = Column(Float, default=0.0, nullable=False)
    payable_hours = Column(Float, default=0.0, nullable=False)
    approved_overtime_hours = Column(Float, default=0.0, nullable=False)
    unapproved_overtime_hours = Column(Float, default=0.0, nullable=False)

    
    status = Column(String(50), default="PROCESSED", nullable=False) # 'PROCESSED', 'HAS_EXCEPTIONS', 'HAS_FLAGS'
    processed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    worker = relationship("Worker", back_populates="payable_results")
    exceptions = relationship("ExceptionRecord", back_populates="payable_result", cascade="all, delete-orphan")
    flags = relationship("ComplianceFlag", back_populates="payable_result", cascade="all, delete-orphan")

    __table_args__ = (
        UniqueConstraint("worker_id", "work_date", "pay_period_id", name="uq_worker_date_period"),
    )
