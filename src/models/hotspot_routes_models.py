from geoalchemy2 import Geometry
from sqlalchemy import DOUBLE_PRECISION, TIMESTAMP, Boolean, Column, ForeignKey, Integer, String, Sequence, text
from db.base import Base 
from datetime import datetime , timezone

class HotspotRoutes(Base):
    __tablename__ = 'hotspot_routes'
    
    hotspot_route_seq = Sequence('hotspot_route_seq', start=1, increment=1, metadata=Base.metadata)

    id = Column(Integer, primary_key=True, index=True)
    hotspot_route_uuid = Column(String, unique=True, nullable=False, index=True, server_default=text("'HOTSPOT_ROUTE-' || nextval('hotspot_route_seq'::regclass)"))
    driver_uuid = Column(String , ForeignKey('driver_main.driver_uuid' , ondelete='SET NULL'))
    start_lat =  Column(DOUBLE_PRECISION , nullable = False)
    start_lng =  Column(DOUBLE_PRECISION , nullable = False)
    start_location =  Column(Geometry(geometry_type='POINT', srid=4326))
    end_lat = Column(DOUBLE_PRECISION , nullable = False)
    end_lng = Column(DOUBLE_PRECISION , nullable = False)
    end_location =  Column(Geometry(geometry_type='POINT', srid=4326))
    route_distance_meters = Column(DOUBLE_PRECISION , nullable = False)
    route_distance_text = Column(String , nullable = False)
    route_duration_seconds = Column(DOUBLE_PRECISION , nullable = False)
    route_duration_text = Column(String , nullable = False)
    route_to_hotspot = Column(Geometry(geometry_type='LINESTRING', srid=4326)) 
    route_overview_polyline = Column(String , nullable = False)
    route_geom = Column(String , nullable = False)
    reached_hotspot = Column(Boolean , default = False)
    reached_hotspot_timestamp = Column(TIMESTAMP, nullable=True)
    got_trip = Column(Boolean , default = False)
    avaronn_porter_trip_uuid = Column(String , ForeignKey('avaronn_porter_trip.avaronn_porter_trip_uuid' , ondelete = 'SET NULL'), nullable = True)
    got_trip_at = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    crn_order_id = Column(String, nullable=True, index=True)
    


class HotspotRoutedeviationLogs(Base):
    __tablename__ = 'hotspot_route_deviation_logs'
    
    id = Column(Integer, primary_key=True, index=True)
    driver_uuid = Column(String , ForeignKey('driver_main.driver_uuid' , ondelete='SET NULL'))
    hotspot_route_uuid = Column(String , ForeignKey('hotspot_routes.hotspot_route_uuid' , ondelete = 'SET NULL') , nullable = False)
    deviated_lat = Column(DOUBLE_PRECISION , nullable = False)
    deviated_lng = Column(DOUBLE_PRECISION , nullable = False)
    deviated_distance_mt = Column(DOUBLE_PRECISION , nullable = False)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    
    
    
class HotspotData(Base):
    __tablename__ = "hotspot_data"

    id = Column(Integer, primary_key=True, index=True)
    driver_geo_region = Column(String)
    pickup_address  = Column(String)
    drop_address  = Column(String)
    start_time = Column(TIMESTAMP)
    end_time  = Column(TIMESTAMP)
    status = Column(String)
    drop_lat = Column(DOUBLE_PRECISION)
    drop_long = Column(DOUBLE_PRECISION)
    pickup_lat = Column(DOUBLE_PRECISION)
    pickup_long = Column(DOUBLE_PRECISION)
    pickup_location = Column(Geometry(geometry_type='POINT', srid=4326))
    drop_location = Column(Geometry(geometry_type='POINT', srid=4326))
       