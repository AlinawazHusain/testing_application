from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, TIMESTAMP, Sequence , text
from db.base import Base
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from datetime import datetime , timezone
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSONB


class MfoMain(Base):
    __tablename__ = 'mfo_main'
    
    mfo_seq = Sequence('mfo_seq', start=1, increment=1, metadata=Base.metadata)
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    mfo_uuid = Column(String, unique=True, nullable=False, index=True,server_default=text("'MFO-' || nextval('mfo_seq'::regclass)"))
    country_code = Column(String, nullable=False)
    phone_number = Column(String, nullable=False , index = True,)
    alternative_phone_number = Column(String , nullable = True)
    city = Column(String, nullable=True)
    pincode = Column(String, nullable=True)
    name = Column(String, nullable=True)
    email = Column(String, nullable=True)
    years_of_experience = Column(TIMESTAMP, nullable=True)
    profile_image = Column(String, nullable=True)
    aadhar_card = Column(String, nullable=True)
    pan_card = Column(String, nullable=True)
    aadhar_card_back = Column(String, nullable=True)
    # fcm_token = Column(String , nullable = False)
    fcm_token = Column(MutableDict.as_mutable(JSONB), default=dict)
    last_login = Column(TIMESTAMP, nullable=True)
    verification_status = Column(Boolean, default = False)
    also_a_driver = Column(Boolean, nullable=True)
    business_name = Column(String, nullable=True)
    device_id = Column(String ,  nullable=True)
    ip_address = Column(String ,  nullable=True)
    device_model = Column(String ,  nullable=True)
    device_language = Column(String , default = "English UK")
    device_brand = Column(String ,  nullable=True)
    profile_completion_percentage = Column(DOUBLE_PRECISION , nullable = True)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_enable = Column(Boolean , default = True)
    disabled_at = Column(TIMESTAMP , nullable = True)

   
   
    
class MfoBusiness(Base):
    __tablename__ = 'mfo_business'

    id = Column(Integer, primary_key=True, autoincrement=True)
    mfo_uuid = Column(String, ForeignKey('mfo_main.mfo_uuid' , ondelete="CASCADE"), nullable=False , index = True,)
    business_name = Column(String, nullable=True)
    logo = Column(String , nullable = True)
    city = Column(String , nullable = True)
    pincode = Column(String , nullable = True)
    gst_number = Column(String, nullable=True)
    total_number_of_vehicles = Column(Integer , default = 0)
    total_number_of_evs = Column(Integer , default = 0)
    registered_office_address = Column(String, nullable=True)
    operating_address = Column(String, nullable=True)
    business_pan_card = Column(String, nullable=True)
    msme_certificate = Column(String, nullable=True)
    gst_certificate = Column(String, nullable=True)
    udyam_registration = Column(String, nullable=True)
    shop_and_establishment_act_license = Column(String, nullable=True)
    partnership_deed = Column(String, nullable=True)
    certificate_of_incorporation = Column(String, nullable=True)
    business_docs_completion_percentage = Column(DOUBLE_PRECISION ,  default = 0.0)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    


    
class MfoVehicleLeasing(Base):
    __tablename__ = 'mfo_vehicle_leasing'

    id = Column(Integer, primary_key=True, autoincrement=True)
    mfo_uuid = Column(String, ForeignKey('mfo_main.mfo_uuid' , ondelete="CASCADE"), nullable=False , index = True,)
    bank_statement = Column(String, nullable=True)
    itr = Column(String, nullable=True)
    balance_sheet = Column(String, nullable=True)
    proof_of_income_from_logistic_business = Column(String, nullable=True)
    leasing_docs_completion_percentage = Column(DOUBLE_PRECISION , default = 0.0)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
