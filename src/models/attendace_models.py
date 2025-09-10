from datetime import datetime, time, timezone
from sqlalchemy import  TIME, Column, Integer, String, Boolean, TIMESTAMP , Sequence , text , ForeignKey
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from db.db import Base
from sqlalchemy.ext.mutable import MutableDict
from sqlalchemy.dialects.postgresql import JSONB

from utils.time_utils import get_utc_time


class DriverAttendance(Base):
    __tablename__ = 'driver_attendance'

    id = Column(Integer, primary_key=True, index=True)
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid' , ondelete="CASCADE") , nullable=False , index=True)
    vehicle_uuid = Column(String, ForeignKey('vehicle_main.vehicle_uuid' , ondelete="CASCADE") , nullable=False , index=True)
    mfo_uuid = Column(String, ForeignKey('mfo_main.mfo_uuid' , ondelete="CASCADE") ,nullable=False , index=True)
    attendance_state_uuid = Column(String, ForeignKey('attendance_states.attendance_state_uuid') ,nullable=True)
    attendance_time = Column(TIME, nullable=True)
    expected_time_stamp = Column(TIME, nullable=True)
    driver_attandence_location_lat = Column(DOUBLE_PRECISION, nullable=True)
    driver_attandence_location_lng = Column(DOUBLE_PRECISION, nullable=True)
    driver_attendance_vehicle_location_lat = Column(DOUBLE_PRECISION, nullable=True)
    driver_attendance_vehicle_location_lng = Column(DOUBLE_PRECISION, nullable=True)
    driver_attendance_vehicle_connected_time_state_uuid = Column(String , ForeignKey('driver_vehicle_connected_time_states.driver_vehicle_connected_time_state_uuid'))
    bluetooth_connection_time = Column(TIME, nullable=True)
    attendance_trigger_time = Column(TIMESTAMP, nullable=True)
    again_requested = Column(Boolean , default = False)
    extra_day_work = Column(Boolean , default = False)
    
    


    
    


class DriverLeaveRequest(Base):
    __tablename__ = 'driver_leave_request'

    
    driver_leave_request_seq = Sequence('driver_leave_request_seq', start=1, increment=1, metadata=Base.metadata)

    id = Column(Integer, primary_key=True, index=True)
    leave_request_uuid = Column(String, unique=True, index = True,server_default=text("'DRIVER_LEAVE_REQUEST-' || nextval('driver_leave_request_seq'::regclass)"))
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid' , ondelete="CASCADE") , nullable=False , index=True)
    mfo_uuid =  Column(String, ForeignKey('mfo_main.mfo_uuid' , ondelete="CASCADE") , nullable=False , index=True)
    start_date = Column(TIMESTAMP, nullable=False)
    end_date = Column(TIMESTAMP, nullable=False)
    leave_type_uuid = Column(String , ForeignKey('leave_types.leave_type_uuid'))
    reason = Column(String)
    leave_status_uuid = Column(String, ForeignKey('request_status.request_status_uuid') ,nullable=True)
    requested_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    reviewed_at = Column(TIMESTAMP , nullable = True)
    reviewed_by = Column(String , nullable = True)
    
    
    

class DriverApprovedLeaves(Base):
    __tablename__ = 'driver_approved_leaves'
    
    id = Column(Integer, primary_key=True, index=True)
    leave_request_uuid = Column(String , ForeignKey('driver_leave_request.leave_request_uuid' , ondelete="CASCADE"))
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid' , ondelete="CASCADE") , nullable=False , index=True)
    leave_date = Column(TIMESTAMP , nullable = False)
    
    
    
    
    
class DriverOffDayWorkRequest(Base):
    __tablename__ = 'driver_off_day_work_request'
    
    driver_work_on_off_day_request_seq = Sequence('driver_work_on_off_day_request_seq', start=1, increment=1, metadata=Base.metadata)

    id = Column(Integer, primary_key=True, index=True)
    work_on_off_day_request_uuid = Column(String, unique=True, index = True,server_default=text("'DRIVER_WORK_ON_OFF_DAY_REQUEST-' || nextval('driver_work_on_off_day_request_seq'::regclass)"))
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid' , ondelete="CASCADE") , nullable=False , index=True)
    mfo_uuid = Column(String, ForeignKey('mfo_main.mfo_uuid' , ondelete="CASCADE") , nullable=False , index=True)
    off_date = Column(TIMESTAMP, nullable=False)
    reason = Column(String, nullable=False)
    request_status_uuid = Column(String, ForeignKey('request_status.request_status_uuid') ,nullable=True)
    requested_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    reviewed_at = Column(TIMESTAMP , nullable = True)
    reviewed_by = Column(String , nullable = True)
    
    
    
    
