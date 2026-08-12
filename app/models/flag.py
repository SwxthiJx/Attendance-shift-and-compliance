from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class ComplianceFlag(Base):
    __tablename__ = "compliance_flags"

    id = Column(Integer, primary_key=True, index=True)
    payable_result_id = Column(Integer, ForeignKey("payable_results.id", ondelete="CASCADE"), nullable=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    work_date = Column(Date, nullable=False, index=True)
    pay_period_id = Column(String(50), nullable=False, index=True)
    
    rule_code = Column(String(50), nullable=False) # e.g. 'MAX_CONTINUOUS_SHIFT_HOURS', 'MAX_CONSECUTIVE_WORKING_DAYS'
    message = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    payable_result = relationship("PayableResult", back_populates="flags")
