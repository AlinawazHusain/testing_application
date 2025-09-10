from datetime import datetime, timezone
from sqlalchemy import  Column, Integer, String, Boolean, TIMESTAMP , Sequence , text , ForeignKey
from sqlalchemy.dialects.postgresql import DOUBLE_PRECISION
from db.db import Base




class IncentiveProgram(Base):
    __tablename__ = 'incentive_program'
    
    incentive_program_seq = Sequence('incentive_program_seq', start=1, increment=1, metadata=Base.metadata)

    id = Column(Integer, primary_key=True, index=True)
    incentive_program_uuid = Column(String, unique=True, nullable=False, index=True, server_default=text("'INCENTIVE_PROGRAM-' || nextval('incentive_program_seq'::regclass)"))
    mfo_uuid = Column(String , ForeignKey('mfo_main.mfo_uuid' , ondelete="CASCADE") , nullable = False)
    is_enabled = Column(Boolean ,nullable = False ,  default = False)
    base_rate_per_km = Column(DOUBLE_PRECISION , nullable = False , default = 0.0)
    bonus_threshold_km = Column(DOUBLE_PRECISION , nullable = False , default = 0.0)
    bonus_rate_km = Column(DOUBLE_PRECISION , nullable = False , default = 0.0)
    daily_task_requried = Column(Boolean , default = False)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_update_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    

class DriverIncentiveProgram(Base):
    __tablename__ = "driver_incentive_program"
    
    id = Column(Integer , primary_key=True , index = True)
    mfo_uuid = Column(String , ForeignKey('mfo_main.mfo_uuid' , ondelete = "SET NULL"))
    driver_uuid = Column(String , ForeignKey('driver_main.driver_uuid' , ondelete='SET NULL'))
    vehicle_uuid = Column(String , ForeignKey('vehicle_main.vehicle_uuid' , ondelete='SET NULL'))
    incentive_program_uuid = Column(String , ForeignKey("incentive_program.incentive_program_uuid" , ondelete = "SET NULL"))
    is_enabled = Column(Boolean , default = False)
    effective_from = Column(TIMESTAMP , nullable = True)
    effective_to  = Column(TIMESTAMP , nullable = True)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    


class DriverDailyTasks(Base):
    __tablename__ = "driver_daily_tasks"
    
    id = Column(Integer , primary_key=True , index = True)
    mfo_uuid = Column(String , ForeignKey("mfo_main.mfo_uuid" , ondelete = "SET NULL"))
    vehicle_uuid = Column(String , ForeignKey("vehicle_main.vehicle_uuid" , ondelete = "SET NULL"))
    driver_uuid = Column(String , ForeignKey("driver_main.driver_uuid" , ondelete="CASCADE"))
    task_type_uuid = Column(String , ForeignKey('task_types.task_type_uuid'))
    points_earned = Column(Integer , default = 0)
    is_completed = Column(Boolean , default = True)
    completed_at = Column(TIMESTAMP)



class DailyDriverIncentive(Base):
    __tablename__ = 'daily_driver_incentive'
    
    id  = Column(Integer , primary_key=True , index = True)
    driver_uuid = Column(String , ForeignKey('driver_main.driver_uuid' , ondelete = 'CASCADE') , nullable = False)
    mfo_uuid = Column(String , ForeignKey('mfo_main.mfo_uuid' , ondelete='SET NULL'))
    vehicle_uuid = Column(String , ForeignKey('vehicle_main.vehicle_uuid' , ondelete='SET NULL'))
    trip_date = Column(TIMESTAMP , nullable = False)
    
    daily_tasks_points = Column(Integer , default = 0)
    daily_task_points_created = Column(Integer , default = 0)
    
    revenue_km = Column(DOUBLE_PRECISION , default = 0.0)
    base_rate = Column(DOUBLE_PRECISION , default = 0.0)
    incentive_earning = Column(DOUBLE_PRECISION , default = 0.0)
    
    total_task_asssigned = Column(Integer , default = 0)
    toal_task_completed = Column(Integer , default = 0)
    
    incentive_unlock_percentage = Column(DOUBLE_PRECISION , default = 0.0)
    
    final_incentive = Column(DOUBLE_PRECISION , default = 0.0)
    incentive_in_wallet = Column(DOUBLE_PRECISION , default = 0.0)
    
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    

class MonthlyDriverIncentive(Base):
    __tablename__ = 'monthly_driver_incentive'
    
    id  = Column(Integer , primary_key=True , index = True)
    driver_uuid = Column(String , ForeignKey('driver_main.driver_uuid' , ondelete = 'CASCADE') , nullable = False)
    month_start = Column(TIMESTAMP , nullable = False)
    month = Column(Integer , nullable = False)
    year = Column(Integer , nullable  = False)
    points_earned = Column(Integer , default = 0)
    total_points = Column(Integer , default = 0)
    total_revenue_km = Column(DOUBLE_PRECISION , default = 0.0)
    base_km = Column(DOUBLE_PRECISION , default = 0.0)
    base_rate = Column(DOUBLE_PRECISION , default = 0.0)
    bonus_km = Column(DOUBLE_PRECISION , default = 0.0)
    bonus_rate = Column(DOUBLE_PRECISION , default = 0.0)
    base_incentive = Column(DOUBLE_PRECISION , default = 0.0)
    bonus_incentive = Column(DOUBLE_PRECISION , default = 0.0)
    total_incentive_earned = Column(DOUBLE_PRECISION , default = 0.0)
    total_incentive = Column(DOUBLE_PRECISION , default = 0.0)
    total_days_eligible = Column(Integer , default = 0)
    incentive_paid = Column(Boolean , default = False)
    paid_on = Column(TIMESTAMP)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))    