from sqlalchemy import Column, DateTime, Float, Integer, String
from sqlalchemy.sql import func

from app.database import Base


class Order(Base):
    __tablename__ = 'orders'

    id = Column(Integer, primary_key=True, index=True)
    amount_brl = Column(Float, nullable=False)
    amount_usd = Column(Float, nullable=True)
    status = Column(String, default='PENDING', index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
