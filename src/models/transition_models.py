from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, TIMESTAMP, ForeignKey
from db.base import Base

class ModelTransition(Base):
    __tablename__ = 'model_transition'

    id = Column(Integer, primary_key=True, index=True)
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="CASCADE"), nullable=False)
    vehicle_uuid = Column(String, ForeignKey('vehicle_main.vehicle_uuid', ondelete="CASCADE"), nullable=False)
    previous_model = Column(String,ForeignKey('model_types.model_type_uuid') , nullable=True)
    current_model = Column(String,ForeignKey('model_types.model_type_uuid') , nullable=True)
    transition_date = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    reason = Column(String, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))