class DriverApprovedOffDayWorks(Base):
    __tablename__ = 'driverapproved_off_day_works'
     
    id = Column(Integer, primary_key=True, index=True)
    work_on_off_day_request_uuid = Column(String , ForeignKey('driver_off_day_work_request.work_on_off_day_request_uuid' , ondelete="CASCADE"))
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid' , ondelete="CASCADE") , nullable=False , index=True)
    work_date = Column(TIMESTAMP , nullable = False)
    
    
    
    


class DriverOffDays(Base):
    __tablename__ = 'driver_off_days'
    # NOT USING ANYWHERE

    id = Column(Integer, primary_key=True, index=True)
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid' , ondelete="CASCADE") , nullable=False , index=True)
    date = Column(TIMESTAMP, nullable=False)
    type = Column(String)
    assigned_by = Column(String)
    created_at =  Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    
    

class DriverAttendanceSummary(Base):
    __tablename__ = 'driver_attendance_summary'
    
    
    id = Column(Integer, primary_key=True, index=True)
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid' , ondelete="CASCADE") , nullable=False , index=True)
    year = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    total_present_days = Column(Integer, default = 0)
    total_off_days = Column(Integer, default = 0)
    total_leave_days = Column(Integer, default = 0)
    total_worked_on_leave_days = Column(Integer, default = 0)
    unauthorised_off = Column(Integer , default = 0)
    required_working_days = Column(Integer , default = 26)
    final_achieved_days = Column(Integer , default = 0)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    
    

class DriverWorkingPolicy(Base):
    __tablename__ = 'driver_working_policy'
    
    
    id = Column(Integer, primary_key=True, index=True)
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid' , ondelete="CASCADE") , nullable=False , index=True)
    mfo_uuid = Column(String , ForeignKey("mfo_main.mfo_uuid" , ondelete= "CASCADE") , nullable = False , index = True)
    driver_policy_uuid = Column(String , ForeignKey('driver_policy.driver_policy_uuid' , ondelete="CASCADE"))
    valid_from = Column(TIMESTAMP)
    valid_till = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    
    
    
    
class DriverPolicy(Base):
    __tablename__ = 'driver_policy'
    
    driver_policy_seq = Sequence('driver_policy_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_policy_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'DRIVER_POLICY-' || nextval('driver_policy_seq'::regclass)"))
    
    monday_working = Column(Boolean ,default = True)
    tuesday_working = Column(Boolean ,default = True)
    wednesday_working = Column(Boolean ,default = True)
    thursday_working = Column(Boolean , default = True)
    friday_working = Column(Boolean , default = True)
    saturday_working = Column(Boolean , default = True)
    sunday_working = Column(Boolean , default = False)
    
    monthly_working_days = Column(Integer , default = 26)
    
    # attendance_trigger_time = Column(TIME, default=lambda: time(hour=9, minute=30))
    # incentive_model_per_km = Column(MutableDict.as_mutable(JSONB), default=dict)
    
    can_work_on_off_days = Column(Boolean , default = True)
    grace_leave_allowed = Column(Boolean , default = True)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    


class AttendanceRequests(Base):
    __tablename__ = 'attendance_requests'
    
    attendance_request_seq = Sequence('attendance_request_seq', start=1, increment=1, metadata=Base.metadata)
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    attendance_request_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'ATTENDANCE_REQUEST-' || nextval('attendance_request_seq'::regclass)"))
    driver_uuid = Column(String , ForeignKey('driver_main.driver_uuid' , ondelete = 'CASCADE'))
    vehicle_uuid = Column(String , ForeignKey('vehicle_main.vehicle_uuid' , ondelete = 'CASCADE'))
    mfo_uuid = Column(String , ForeignKey('mfo_main.mfo_uuid' , ondelete = 'CASCADE'))
    attendance_request_status = Column(String , default = 'Pending')
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))