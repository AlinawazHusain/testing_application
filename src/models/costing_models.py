from sqlalchemy import Boolean, Column,Integer, String, ForeignKey, TIMESTAMP
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from db.base import Base
from datetime import datetime , timezone


class VehicleCosting(Base):
    __tablename__ = 'vehicle_costing'

    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_uuid = Column(String, ForeignKey('vehicle_main.vehicle_uuid',ondelete="CASCADE" ), nullable=False)
    mfo_uuid = Column(String, ForeignKey('mfo_main.mfo_uuid' , ondelete="CASCADE" ), nullable=False)
    vehicle_emi = Column(DOUBLE_PRECISION, default = 0)
    parking_cost = Column(DOUBLE_PRECISION, default = 0)
    # driver_salary = Column(DOUBLE_PRECISION, default = 0)
    maintenance = Column(DOUBLE_PRECISION, default = 0)
    fuel_based_costing_uuid = Column(String, ForeignKey('fuel_base_costing.fuel_base_costing_uuid'),nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_enable = Column(Boolean , default = True)
    disabled_at = Column(TIMESTAMP , nullable = True)
    