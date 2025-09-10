from geoalchemy2 import Geometry
from sqlalchemy import DOUBLE_PRECISION, Boolean, Column,  Integer, String, ForeignKey, TIMESTAMP
from db.base import Base
from datetime import datetime , timezone


class DriverDatabaseUpdateLogs(Base):
    __tablename__ = 'driver_database_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String)
    device_id = Column(String)
    driver_uuid = Column(String , ForeignKey('driver_main.driver_uuid' ,  ondelete="CASCADE"))
    table_name = Column(String)
    table_row_unique_identifier = Column(String)
    table_row_unique_identifier_value = Column(String)
    table_attribute_name = Column(String)
    attribute_previous_value = Column(String)
    attribute_updated_value = Column(String)
    timestamp = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    

class MfoDatabaseUpdateLogs(Base):
    __tablename__ = 'mfo_database_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String)
    device_id = Column(String)
    mfo_uuid = Column(String , ForeignKey('mfo_main.mfo_uuid' ,  ondelete="CASCADE"))
    table_name = Column(String)
    table_row_unique_identifier = Column(String)
    table_row_unique_identifier_value = Column(String)
    table_attribute_name = Column(String)
    attribute_previous_value = Column(String)
    attribute_updated_value = Column(String)
    timestamp = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    
    
class TempDriverLocation(Base):
    __tablename__ = 'temp_driver_location'
    
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String)
    device_id = Column(String)
    driver_lat = Column(DOUBLE_PRECISION)
    driver_lng = Column(DOUBLE_PRECISION)
    timestamp = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    



class VehicleMonitoringLogs(Base):
    __tablename__ = 'vehicle_monitoring_logs'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_uuid = Column(String , ForeignKey('vehicle_main.vehicle_uuid', ondelete = 'CASCADE'))
    driver_uuid = Column(String , ForeignKey('driver_main.driver_uuid' , ondelete = 'SET NULL'))
    event = Column(String , nullable = False)
    vehicle_lat = Column(DOUBLE_PRECISION)
    vehicle_lng = Column(DOUBLE_PRECISION)
    vehicle_location = Column(Geometry(geometry_type='POINT', srid=4326))
    driver_lat = Column(DOUBLE_PRECISION)
    driver_lng = Column(DOUBLE_PRECISION)
    driver_location = Column(Geometry(geometry_type='POINT', srid=4326))
    timestamp = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))



class DriverNudgesResponses(Base):
    __tablename__ = 'driver_nudges_responses'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_uuid = Column(String , ForeignKey('driver_main.driver_uuid' , ondelete = 'SET NULL'))
    nudge_response = Column(Boolean , nullable = False)
    action_type = Column(String , nullable = False)
    overlay_text = Column(String , nullable = False)
    timestamp = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))