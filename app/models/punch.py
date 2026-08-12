from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.session import Base

class Punch(Base):
    __tablename__ = "punches"

    id = Column(Integer, primary_key=True, index=True)
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"), nullable=False, index=True)
    punch_timestamp = Column(DateTime, nullable=False, index=True)
    punch_type = Column(String(10), nullable=False) # 'IN' or 'OUT'
    raw_device_id = Column(String(50), nullable=True)
    is_deduplicated = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    worker = relationship("Worker", back_populates="punches")
