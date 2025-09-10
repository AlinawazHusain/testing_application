from sqlalchemy import and_, create_engine, select
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from db.base import Base
from models.assignment_mapping_models import *
from models.client_models import *
from models.driver_models import *
from models.mfo_models import *
from models.porter_models import *
from models.status_models import *
from models.task_management_models import *
from models.transition_models import *
from models.vehicle_models import *
from models.costing_models import *
from models.log_models import *
from models.attendace_models import *
from settings.credential_settings import credential_setting
from config.exceptions import DatabaseError
from sqlalchemy.exc import SQLAlchemyError
from db.static_tables_data import *
from models.can_data_model import *
from models.vehicle_hub_models import *
from models.notification_listner_models import *


"""
Database Configuration and Initialization Module.

This module sets up both synchronous and asynchronous database engines using SQLAlchemy.
It includes:
- Connection strings for PostgreSQL
- Session factories for both sync and async usage
- Utility functions to get database sessions
- A function to create tables and insert static reference data if not already present

Environment variables and AWS parameter store secrets are used for securely injecting credentials.

Functions:
-----------
- get_db():
    Provides a synchronous session scope for use with traditional SQLAlchemy operations.

- get_async_db():
    Async generator function that yields an `AsyncSession` for database operations in an async context.

- create_db_and_tables():
    Initializes all database tables from SQLAlchemy models and inserts static reference data 
    such as statuses, roles, fuel types, model types, and others required for the system.

Raises:
-------
- DatabaseError:
    Raised if any exception occurs during the creation of tables or insertion of data.

Examples:
---------
>>> async with get_async_db() as session:
>>>     result = await session.execute(select(SomeModel))
>>>     data = result.scalars().all()

>>> await create_db_and_tables()
"""


DATABASE_URL=f"postgresql://dbmasteruser:{credential_setting.avronn_backend_db}@{credential_setting.avaronn_backend_db_endpoint}:5432/{credential_setting.database_name}"
DATABASE_URL_ASYNC=f"postgresql+asyncpg://dbmasteruser:{credential_setting.avronn_backend_db}@{credential_setting.avaronn_backend_db_endpoint}:5432/{credential_setting.database_name}"

# DATABASE_URL=f"postgresql://postgres:root@localhost:5432/testdb"
# DATABASE_URL_ASYNC=f"postgresql+asyncpg://postgres:root@localhost:5432/testdb"
# DATABASE_URL_FLEETWISE_ASYNC = f"postgresql+asyncpg://dbmasteruser:{credential_setting.avronn_backend_db}@{credential_setting.avaronn_backend_db_endpoint}:5432/Avaronn_CLIENTWISE_DEVELOPMENT"

# async_engine_clientwise: AsyncEngine = create_async_engine(DATABASE_URL_FLEETWISE_ASYNC)

# AsyncSessionLocalClientwise = sessionmaker(
#     async_engine_clientwise, class_=AsyncSession, expire_on_commit=False
# )



# async def get_async_clientwise_db():
#     async with AsyncSessionLocalClientwise() as session:
#         try:
#             yield session
#         finally:
#             await session.close()
 
 
engine = create_engine(DATABASE_URL)


SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

async_engine: AsyncEngine = create_async_engine(DATABASE_URL_ASYNC)

AsyncSessionLocal = sessionmaker(
    async_engine, class_=AsyncSession, expire_on_commit=False
)



async def get_async_db():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

def get_async_session_factory():
    return AsyncSessionLocal

            
            
            
