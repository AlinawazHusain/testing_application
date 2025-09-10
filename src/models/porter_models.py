from geoalchemy2 import Geometry
from sqlalchemy import  TIME, Column,  Integer, String, TIMESTAMP, Interval, ForeignKey , Sequence, text
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION

from db.base import Base

class AvaronnPorterTrip(Base):
    __tablename__ = 'avaronn_porter_trip'
    avaronn_porter_trip_seq = Sequence('avaronn_porter_trip_seq', start=1, increment=1, metadata=Base.metadata)

    id = Column(Integer, primary_key=True, index=True)
    avaronn_porter_trip_uuid = Column(String, unique=True, index=True,server_default=text("'AVARONN_PORTER_TRIP-' || nextval('avaronn_porter_trip_seq'::regclass)"))
    
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="SET NULL"))
    vehicle_uuid = Column(String, ForeignKey('vehicle_main.vehicle_uuid', ondelete="CASCADE"), nullable=False)
    schedule_uuid = Column(String, ForeignKey('schedules.schedule_uuid', ondelete="CASCADE"), nullable=False)
    trip_on_lat = Column(DOUBLE_PRECISION, nullable=True)
    trip_on_lng = Column(DOUBLE_PRECISION, nullable=True)
    trip_on_location = Column(Geometry(geometry_type='POINT', srid=4326))
    
    trip_off_lat = Column(DOUBLE_PRECISION, nullable=True)
    trip_off_lng = Column(DOUBLE_PRECISION, nullable=True)
    trip_off_location = Column(Geometry(geometry_type='POINT', srid=4326))
    
    trip_on_time = Column(TIMESTAMP, nullable=True)
    trip_off_time = Column(TIMESTAMP, nullable=True)
    expected_earning = Column(DOUBLE_PRECISION)
    expected_distance_km = Column(DOUBLE_PRECISION)
    expected_cost = Column(DOUBLE_PRECISION)
    total_trip_time = Column(Interval, nullable=True)
    
    

class PorterPnL(Base):
    __tablename__ = 'porter_pnl'
    
    porter_PnL_seq = Sequence('porter_pnl_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, index=True)
    porter_pnl_uuid = Column(String, unique=True, index=True,server_default=text("'PORTER_PNL-' || nextval('porter_pnl_seq'::regclass)"))
    date = Column(TIMESTAMP)
    driver_uuid = Column(String)
    vehicle_uuid = Column(String)
    porter_order_id = Column(String)
    trip_fare = Column(DOUBLE_PRECISION)
    trip_earnings = Column(DOUBLE_PRECISION)
    trip_commission = Column(DOUBLE_PRECISION)
    trip_status = Column(String)
    wallet_transaction = Column(DOUBLE_PRECISION)
    avaronn_porter_trip_uuid = Column(String)
    trip_start_time = Column(TIMESTAMP)
    trip_end_time = Column(TIMESTAMP)
    pickup_lat = Column(DOUBLE_PRECISION)
    pickup_lng = Column(DOUBLE_PRECISION)
    drop_lat = Column(DOUBLE_PRECISION)
    drop_lng = Column(DOUBLE_PRECISION)
    distance_km = Column(DOUBLE_PRECISION)
    duration_min = Column(TIME)


class PorterDriverPerformance(Base):
    __tablename__ = "porter_driver_performance"
    
    porter_driver_performance_seq = Sequence('porter_driver_performance_seq', start=1, increment=1, metadata=Base.metadata)

    id = Column(Integer, primary_key=True, index=True)
    porter_driver_performance_uuid = Column(String, unique=True, index=True,server_default=text("'PORTER_DRIVER_PERFORMANCE-' || nextval('porter_driver_performance_seq'::regclass)"))
    
    date = Column(TIMESTAMP)
    driver_uuid = Column(String)
    vehicle_uuid = Column(String)
    total_login_time_hrs = Column(DOUBLE_PRECISION)
    idle_time_hrs = Column(DOUBLE_PRECISION)
    time_spent_on_orders_in_hrs = Column(DOUBLE_PRECISION)
    distance_in_order_km = Column(DOUBLE_PRECISION)
    distance_in_idle_km = Column(DOUBLE_PRECISION)
    total_distance_km = Column(DOUBLE_PRECISION)
    notifications_received = Column(Integer)
    notification_accepeted = Column(Integer)
    acceptance_rate_pct = Column(DOUBLE_PRECISION)
    utilizaion_pct = Column(DOUBLE_PRECISION)
    first_login_time = Column(TIMESTAMP)
    last_logout_time = Column(TIMESTAMP)
    first_cluster = Column(String)
    last_cluster = Column(String)

