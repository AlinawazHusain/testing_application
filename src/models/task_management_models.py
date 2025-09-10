from datetime import datetime,timezone
from sqlalchemy import Column, Integer, Sequence, String, TIMESTAMP, JSON, ForeignKey, Time,  text
from db.base import Base

class Schedules(Base):
    __tablename__ = 'schedules'

    schedule_seq = Sequence('schedule_seq', start=1, increment=1, metadata=Base.metadata)
    
    id = Column(Integer, primary_key=True, index=True)
    schedule_uuid = Column(String, unique=True, nullable=False, index=True,server_default=text("'SCH-' || nextval('schedule_seq'::regclass)"))
    mfo_driver_assignment_model = Column(String,ForeignKey('model_types.model_type_uuid' , ondelete="CASCADE") , nullable=True)
    client_uuid = Column(String, ForeignKey('client_main.client_uuid', ondelete="CASCADE"), nullable=True)
    route = Column(JSON, nullable=True)
    schedule_start_time = Column(Time, nullable=False) 
    schedule_end_time = Column(Time, nullable=False) 
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))


class Tasks(Base):
    __tablename__ = 'tasks'
    
    task_seq = Sequence('task_seq', start=1, increment=1, metadata=Base.metadata)

    id = Column(Integer, primary_key=True, index=True)
    task_uuid = Column(String, unique=True, nullable=False, index=True,server_default=text("'TASK-' || nextval('task_seq'::regclass)"))
    vehicle_uuid = Column(String , ForeignKey('vehicle_main.vehicle_uuid', ondelete="CASCADE") , nullable = True)
    mfo_uuid = Column(String, ForeignKey('mfo_main.mfo_uuid', ondelete="CASCADE"), nullable=True)
    model_type = Column(String,ForeignKey('model_types.model_type_uuid') , nullable=True)
    sub_model_type = Column(String , ForeignKey('sub_model_types.sub_model_type_uuid') , nullable = True)
    task_start_time = Column(TIMESTAMP , nullable = False)
    task_end_time = Column(TIMESTAMP , nullable = False)
    task_status_uuid = Column(String, ForeignKey('task_status.task_status_uuid') , nullable=True)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    
    
class TaskScheduleMapping(Base):
    __tablename__ = 'tasks_schedules_mapping'

    id = Column(Integer, primary_key=True, index=True)
    task_uuid = Column(String, ForeignKey('tasks.task_uuid'), nullable=False)
    schedule_uuid = Column(String, ForeignKey('schedules.schedule_uuid', ondelete="CASCADE"), nullable=False)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))