async def create_db_and_tables(skip_insertion_static_data = False):
    """
    Initializes the database and creates the necessary tables, inserting predefined data into various tables 
    if no records already exist for the specified values.

    This function will create the database tables defined in the `Base.metadata`, then proceed to insert default values 
    into predefined tables like `VehicleStatus`, `TaskStatus`, `DriverRoles`, `FuelTypes`, `AttendanceStates`, `UnlockStates`, 
    `DriverVehicleConnectedTimeStates`, `ModelTypes`, `FuelBaseCosting`, `RequestStatus`, `LeaveTypes`, and `ClientMain` 
    based on predefined lists and dictionaries. If any of these records already exist, they are not added again.

    **Procedure:**
    1. Create tables defined in the metadata.
    2. Check if predefined data exists in the respective tables.
    3. Insert predefined data where no records exist.

    :raises DatabaseError: If an error occurs while creating tables or inserting data.
    """
    
    
    
    print(f"Running with Database -> {credential_setting.database_name}")

    async with async_engine.begin() as conn:
        try:        
            await conn.run_sync(Base.metadata.create_all)
        except SQLAlchemyError as e:
            raise DatabaseError(message= f"Failed to initialize tables with data: {str(e)}")      
    if skip_insertion_static_data:
        return
            
    async with AsyncSessionLocal() as session:
        try:
            
            for status in vehicle_statuses:
                existing_status = await session.execute(select(VehicleStatus).where(VehicleStatus.vehicle_status == status))
                if not existing_status.scalars().first():
                    session.add(VehicleStatus(vehicle_status=status))



           
            for status in task_statuses:
                existing_status = await session.execute(select(TaskStatus).where(TaskStatus.task_status == status))
                if not existing_status.scalars().first():
                    session.add(TaskStatus(task_status=status))
            
            
            
            for role in driver_roles:
                existing_status = await session.execute(select(DriverRoles).where(DriverRoles.driver_role == role))
                if not existing_status.scalars().first():
                    session.add(DriverRoles(driver_role=role))
                
            
            
            for fuel in fuel_types:
                existing_status = await session.execute(select(FuelTypes).where(FuelTypes.fuel_type == fuel))
                if not existing_status.scalars().first():
                    session.add(FuelTypes(fuel_type=fuel))
                    
                    
            
            for attendance in attendance_states:
                existing_status = await session.execute(select(AttendanceStates).where(AttendanceStates.attendance_state == attendance))
                if not existing_status.scalars().first():
                    session.add(AttendanceStates(attendance_state=attendance))


            
            for unlock in unlock_states:
                existing_status = await session.execute(select(VehicleUnlockStates).where(VehicleUnlockStates.vehicle_unlock_state == unlock))
                if not existing_status.scalars().first():
                    session.add(VehicleUnlockStates(vehicle_unlock_state=unlock))
            
            
            for connected_time_state in driver_vehicle_connected_time_states:
                existing_status = await session.execute(select(DriverVehicleConnectedTimeStates).where(DriverVehicleConnectedTimeStates.driver_vehicle_connected_time_state == connected_time_state))
                if not existing_status.scalars().first():
                    session.add(DriverVehicleConnectedTimeStates(driver_vehicle_connected_time_state=connected_time_state))
            
            
            
            
            for model in model_types:
                existing_status = await session.execute(select(ModelTypes).where(ModelTypes.model_type == model))
                if not existing_status.scalars().first():
                    session.add(ModelTypes(model_type=model))
            
            
            for sub_model in sub_model_types:
                existing_status = await session.execute(select(SubModelTypes).where(SubModelTypes.sub_model_type == sub_model))
                if not existing_status.scalars().first():
                    session.add(SubModelTypes(sub_model_type=sub_model))

            
            for category, fuels in VEHICLE_COST_PER_KM.items():
                for fuel, cost in fuels.items():
                    existing_status = await session.execute(select(FuelBaseCosting).where(and_(FuelBaseCosting.vehicle_category == category , FuelBaseCosting.fuel == fuel)))
                    if not existing_status.scalars().first():
                        session.add(FuelBaseCosting(vehicle_category = category , fuel = fuel , per_km_cost = cost))
            
            
            for request in request_status:
                existing_status = await session.execute(select(RequestStatus).where(RequestStatus.request_status == request))
                if not existing_status.scalars().first():
                    session.add(RequestStatus(request_status = request))
                    
                    
            for leave_type in leave_types:
                existing_status = await session.execute(select(LeaveTypes).where(LeaveTypes.leave_type == leave_type))
                if not existing_status.scalars().first():
                    session.add(LeaveTypes(leave_type = leave_type))
                    
            
            for task_type, point in task_types.items():
                result = await session.execute(
                    select(TaskTypes).where(TaskTypes.task_type == task_type)
                )
                existing_status = result.scalars().first()
                if existing_status:
                    existing_status.points = point
                else:
                    session.add(TaskTypes(task_type=task_type, points=point))

                
            
            existing_status = await session.execute(select(ClientMain).where(ClientMain.name == 'Avaronn'))
            if not existing_status.scalars().first():
                session.add(ClientMain(name = "Avaronn"))
                
            await session.commit()
        except SQLAlchemyError as e:
            await session.rollback()
            raise DatabaseError(message=f"Failed to initialize tables with data: {str(e)}")
            
