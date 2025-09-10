from sqlalchemy import Column, Integer, String,ForeignKey, TIMESTAMP
from db.base import Base
from datetime import datetime , timezone
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSONB


class NotificationListner(Base):
    __tablename__ = 'notification_listner'
    
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid'))
    notification_data = Column(MutableDict.as_mutable(JSONB), default=dict)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))