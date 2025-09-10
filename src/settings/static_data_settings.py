import asyncio
from db.database_operations import fetch_from_table
from db.db import get_async_db
from models.status_models import (
    LeaveTypes, RequestStatus, TaskTypes, VehicleStatus, TaskStatus, DriverRoles,
    FuelTypes , AttendanceStates, DriverVehicleConnectedTimeStates,
    ModelTypes , FuelBaseCosting,
    SubModelTypes, VehicleUnlockStates 
)


class StaticTableSettings:
    def __init__(self):
        """ Synchronous constructor initializes an empty dictionary. """
        self.static_table_data = {}

    async def load_static_tables_data(self):
        """ Asynchronous method to load static data from the database. """
        async for session in get_async_db():
            try:
                data = await asyncio.gather(
                    fetch_from_table(session, VehicleStatus),
                    fetch_from_table(session, TaskStatus),
                    fetch_from_table(session, DriverRoles),
                    fetch_from_table(session, FuelTypes),
                    fetch_from_table(session, AttendanceStates),
                    fetch_from_table(session, DriverVehicleConnectedTimeStates),
                    fetch_from_table(session, VehicleUnlockStates),
                    fetch_from_table(session, ModelTypes),
                    fetch_from_table(session, SubModelTypes),
                    fetch_from_table(session, FuelBaseCosting),
                    fetch_from_table(session, RequestStatus),
                    fetch_from_table(session, LeaveTypes),
                    fetch_from_table(session, TaskTypes),
                )
                vehicle_status_mapping = {
                    item["vehicle_status_uuid"]: item["vehicle_status"]
                    for item in data[0]
                }
                task_status_mapping = {
                    item["task_status_uuid"] : item["task_status"]
                    for item in data[1]
                }
                driver_roles_mapping = {
                    item["driver_role_uuid"] : item["driver_role"]
                    for item in data[2]
                }
                fuel_type_mapping = {
                    item["fuel_type_uuid"] : item["fuel_type"]
                    for item in data[3]
                }
                attendance_state_mapping = {
                    item["attendance_state_uuid"] : item["attendance_state"]
                    for item in data[4]
                }
                driver_vehicle_connected_time_state_mapping = {
                    item["driver_vehicle_connected_time_state_uuid"] : item["driver_vehicle_connected_time_state"]
                    for item in data[5]
                }
                vehicle_unlock_states_mapping = {
                    item["vehicle_unlock_state_uuid"] : item["vehicle_unlock_state"]
                    for item in data[6]
                }
                model_types_mapping = {
                    item["model_type_uuid"] : item["model_type"]
                    for item in data[7]
                }
                
                sub_model_types_mapping = {
                    item["sub_model_type_uuid"] : item["sub_model_type"]
                    for item in data[8]
                }
                
                
                vehicle_fuel_mapping = {}
                for entry in data[9]:
                    category = entry['vehicle_category']
                    fuel = entry['fuel']
                    uuid = entry['fuel_base_costing_uuid']
                    
                    if category not in vehicle_fuel_mapping:
                        vehicle_fuel_mapping[category] = {}
                    
                    vehicle_fuel_mapping[category][fuel] = uuid

                uuid_cost_mapping = {entry['fuel_base_costing_uuid']: entry['per_km_cost'] for entry in data[9]}
                
                request_status_mapping  = {
                    item["request_status_uuid"] : item["request_status"]
                    for item in data[10]
                }
                
                leave_types_mapping  = {
                    item["leave_type_uuid"] : item["leave_type"]
                    for item in data[11]
                }
                
                task_types_mapping = {
                    item["task_type_uuid"] : {"task_type" : item["task_type"]  , "points" : item["points"]}
                    for item in data[12]
                }
                

                self.static_table_data = {
                    "VEHICLE_STATUS": vehicle_status_mapping,
                    "TASK_STATUS": task_status_mapping,
                    "DRIVER_ROLES": driver_roles_mapping,
                    "FUEL_TYPES": fuel_type_mapping,
                    "ATTENDANCE_STATES": attendance_state_mapping,
                    "DRIVER_VEHICLE_CONNECTED_TIME_STATES": driver_vehicle_connected_time_state_mapping,
                    "VEHICLE_UNLOCK_STATES": vehicle_unlock_states_mapping,
                    "MODEL_TYPES": model_types_mapping,
                    "SUB_MODEL_TYPES" : sub_model_types_mapping,
                    "FUEL_BASED_COSTING": uuid_cost_mapping,
                    "FUEL_BASED_COSTING_UUID": vehicle_fuel_mapping,
                    "REQUEST_STATUSES" : request_status_mapping,
                    "LEAVE_TYPES" : leave_types_mapping,
                    "TASK_TYPES" : task_types_mapping
                }

                await session.close()
                
                # df = pd.read_csv('static/clustered_data.csv')
                # cluster_centers = df.groupby('cluster').agg({'lat': 'mean', 'long': 'mean'}).reset_index()

                # # Build KDTree for quick nearest cluster lookup
                # cluster_tree = KDTree(cluster_centers[['lat', 'long']].values)
                # self.static_table_data["CLUSTED_CSV_DATA"] = df
                # self.static_table_data["CLUSTER_CENTERS"] = cluster_centers
                # self.static_table_data["CLUSTERED_TREE"] = cluster_tree

            except Exception as e:
                print(f"Error loading static tables: {e}")

    def __getattr__(self, item):
        """ Retrieve values from the static table data dictionary. """
        if item in self.static_table_data:
            return self.static_table_data[item]
        raise AttributeError(f"Parameter '{item}' not found in static data.")


static_table_settings = StaticTableSettings()

async def initialize_static_data():
    await static_table_settings.load_static_tables_data()
