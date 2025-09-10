from datetime import datetime, timezone
from sqlalchemy import  DOUBLE_PRECISION, INTEGER, Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, text, Sequence
from geoalchemy2 import Geometry
from db.base import Base
  

class HubAddressBook(Base):
    __tablename__ = 'hub_address_book'
    
    hub_address_book_seq = Sequence('hub_address_book_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, index=True)
    hub_address_book_uuid = Column(String, unique=True, nullable=False, index=True,server_default=text("'HUB_ADDRESS-' || nextval('hub_address_book_seq'::regclass)"))
    hub_name = Column(String , nullable = False)
    mfo_uuid = Column(String , ForeignKey('mfo_main.mfo_uuid' , ondelete = 'CASCADE'))
    hub_lat = Column(DOUBLE_PRECISION , nullable = False) 
    hub_lng = Column(DOUBLE_PRECISION , nullable = False) 
    hub_location = Column(Geometry(geometry_type='POINT', srid=4326))
    hub_area = Column(String , nullable = True) 
    hub_city = Column(String , nullable = False) 
    hub_state = Column(String , nullable = False) 
    hub_pincode = Column(String , nullable = False) 
    hub_country = Column(String  , default = "India")
    hub_full_address = Column(String , nullable = False) 
    hub_google_location = Column(String , nullable = True) 
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_enable = Column(Boolean , default = True)
    disabled_at = Column(TIMESTAMP , nullable = True)
      



class VehicleHubMapping(Base):
    __tablename__ = 'vehicle_hub_mapping'
    

    id = Column(Integer, primary_key=True, index=True)
    hub_address_book_uuid = Column(String, ForeignKey('hub_address_book.hub_address_book_uuid' , ondelete = 'CASCADE'))
    mfo_uuid = Column(String , ForeignKey('mfo_main.mfo_uuid' , ondelete = 'CASCADE'))
    vehicle_uuid = Column(String , ForeignKey('vehicle_main.vehicle_uuid' , ondelete = 'CASCADE'))
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_enable = Column(Boolean , default = True)
    hub_changed_at = Column(TIMESTAMP, nullable=True)



class VehicleHubLogs(Base):
    __tablename__ = 'vehicle_hub_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    hub_address_book_uuid = Column(String, ForeignKey('hub_address_book.hub_address_book_uuid' , ondelete = 'CASCADE'))
    vehicle_uuid = Column(String , ForeignKey('vehicle_main.vehicle_uuid' , ondelete = 'CASCADE'))
    vehicle_hub_left_time = Column(TIMESTAMP , nullable = True)
    vehicle_hub_in_time = Column(TIMESTAMP , nullable = True)
    total_time_at_hub = Column(TIMESTAMP , nullable = True)
    total_time_outside_hub = Column(TIMESTAMP , nullable = True)
    vehicle_left_time_soc = Column(DOUBLE_PRECISION , default = 0)
    vehicle_in_time_soc = Column(DOUBLE_PRECISION , default = 0)
    vehicle_left_time_odometer_value = Column(DOUBLE_PRECISION , default = 0)
    vehicle_in_time_odometer_value = Column(DOUBLE_PRECISION , default = 0)
    comment = Column(String , nullable = True)
    day = Column(String , nullable = False)
    date = Column(INTEGER , nullable = False)
    month = Column(INTEGER , nullable = False)
    year = Column(INTEGER , nullable = False)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))