from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class ExceptionRecord(Base):
    __tablename__ = "exception_records"

    id = Column(Integer, primary_key=True, index=True)
    payable_result_id = Column(Integer, ForeignKey("payable_results.id", ondelete="CASCADE"), nullable=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    work_date = Column(Date, nullable=False, index=True)
    pay_period_id = Column(String(50), nullable=False, index=True)
    
    code = Column(String(50), nullable=False) # e.g. 'MISSING_IN', 'MISSING_OUT', 'PUNCH_ON_LEAVE', 'UNAPPROVED_OVERTIME'
    message = Column(String(255), nullable=False)
    severity = Column(String(20), default="HIGH", nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    payable_result = relationship("PayableResult", back_populates="exceptions")
