from datetime import datetime, timezone
from sqlalchemy import BIGINT, DOUBLE_PRECISION, Column, Integer, String, Boolean, TIMESTAMP, ForeignKey, text, Sequence
from geoalchemy2 import Geometry
from db.base import Base
  

class VehicleMain(Base):
    __tablename__ = 'vehicle_main'
    
    vehicle_seq = Sequence('vehicle_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, index=True)
    vehicle_uuid = Column(String, unique=True, nullable=False, index=True,server_default=text("'VEH-' || nextval('vehicle_seq'::regclass)"))
    mfo_uuid = Column(String, ForeignKey('mfo_main.mfo_uuid' , ondelete="CASCADE"), nullable=False , index = True)
    bluetooth_id = Column(String, nullable=True)
    vehicle_number = Column(String, nullable=False , index = True , unique = False)
    vehicle_model = Column(String)
    rc = Column(String, nullable=True)
    insurance_docs = Column(String, nullable = True)
    insurance_upto = Column(String, nullable=True)
    fitness_certificate = Column(String, nullable=True)
    category = Column(String, nullable=True)
    puc = Column(String, nullable=True)
    financed = Column(Boolean, nullable=True)
    commercial = Column(Boolean, nullable=True)
    permit = Column(String, nullable=True)
    vehicle_status = Column(String ,ForeignKey('vehicle_status.vehicle_status_uuid'), nullable = True)
    vehicle_at_hub = Column(Boolean , default = False)
    fuel_type = Column(String, ForeignKey('fuel_types.fuel_type_uuid'),nullable=True)
    assigned = Column(Boolean, default= False)
    details = Column(String, nullable=True)
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid' , ondelete = 'SET NULL'), nullable=True)
    verification_status = Column(Boolean, nullable=True)
    bluetooth_connection_status = Column(Boolean , default = False)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_enable = Column(Boolean , default = True)
    disabled_at = Column(TIMESTAMP , nullable = True)
    
    


    

class VehicleUtilization(Base):
    __tablename__ = 'vehicle_utilization'

    id = Column(Integer, primary_key=True, index=True)
    vehicle_uuid = Column(String, ForeignKey('vehicle_main.vehicle_uuid'), nullable=False , index = True)
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid' , ondelete = "SET NULL") , index = True)
    total_distance_km = Column(DOUBLE_PRECISION, nullable=True)
    total_hours = Column(DOUBLE_PRECISION, nullable=True)
    onspot_hours = Column(DOUBLE_PRECISION, nullable=True)
    schedule_hours = Column(DOUBLE_PRECISION, nullable=True)
    ideal_kms = Column(DOUBLE_PRECISION , nullable = True)
    order_kms = Column(DOUBLE_PRECISION , nullable = True)
    utilization_score = Column(DOUBLE_PRECISION, nullable=True)
    date = Column(TIMESTAMP)
    
    



class VehicleDistanceTravelled(Base):
    __tablename__ = 'vehicle_distance_travelled'

    id = Column(Integer, primary_key=True, index=True)
    vehicle_uuid = Column(String , ForeignKey('vehicle_main.vehicle_uuid' , ondelete='CASCADE'))
    distance_travelled_km = Column(DOUBLE_PRECISION)
    driving_hours = Column(DOUBLE_PRECISION)
    date = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    

class VehicleLocation(Base):
    __tablename__ = 'vehicle_location'

    id = Column(Integer, primary_key=True, index=True)
    vehicle_number = Column(String , nullable = False , index = True)
    commtime = Column(BIGINT , default = 0)
    lat = Column(DOUBLE_PRECISION)
    lng = Column(DOUBLE_PRECISION)
    location = Column(Geometry(geometry_type='POINT', srid=4326))
    alti = Column(DOUBLE_PRECISION , default = 0.0)
    devbattery = Column(DOUBLE_PRECISION , default = 0.0)
    vehbattery = Column(DOUBLE_PRECISION , default = 0.0)
    speed = Column(DOUBLE_PRECISION ,default = 0.0)
    heading = Column(DOUBLE_PRECISION , default = 0.0)
    rxdbm = Column(DOUBLE_PRECISION , default = 0.0)
    ignstatus = Column(String , default = "off")
    odometer = Column(DOUBLE_PRECISION , default = 0.0)
    mobili = Column(DOUBLE_PRECISION , default = 0.0)
    fixquality = Column(DOUBLE_PRECISION , default = 0.0)
    devstate = Column(DOUBLE_PRECISION , default = 0.0)
    proctime = Column(BIGINT , default = 0)
    dout_1 = Column(DOUBLE_PRECISION , default = 0.0)
    dout_2 = Column(DOUBLE_PRECISION , default = 0.0)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))

    

class VehicleTelematicInfo(Base):
    __tablename__ = 'vehicle_telematics_info'

    id = Column(Integer, primary_key=True, index=True)
    vehicle_uuid = Column(String , ForeignKey('vehicle_main.vehicle_uuid' , ondelete='CASCADE'))
    make = Column(String)
    model = Column(String)
    battery_capacity_kwh = Column(DOUBLE_PRECISION , default = 7.7)
    full_range_km = Column(DOUBLE_PRECISION , default = 70)
    average_consumption_kwh_per_km = Column(DOUBLE_PRECISION , default = 9.09)
    usable_battery_percentage = Column(DOUBLE_PRECISION , default = 90.0)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))




class VehicleEfficiencyLogs(Base):
    __tablename__ = 'vehicle_efficiency_logs'

    id = Column(Integer, primary_key=True, index=True)
    vehicle_uuid = Column(String , ForeignKey('vehicle_main.vehicle_uuid' , ondelete='CASCADE'))
    driver_id = Column(String , ForeignKey('driver_main.driver_uuid' , ondelete = 'CASCADE'))
    date = Column(TIMESTAMP , nullable = False)
    average_consumption_kwh_per_km = Column(DOUBLE_PRECISION)
    route_type = Column(String)
