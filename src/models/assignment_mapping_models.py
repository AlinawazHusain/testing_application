from sqlalchemy import DOUBLE_PRECISION, Boolean, Column, String, TIMESTAMP, ForeignKey, Sequence, Integer, text
from db.base import Base
from datetime import datetime , timezone

class MfoVehicleMapping(Base):
    __tablename__ = 'mfo_vehicle_mapping'

    mfo_vehicle_seq = Sequence('mfo_vehicle_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, index=True)
    mfo_vehicle_mapping_uuid = Column(String, unique=True, index = True , server_default=text("'MFO_VEH-' || nextval('mfo_vehicle_seq'::regclass)"))
    vehicle_uuid = Column(String, ForeignKey('vehicle_main.vehicle_uuid' , ondelete="CASCADE"),unique=False)
    mfo_uuid = Column(String, ForeignKey('mfo_main.mfo_uuid' , ondelete="CASCADE"), nullable=False)
    
    primary_driver = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="SET NULL") , nullable=True)
    secondary_driver = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="SET NULL"), nullable=True)
    tertiary1_driver = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="SET NULL") , nullable=True)
    tertiary2_driver = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="SET NULL") ,  nullable=True)
    supervisor_driver = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="SET NULL") , nullable=True)
    current_assigned_driver = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="SET NULL") , nullable=True)
    today_assigned_driver = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="SET NULL") , nullable = True)
    last_assigned_driver = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="SET NULL") , nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_enable = Column(Boolean , default = True)
    disabled_at = Column(TIMESTAMP , nullable = True)





class DriverVehicleMapping(Base):
    __tablename__ = 'driver_vehicle_mapping'

    driver_vehicle_seq = Sequence('driver_vehicle_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, index=True)
    driver_vehicle_mapping_uuid = Column(String, unique=True, index = True , server_default=text("'DR_VEH-' || nextval('driver_vehicle_seq'::regclass)"))
    vehicle_uuid = Column(String, ForeignKey('vehicle_main.vehicle_uuid' , ondelete="CASCADE"), unique=False)
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="CASCADE"), unique=False)
    driver_role = Column(String,ForeignKey('driver_roles.driver_role_uuid') , nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_enable = Column(Boolean , default = True)
    disabled_at = Column(TIMESTAMP , nullable = True)



class DriverMfoMapping(Base):
    __tablename__ = 'driver_mfo_mapping'
    
    driver_mfo_seq = Sequence('driver_mfo_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, index=True)
    driver_mfo_mapping_uuid = Column(String, unique=True, index = True , server_default=text("'DR_MFO-' || nextval('driver_mfo_seq'::regclass)"))
    mfo_uuid = Column(String, ForeignKey('mfo_main.mfo_uuid', ondelete="CASCADE"), unique=False)
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="CASCADE"), unique=False)
    driver_salary = Column(DOUBLE_PRECISION , default = 0.0)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_enable = Column(Boolean , default = True)
    disabled_at = Column(TIMESTAMP , nullable = True)



class DriverFutureArrangement(Base):
    __tablename__ = 'driver_future_arrangement'
    
    id = Column(Integer, primary_key=True, index=True)
    driver_uuid = Column(String , ForeignKey('driver_main.driver_uuid' , ondelete = 'CASCADE'))
    vehicle_uuid = Column(String , ForeignKey('vehicle_main.vehicle_uuid' , ondelete = 'CASCADE'))
    arrangement_for = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))