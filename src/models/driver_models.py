from datetime import datetime, timezone
from geoalchemy2 import Geometry
from sqlalchemy import  Column, Integer, String, Boolean, TIMESTAMP , Sequence , text , ForeignKey
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSONB
from db.db import Base


class DriverMain(Base):
    __tablename__ = 'driver_main'
    
    driver_seq = Sequence('driver_seq', start=1, increment=1, metadata=Base.metadata)

    id = Column(Integer, primary_key=True, index=True)
    driver_uuid = Column(String, unique=True, nullable=False, index=True, server_default=text("'DR-' || nextval('driver_seq'::regclass)"))
    country_code = Column(String, nullable=False)
    phone_number = Column(String, nullable=False , index=True)
    city = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    name = Column(String, nullable=True)
    profile_image = Column(String, nullable=True)
    aadhar_card = Column(String, nullable=True)
    pan_card = Column(String, nullable=True)
    driving_license = Column(String, nullable=True)
    aadhar_card_back = Column(String, nullable=True)
    # fcm_token = Column(String , nullable = False)
    fcm_token = Column(MutableDict.as_mutable(JSONB), default=dict)
    alternative_phone_number = Column(String, nullable=True)
    years_of_experience = Column(TIMESTAMP, nullable=True)
    used_ev_before = Column(Boolean , default = False)
    distance_driven = Column(DOUBLE_PRECISION, default = 0)
    assignments_completed = Column(Integer,default=0)
    verification_status = Column(Boolean, default = False)
    score = Column(DOUBLE_PRECISION, default= 75.0)
    main_profile_completion_percentage = Column(DOUBLE_PRECISION , default = 0.0)
    docs_completion_percentage = Column(DOUBLE_PRECISION , default = 0.0)
    device_id = Column(String ,  nullable=True)
    ip_address = Column(String ,  nullable=True)
    device_model = Column(String ,  nullable=True)
    device_language = Column(String , default = "English UK")
    device_brand = Column(String ,  nullable=True)
    support_nfc = Column(Boolean , default = False)
    last_login = Column(TIMESTAMP, nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_update_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_enable = Column(Boolean , default = True)
    disabled_at = Column(TIMESTAMP , nullable = True)





class DriverLocation(Base):
    __tablename__ = 'driver_location'

    id = Column(Integer, primary_key=True, index=True)
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid' , ondelete="CASCADE") , nullable=False , index = True)
    lat = Column(DOUBLE_PRECISION, nullable=True)
    lng = Column(DOUBLE_PRECISION, nullable=True)
    location = Column(Geometry(geometry_type='POINT', srid=4326))
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))