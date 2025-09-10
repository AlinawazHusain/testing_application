from sqlalchemy import DOUBLE_PRECISION, Column, Integer, String, Sequence, text
from db.base import Base


class VehicleStatus(Base):
    __tablename__ = 'vehicle_status'
    vehicle_status_seq = Sequence('vehicle_status_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_status_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'VEH_STATUS-' || nextval('vehicle_status_seq'::regclass)"))
    vehicle_status = Column(String, nullable=False)



class TaskStatus(Base):
    __tablename__ = 'task_status'
    task_status_seq = Sequence('task_status_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_status_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'TASK_STATUS-' || nextval('task_status_seq'::regclass)"))
    task_status = Column(String, nullable=False)



class DriverRoles(Base):
    __tablename__ = 'driver_roles'
    
    driver_role_seq = Sequence('driver_role_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_role_uuid = Column(String, unique=True, nullable=False,index = True,  server_default=text("'DR_ROLE-' || nextval('driver_role_seq'::regclass)"))
    driver_role = Column(String, nullable=True)



class FuelTypes(Base):
    __tablename__ = 'fuel_types'

    fuel_type_seq = Sequence('fuel_type_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    fuel_type_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'FUEL-' || nextval('fuel_type_seq'::regclass)"))
    fuel_type = Column(String, nullable=False)
    icon_link = Column(String, nullable=True)



class AttendanceStates(Base):
    __tablename__ = 'attendance_states'
    
    attendance_state_seq = Sequence('attendance_state_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    attendance_state_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'ATTENDANCE_STATE-' || nextval('attendance_state_seq'::regclass)"))
    attendance_state = Column(String, nullable=False)

class DriverVehicleConnectedTimeStates(Base):
    __tablename__ = 'driver_vehicle_connected_time_states'
    driver_vehicle_connected_time_states_seq = Sequence('driver_vehicle_connected_time_states_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    driver_vehicle_connected_time_state_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'DRIVER_VEHICLE_CONNECT_TIME_STATE-' || nextval('driver_vehicle_connected_time_states_seq'::regclass)"))
    driver_vehicle_connected_time_state = Column(String, nullable=False)
    

class VehicleUnlockStates(Base):
    __tablename__ = 'vehicle_unlock_states'

    vehicle_unlock_state_seq = Sequence('vehicle_unlock_state_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    vehicle_unlock_state_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'UNLOCK_STATE-' || nextval('vehicle_unlock_state_seq'::regclass)"))
    vehicle_unlock_state = Column(String, nullable=False)



class ModelTypes(Base):
    __tablename__ = 'model_types'

    model_type_seq = Sequence('model_type_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    model_type_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'MODEL-' || nextval('model_type_seq'::regclass)"))
    model_type = Column(String, nullable=False)


class SubModelTypes(Base):
    __tablename__ = 'sub_model_types'

    sub_model_type_seq = Sequence('sub_model_type_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    sub_model_type_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'SUB_MODEL-' || nextval('sub_model_type_seq'::regclass)"))
    sub_model_type = Column(String, nullable=False)
    

class FuelBaseCosting(Base):
    __tablename__ = 'fuel_base_costing'
    
    fuel_base_costing_seq = Sequence('fuel_base_costing_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    fuel_base_costing_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'FUEL_BASE_COSTING-' || nextval('fuel_base_costing_seq'::regclass)"))
    vehicle_category = Column(String, nullable=False)
    fuel = Column(String, nullable=False)
    per_km_cost = Column(DOUBLE_PRECISION)
    



    
class RequestStatus(Base):
    __tablename__ = 'request_status'
    
    request_status_seq = Sequence('request_status_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    request_status_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'REQUEST_STATUS-' || nextval('request_status_seq'::regclass)"))
    request_status = Column(String, nullable=False)



class LeaveTypes(Base):
    __tablename__ = 'leave_types'
    
    leave_types_seq = Sequence('leave_types_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    leave_type_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'LEAVE_TYPE-' || nextval('leave_types_seq'::regclass)"))
    leave_type = Column(String, nullable=False)


class TaskTypes(Base):
    __tablename__ = 'task_types'
    
    task_types_seq = Sequence('task_types_seq', start=1, increment=1, metadata=Base.metadata)
    id = Column(Integer, primary_key=True, autoincrement=True)
    task_type_uuid = Column(String, unique=True, nullable=False,index = True, server_default=text("'TASK_TYPE-' || nextval('task_types_seq'::regclass)"))
    task_type = Column(String, nullable=False)
    points = Column(DOUBLE_PRECISION , default = 0.0)
