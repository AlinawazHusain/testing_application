import calendar
from fastapi import APIRouter , Depends, File, Form, Header, Request, UploadFile
from datetime import datetime,timedelta, timezone
from sqlalchemy import and_, desc, func, select
from auth.dependencies import mfo_role_required
from config.exceptions import ConflictError, NotFoundError
from db.database_operations import fetch_from_table, get_tuple_instance, insert_into_table, update_table
from helpers.mfo_helpers.mfo_driver_helper import create_attendance, create_driver_policy
from helpers.mfo_helpers.mfo_vehicle_helpers import create_avaronn_schedule_and_task, get_vehicle_details, get_vehicle_current_activity, get_vehicle_tag
from integrations.aws_utils import upload_file_to_s3
from integrations.location_service import get_location_name
from models.attendace_models import DriverWorkingPolicy, DriverApprovedLeaves, DriverAttendance
from models.can_data_model import CANData
from models.petty_expense_models import PettyExpenses
from models.porter_models import PorterDriverPerformance
from models.status_models import FuelBaseCosting
from models.vehicle_models import VehicleLocation, VehicleMain, VehicleUtilization
from schemas.v1.standard_schema import standard_success_response
from schemas.v1.mfo_schemas.mfo_vehicle_management_schema import(
    add_driver_to_vehicle_request, add_driver_to_vehicle_response,
    get_unassigned_vehicle_data_request, get_unassigned_vehicle_data_response,
    get_vehicle_assigned_data_soc_and_speed, mapped_driver_data, other_available_driver_data,
    remove_driver_from_vehicle_request, remove_driver_from_vehicle_response, remove_vehicle_request, remove_vehicle_response, unassign_driver_from_vehicle_request, unassign_driver_from_vehicle_response,
    unassigned_vehicles , assigned_vehicles,
    add_vehicle_request, add_vehicle_response, assign_driver_to_vehicle_request,
    assign_driver_to_vehicle_response, get_all_vehicle_data_response, get_vehicle_assigned_data_request,
    get_vehicle_assigned_data_response, get_vehicle_costing_request, get_vehicle_costing_response,
    get_vehicle_data_request, get_vehicle_data_response, get_vehicle_detail_request,
    get_vehicle_detail_response, get_vehicle_docs_request, get_vehicle_docs_response,
    update_vehicle_costing_request, update_vehicle_costing_response, update_vehicle_docs_response, 
    vehicle_assigned_driver, vehicle_assigned_header, vehicle_cost_summary, vehicle_distance_utilization, vehicle_live_location,
    vehicle_mapped_driver, vehicle_time_utilization, vehicle_performance
    )
from sqlalchemy.ext.asyncio import AsyncSession

from db.db import get_async_db
from models.assignment_mapping_models import DriverMfoMapping, MfoVehicleMapping , DriverVehicleMapping
from models.costing_models import VehicleCosting
from models.driver_models import DriverLocation, DriverMain
from dotenv import load_dotenv
from settings.static_data_settings import static_table_settings
from utils.response import success_response
from utils.time_utils import convert_utc_to_ist, get_utc_time
from utils.vehicle_activity_rule_engine import get_vehile_activity

load_dotenv()




mfo_vehicle_management_router = APIRouter()



name_role_mapping = {
        'primary_driver' : "Primary",
        "secondary_driver" : "Secondary",
        "tertiary1_driver" : "Tertiary1",
        "tertiary2_driver" : "Tertiary2",
        "supervisor_driver" : "Supervisor"
    }








@mfo_vehicle_management_router.post("/getVehicleDetail" , response_model= standard_success_response[get_vehicle_detail_response])
async def get_vehicle_detail_api(request:Request,
                             req:get_vehicle_detail_request,
                             mfo_uuid = Depends(mfo_role_required()),
                             session_id: str = Header(..., alias="session-id"),
                             device_id: str = Header(..., alias="device-id")
                             ):
    
    data , path_to_s3 = await get_vehicle_details(req.vehicle_number)
    data_res = get_vehicle_detail_response(**data)
    return success_response(request , data_res , message = "Vehicle Details Get successfully")
    







@mfo_vehicle_management_router.post("/addVehicle" , response_model = standard_success_response[add_vehicle_response] , status_code=201)
async def add_vehicle(request:Request,
                      req : add_vehicle_request ,
                      mfo_uuid = Depends(mfo_role_required()),
                      session:AsyncSession = Depends(get_async_db),
                      session_id: str = Header(..., alias="session-id"),
                      device_id: str = Header(..., alias="device-id")
                      ):
    
    vehicle_details , path_to_s3 = await get_vehicle_details(req.vehicle_number)
    fuel_type = vehicle_details['fuel_type']
    
    vehicle_exist = await fetch_from_table(session , VehicleMain , None , {"vehicle_number" : req.vehicle_number , "is_enable" : True})
    if vehicle_exist:
        raise ConflictError("Vehilce already exists with you" if vehicle_exist[0]['mfo_uuid'] == mfo_uuid else "Vehicle already exists with another MFO")
    
    
    
    fuel_types_dict = static_table_settings.static_table_data['FUEL_TYPES']
    vehicle_statuses_dict = static_table_settings.static_table_data['VEHICLE_STATUS']
    fuel_based_costing_dict = static_table_settings.static_table_data['FUEL_BASED_COSTING_UUID']
    
    fuel_type_uuid = next((k for k, v in fuel_types_dict.items() if v == fuel_type), None)
    vehicle_status_uuid = next((k for k, v in vehicle_statuses_dict.items() if v == 'Inactive'), None)
    fuel_based_costing_uuid = None
    category = fuel_based_costing_dict.get(vehicle_details['category'] , None) 
    if category:
        fuel_based_costing_uuid = category.get(fuel_type , None)
    
    vehicle_main_data = {
        'mfo_uuid' :  mfo_uuid,
        'vehicle_number' :  req.vehicle_number,
        'details' :  path_to_s3,
        'insurance_upto' :  vehicle_details['insurance_upto'],
        'category' :  vehicle_details['category'],
        'financed' :  vehicle_details['financed'],
        'commercial' :  vehicle_details['commercial'],
        'fuel_type' :  fuel_type_uuid,
        "vehicle_status" : vehicle_status_uuid,
        "vehicle_model" : vehicle_details['vehicle_model']
    }
    
    vehicle_main_instance = await insert_into_table(session , VehicleMain , vehicle_main_data)
    vehicle_uuid = vehicle_main_instance.vehicle_uuid
    
    
    if not fuel_based_costing_uuid:
        fuel_based_costing_instance = await insert_into_table(session , FuelBaseCosting , {"vehicle_category":vehicle_details['category'] , "fuel" : fuel_type, "per_km_cost" :5.0})
        # print(static_table_settings.static_table_data['FUEL_BASED_COSTING'][vehicle_details['category']])
        static_table_settings.static_table_data['FUEL_BASED_COSTING'][vehicle_details['category']] = {}
        static_table_settings.static_table_data['FUEL_BASED_COSTING'][vehicle_details['category']][fuel_type] = 5.0
        fuel_based_costing_uuid = fuel_based_costing_instance.fuel_base_costing_uuid
    
    
    vehicle_costing = VehicleCosting(
        mfo_uuid = mfo_uuid,
        fuel_based_costing_uuid = fuel_based_costing_uuid,
        vehicle_uuid = vehicle_uuid
    )
    
    mfo_vehicle_mapping = MfoVehicleMapping(
        mfo_uuid = mfo_uuid,
        vehicle_uuid = vehicle_uuid
    )
    
    
    
    session.add(vehicle_costing)
    session.add(mfo_vehicle_mapping)
    
    await create_avaronn_schedule_and_task(session , mfo_uuid , vehicle_uuid)
    
    await session.commit()
    await session.close()
    
    data_res = add_vehicle_response(
        vehicle_uuid = vehicle_uuid
        )
    return success_response(request , data_res , message = "Vehicle Added successfully")






@mfo_vehicle_management_router.put("/assignDriverToVehicle" , response_model = standard_success_response[assign_driver_to_vehicle_response])
async def assign_driver_to_vehicle(request:Request,
                                   req: assign_driver_to_vehicle_request,
                        mfo_uuid = Depends(mfo_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    already_assigned_instance = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" : req.driver_uuid , "is_enable" : True})
    if already_assigned_instance:
        raise ConflictError("Driver Already Currently assigned to another Vehicle")
    
    mapping_exists = await get_tuple_instance(session , DriverVehicleMapping , {"driver_uuid" : req.driver_uuid , "vehicle_uuid" : req.vehicle_uuid , "is_enable" : True})
    if not mapping_exists:
        drivers = ["primary_driver" , "secondary_driver" , "tertiary1_driver" , "tertiary2_driver" , "supervisor_driver"]
        mfo_veh_instance = await get_tuple_instance(session , MfoVehicleMapping , {"vehicle_uuid" : req.vehicle_uuid , "mfo_uuid" : mfo_uuid , "is_enable" : True})
        get_loc = False
        driver_role = None
        for col in drivers:
            value = getattr(mfo_veh_instance, col)
            if value == req.driver_uuid:
                break  
            if value is None:
                setattr(mfo_veh_instance , col , req.driver_uuid)
                driver_role = col
                get_loc = True
                break
        
        if not get_loc:
            i = 3
            setattr(mfo_veh_instance , drivers[i] , req.driver_uuid)
            driver_role = drivers[i]
            
        
        driver_roles_dict = static_table_settings.static_table_data['DRIVER_ROLES']
        driver_role_uuid = next((k for k , v in driver_roles_dict.items() if v == name_role_mapping[driver_role]) , None)
                
        driver_veh_mapping = await get_tuple_instance(session , DriverVehicleMapping , {'vehicle_uuid' : req.vehicle_uuid , 'driver_uuid': req.driver_uuid})
        
        
        if(driver_veh_mapping):
            driver_veh_mapping.driver_role = driver_role_uuid
        else:
            new_mapping = DriverVehicleMapping(
                vehicle_uuid = req.vehicle_uuid,
                driver_uuid = req.driver_uuid,
                driver_role = driver_role_uuid
            )
            session.add(new_mapping)
    vehicle_status_dict = static_table_settings.static_table_data["VEHICLE_STATUS"]
    idle_status_uuid = next((k for k , v in vehicle_status_dict.items() if v == "Idle") , None) 
        
    await update_table(session , VehicleMain , {'vehicle_uuid' : req.vehicle_uuid} ,  {'assigned' : True , 'driver_uuid' : req.driver_uuid , "vehicle_status" : idle_status_uuid})
    await update_table(session , MfoVehicleMapping , {'vehicle_uuid': req.vehicle_uuid , "is_enable" : True} ,{'current_assigned_driver' : req.driver_uuid})
    
    await create_attendance(session , req.driver_uuid , req.vehicle_uuid , mfo_uuid )
    await create_driver_policy(session , req.driver_uuid , mfo_uuid)
    await session.commit()
    await session.close()
    
    data_res = assign_driver_to_vehicle_response(driver_uuid=req.driver_uuid , vehicle_uuid= req.vehicle_uuid)
    return success_response(request , data_res , message = "Driver Assigned to Vehicle successfully")







@mfo_vehicle_management_router.put("/addDriverToVehicle" , response_model=standard_success_response[add_driver_to_vehicle_response])
async def addDriverToVehicle(request:Request,
                             req:add_driver_to_vehicle_request,
                        mfo_uuid = Depends(mfo_role_required()),
                        session:AsyncSession = Depends(get_async_db)
                        ):
    mfo_vehicle_mapping_update_attribute_data = {}
    drivers = ["primary_driver" , "secondary_driver" , "tertiary1_driver" , "tertiary2_driver" , "supervisor_driver"]
    
    mfo_veh_instance = await get_tuple_instance(session , MfoVehicleMapping , {"vehicle_uuid" : req.vehicle_uuid , "mfo_uuid" : mfo_uuid , "is_enable" : True})
    get_loc = False
    driver_role = None
    for col in drivers:
        value = getattr(mfo_veh_instance, col)
        if value == req.driver_uuid:
            raise ConflictError("Driver Already Added with Vehicle")  
        if value is None:
            mfo_vehicle_mapping_update_attribute_data[col] = req.driver_uuid
            driver_role = col
            get_loc = True
            break
    
    if not get_loc:
        i = 3
        mfo_vehicle_mapping_update_attribute_data[drivers[i]] = req.driver_uuid
        driver_role = drivers[i]
    
    
    if 'primary_driver' in mfo_vehicle_mapping_update_attribute_data.keys():
        already_assigned_instance = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" : req.driver_uuid , "is_enable" : True})
        if not already_assigned_instance:
            vehicle_main_instance = await get_tuple_instance(session  , VehicleMain , {'vehicle_uuid' : req.vehicle_uuid , "is_enable" : True})
            if not vehicle_main_instance.assigned:
                vehicle_status_dict = static_table_settings.static_table_data["VEHICLE_STATUS"]
                idle_status_uuid = next((k for k , v in vehicle_status_dict.items() if v == "Idle") , None) 
                vehicle_main_instance.assigned = True
                vehicle_main_instance.driver_uuid = req.driver_uuid
                vehicle_main_instance.vehicle_status = idle_status_uuid
                # await update_table(session , VehicleMain , {'vehicle_uuid' : req.vehicle_uuid} ,  {'assigned' : True , 'driver_uuid' : req.driver_uuid})
                # task_instance = await update_table(session  , Tasks , {"vehicle_uuid" : req.vehicle_uuid , "mfo_uuid" : mfo_uuid} , {"vehicle_uuid" : req.vehicle_uuid})
                mfo_vehicle_mapping_update_attribute_data['current_assigned_driver'] = mfo_vehicle_mapping_update_attribute_data['primary_driver']
                await create_attendance(session , req.driver_uuid , req.vehicle_uuid , mfo_uuid )
                await create_driver_policy(session , req.driver_uuid , mfo_uuid)
            
    
    driver_roles_dict = static_table_settings.static_table_data['DRIVER_ROLES']
    driver_role_uuid = next((k for k , v in driver_roles_dict.items() if v == name_role_mapping[driver_role]) , None)
            
    driver_veh_mapping = await get_tuple_instance(session , DriverVehicleMapping , {'vehicle_uuid' : req.vehicle_uuid , 'driver_uuid': req.driver_uuid , "is_enable" : True})
    
    
    if(driver_veh_mapping):
        driver_veh_mapping.driver_role = driver_role_uuid
    else:
        new_mapping = DriverVehicleMapping(
            vehicle_uuid = req.vehicle_uuid,
            driver_uuid = req.driver_uuid,
            driver_role = driver_role_uuid
        )
        session.add(new_mapping)
        
    await update_table(session , MfoVehicleMapping , {'vehicle_uuid': req.vehicle_uuid , "is_enable" : True} , mfo_vehicle_mapping_update_attribute_data)
    
    await session.commit()
    await session.close()
        
    data_res = add_driver_to_vehicle_response(
        data = mfo_vehicle_mapping_update_attribute_data
    )
    return success_response(request , data_res , message = "Driver Added to Vehicle successfully")
    









    

@mfo_vehicle_management_router.get("/getVehicleData" , response_model=standard_success_response[get_vehicle_data_response])
async def getVehicleData(request:Request,
                         req:get_vehicle_data_request,
                         mfo_uuid = Depends(mfo_role_required()),
                         session:AsyncSession = Depends(get_async_db),
                         session_id: str = Header(..., alias="session-id"),
                         device_id: str = Header(..., alias="device-id")
                         ):
    unique_attribute = {'vehicle_uuid' : req.vehicle_uuid , "is_enable" : True}
    attributes = None
    data_res = await fetch_from_table(session , VehicleMain , attributes , unique_attribute)
    await session.commit()
    await session.close()
    response = get_vehicle_data_response(
        data =data_res[0],
    )
    return success_response(request , response , message = "Vehicle Data Get successfully")
    


@mfo_vehicle_management_router.get("/getVehicleDocs" , response_model=standard_success_response[get_vehicle_docs_response])
async def getVehicleDocs(request:Request,
                         req:get_vehicle_docs_request,
                         mfo_uuid = Depends(mfo_role_required()),
                         session:AsyncSession = Depends(get_async_db),
                         session_id: str = Header(..., alias="session-id"),
                         device_id: str = Header(..., alias="device-id")
                         ):
    unique_attribute = {'vehicle_uuid' : req.vehicle_uuid , "is_enable" : True}
    attributes = ["fitness_certificate" , "rc" , "puc" , "permit" , "insurance_docs"]
    data_res = await fetch_from_table(session , VehicleMain , attributes , unique_attribute)
    await session.commit()
    await session.close()
    response =  get_vehicle_docs_response(**data_res[0])
    return success_response(request , response , message = "Vehicle Docs Get successfully")




@mfo_vehicle_management_router.put("/updateVehicleDocs" , response_model=standard_success_response[update_vehicle_docs_response])
async def updataVehicleDocs(request:Request,
                            vehicle_uuid:str = Form(...),
                            file_attribute:str = Form(...),
                            file :UploadFile =  File(...),
                            mfo_uuid = Depends(mfo_role_required()),
                            session:AsyncSession = Depends(get_async_db),
                            session_id: str = Header(..., alias="session-id"),
                            device_id: str = Header(..., alias="device-id")
                        ):
    dt = datetime.now(timezone.utc).replace(tzinfo=None).strftime("%Y-%m-%d_%H-%M-%S")
    UPLOAD_FOLDER_DRIVER = f"vehicle/{vehicle_uuid}"

    file_extension = file.filename.split('.')[-1].lower()
    file_path = f"{UPLOAD_FOLDER_DRIVER}/{file_attribute}_{dt}.{file_extension}"
    path_to_s3 = await upload_file_to_s3(file , file_path)  
    unique_attribute = {"vehicle_uuid" : vehicle_uuid , "is_enable" : True}
    update_attribute = {
        file_attribute : path_to_s3,
        }
    
    
    await update_table(session , VehicleMain , unique_attribute , update_attribute)
    await session.commit()
    await session.close()
    response =  update_vehicle_docs_response(
        file_path = path_to_s3
    )
    return success_response(request , response , message = "Vehicle Docs updated successfully")



    
    
@mfo_vehicle_management_router.get("/getVehicleAssignedData", response_model=standard_success_response[get_vehicle_assigned_data_response])
async def getVehicleAssignedData(request:Request,
                                 req: get_vehicle_assigned_data_request,
                                 mfo_uuid = Depends(mfo_role_required()),
                                 session:AsyncSession = Depends(get_async_db),
                                 session_id: str = Header(..., alias="session-id"),
                                 device_id: str = Header(..., alias="device-id")
                                 ):
    vehicle_status_dict = static_table_settings.static_table_data['VEHICLE_STATUS']
    vehicle_main_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : req.vehicle_uuid , "is_enable" : True})
    vehicle_header = vehicle_assigned_header(
        id = vehicle_main_instance.id,
        vehicle_uuid = req.vehicle_uuid,
        vehicle_number = vehicle_main_instance.vehicle_number , 
        vehicle_model = vehicle_main_instance.vehicle_model,
        vehilce_status = vehicle_status_dict[vehicle_main_instance.vehicle_status],
        vehilce_driver_current_status = ""
    )
    assigned_driver =  None
    other_mapped_driver = []
    assigned_driver_uuid = None
    
    mfo_vehicle_mapping_instance = await get_tuple_instance(session , MfoVehicleMapping , {"mfo_uuid" : mfo_uuid , "vehicle_uuid" : req.vehicle_uuid , "is_enable" : True})
    driver_roles_columns = ["primary_driver" , "secondary_driver" , "tertiary1_driver" , "tertiary2_driver" , "supervisor_driver"]
    if mfo_vehicle_mapping_instance.current_assigned_driver:
        driver_role = "Undefined"
        for role in driver_roles_columns:
            value = getattr(mfo_vehicle_mapping_instance , role)
            if value == mfo_vehicle_mapping_instance.current_assigned_driver:
                driver_role = role
                break
            
        
        driver_main_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" :mfo_vehicle_mapping_instance.current_assigned_driver , "is_enable" : True})
        
        
        attendance_states_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
        attendance_status = "On Leave"
        
        attendance_instance = await get_tuple_instance(
                            session,
                            DriverAttendance,
                            {'driver_uuid': driver_main_instance.driver_uuid},
                            extra_conditions=[
                                func.DATE(convert_utc_to_ist(DriverAttendance.attendance_trigger_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
                            ],
                            order_by=[desc(DriverAttendance.id)],
                            limit=1  
                        )
        if attendance_instance:
            attendance_status = attendance_states_dict[attendance_instance.attendance_state_uuid]
        
        assigned_driver = vehicle_assigned_driver(
            id = driver_main_instance.id,
            driver_uuid = driver_main_instance.driver_uuid,
            driver_name = driver_main_instance.name,
            driver_role = driver_role,
            driver_profile_image = driver_main_instance.profile_image,
            driver_country_code = driver_main_instance.country_code,
            driver_phone_number = driver_main_instance.phone_number,
            driver_attendance_status = attendance_status,
            driver_verification_status = driver_main_instance.verification_status,
        )
        assigned_driver_uuid = driver_main_instance.driver_uuid
    
    for column in driver_roles_columns:
        value = getattr(mfo_vehicle_mapping_instance, column, None)
        if value and value != assigned_driver_uuid:
            driver_main_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : value , "is_enable" : True})
            can_be_assigned = False
            mapping_instance = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" : value , "is_enable" : True})
            if not mapping_instance:
                driver_leave_instance = await get_tuple_instance(session , DriverApprovedLeaves , {"driver_uuid" : value , "leave_date" : get_utc_time().date()})
                if not driver_leave_instance:
                    can_be_assigned = True
                
            other_mapped_driver.append(vehicle_mapped_driver(
                id = driver_main_instance.id,
                driver_uuid = driver_main_instance.driver_uuid,
                driver_name = driver_main_instance.name,
                driver_role = column,
                driver_profile_image = driver_main_instance.profile_image,
                driver_can_be_assigned = can_be_assigned,
                driver_verification_status = driver_main_instance.verification_status
                
            ))
        
        
        
    today = get_utc_time()
    current_year = today.year
    current_month = today.month

    start_date = datetime(current_year, current_month, 1, 0, 0, 0)

    last_day = calendar.monthrange(current_year, current_month)[1]
    end_date = datetime(current_year, current_month, last_day, 23, 59, 59)

    query= select(
                func.COALESCE(func.SUM(PettyExpenses.expense), 0).label("petty_expense"),
            ).where(
                PettyExpenses.vehicle_uuid == req.vehicle_uuid,
                PettyExpenses.mfo_uuid == mfo_uuid,
                PettyExpenses.is_enable == True,
                and_(
                    func.DATE(PettyExpenses.expense_date) >= start_date,
                    func.DATE(PettyExpenses.expense_date) <= end_date
                    
                )
            )

    result = await session.execute(query)
    summed_values = result.fetchone()
            
            
    vehicle_petty_expense = summed_values.petty_expense
    vehicle_costing_instance = await get_tuple_instance(session , VehicleCosting , {"vehicle_uuid" : req.vehicle_uuid ,  "is_enable":True})
    cost = (vehicle_costing_instance.vehicle_emi +  vehicle_costing_instance.parking_cost + vehicle_costing_instance.maintenance)
    driver_salary = 0.0
    if vehicle_main_instance.driver_uuid:
        mapping_instance = await get_tuple_instance(session , DriverMfoMapping , {"mfo_uuid" : mfo_uuid , "driver_uuid" : vehicle_main_instance.driver_uuid , "is_enable" : True})
        driver_salary = mapping_instance.driver_salary
    cost += driver_salary
    cost_summary = vehicle_cost_summary(
        monthly_vehicle_cost = cost,
        monthly_vehicle_utilization = "Active Trip days = 23/30 days",
        monthly_petty_expense = vehicle_petty_expense
    )


    today = get_utc_time()
    first_day_of_month = today.replace(day=1).date() 
    last_day_of_month = ((today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)).date()

    query_monthly= select(
        func.COALESCE(func.SUM(VehicleUtilization.total_distance_km), 0).label("total_distance_km"),
            func.COALESCE(func.SUM(VehicleUtilization.total_hours), 0).label("total_hours"),
            func.COUNT(VehicleUtilization.onspot_hours).label("onspot_hours"),
            func.COALESCE(func.SUM(VehicleUtilization.schedule_hours), 0).label("schedule_hours"),
            func.COALESCE(func.SUM(VehicleUtilization.ideal_kms), 0).label("ideal_kms"),
            func.COUNT(VehicleUtilization.order_kms).label("order_kms")
    ).where(
        VehicleUtilization.vehicle_uuid == req.vehicle_uuid,
        and_(
            func.DATE(VehicleUtilization.date) >= first_day_of_month,
            func.DATE(VehicleUtilization.date) <= last_day_of_month
        )
    )
    
    result_monthly = await session.execute(query_monthly)
    summed_values_monthly = result_monthly.fetchone()
    
    result_yesterday = await session.execute(query_monthly)
    summed_values_yesterday= result_yesterday.fetchone()
    

    time_status_monthly = vehicle_time_utilization(
        total_time_hr = summed_values_monthly.total_hours,
        idle_time_hr = summed_values_monthly.total_hours - summed_values_monthly.onspot_hours,
        earning_time = summed_values_monthly.onspot_hours
    )
    distance_status_monthly = vehicle_distance_utilization(
        total_distance_km = summed_values_monthly.total_distance_km,
        idle_distance_km = summed_values_monthly.ideal_kms,
        earning_distance_km = summed_values_monthly.order_kms
    )
    
    time_status_today= vehicle_time_utilization(
        total_time_hr = summed_values_yesterday.total_hours,
        idle_time_hr = summed_values_yesterday.total_hours - summed_values_yesterday.onspot_hours,
        earning_time = summed_values_yesterday.onspot_hours
    )
    distance_status_today = vehicle_distance_utilization(
        total_distance_km = summed_values_yesterday.total_distance_km,
        idle_distance_km = summed_values_yesterday.ideal_kms,
        earning_distance_km = summed_values_yesterday.onspot_hours
    )
    
    veh_performance = vehicle_performance(
        time_utilization_monthly = time_status_monthly,
        distance_utilization_monthly =  distance_status_monthly,
        time_utilization_today = time_status_today,
        distance_utilization_today = distance_status_today
    )
    

    liveLocation =  None
    
    vehicle_location_instance = await get_tuple_instance(session , VehicleLocation , {"vehicle_number" :vehicle_main_instance.vehicle_number } , order_by=[desc(VehicleLocation.id)] , limit = 1)
    if vehicle_location_instance:
            liveLocation = {
                'latitude' : vehicle_location_instance.lat,
                'longitude' : vehicle_location_instance.lng,
                "location_name" : await get_location_name(vehicle_location_instance.lat , vehicle_location_instance.lng),
                "updated_at" :  convert_utc_to_ist(vehicle_location_instance.created_at)
            }
    
    live_location = vehicle_live_location(**liveLocation) if liveLocation else None
    
    
    can_data_isntance = await get_tuple_instance(session , CANData , {"vehicle_number" : vehicle_main_instance.vehicle_number} , order_by=[desc(CANData.id)] , limit = 1)
    
    vehicle_soc_and_speed= None
    if can_data_isntance:
        vehicle_soc_and_speed = get_vehicle_assigned_data_soc_and_speed(
            vehicle_current_soc_percentage = can_data_isntance.soc_value,
            vehicle_km_left = round(((can_data_isntance.soc_value/100.0) * 7.7)*9.09 , 2),
            vehicle_speed_kmph = can_data_isntance.vehicle_speed_value
        )
        
    
    await session.commit()
    await session.close()
    response = get_vehicle_assigned_data_response(
        vehicle_assigned_header = vehicle_header,
        assigned_driver =  assigned_driver,
        other_mapped_driver = other_mapped_driver,
        vehicle_soc_and_speed = vehicle_soc_and_speed,
        vehicle_cost_summary = cost_summary,
        vehicle_performance = veh_performance,
        vehicle_live_location = live_location
    )
    return success_response(request , response , message = "Vehicle Assigned Data Get successfully" , round_data=False)








@mfo_vehicle_management_router.get("/getUnassignedDriverList", response_model=standard_success_response[get_unassigned_vehicle_data_response])
async def getUnassignedDriverList(request:Request,
                                 req: get_unassigned_vehicle_data_request,
                                 mfo_uuid = Depends(mfo_role_required()),
                                 session:AsyncSession = Depends(get_async_db),
                                 session_id: str = Header(..., alias="session-id"),
                                 device_id: str = Header(..., alias="device-id")
                                 ):
    
    mapped_driver = []
    other_available_driver = []
    assigned_driver = None
    assigned_driver_uuid = None
   
    mapped_driver_list = []
    mfo_vehicle_mapping_instance = await get_tuple_instance(session , MfoVehicleMapping , {"mfo_uuid" : mfo_uuid , "vehicle_uuid" : req.vehicle_uuid , "is_enable" : True})
    
    if mfo_vehicle_mapping_instance.current_assigned_driver:
        assigned_driver_uuid = mfo_vehicle_mapping_instance.current_assigned_driver
        driver_main_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : mfo_vehicle_mapping_instance.current_assigned_driver , "is_enable" : True})
        
        attendance_states_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
        attendance_status = "On Leave"
        
        attendance_instance = await get_tuple_instance(
                            session,
                            DriverAttendance,
                            {'driver_uuid': driver_main_instance.driver_uuid},
                            extra_conditions=[
                                func.DATE(convert_utc_to_ist(DriverAttendance.attendance_trigger_time)) == func.DATE(convert_utc_to_ist(get_utc_time()))
                            ],
                            order_by=[desc(DriverAttendance.id)],
                            limit=1  
                        )
        if attendance_instance:
            attendance_status = attendance_states_dict[attendance_instance.attendance_state_uuid]
            
        
        driver_roles_columns = ["primary_driver" , "secondary_driver" , "tertiary1_driver" , "tertiary2_driver" , "supervisor_driver"]
        driver_role = "Undefined"
        for role in driver_roles_columns:
            value = getattr(mfo_vehicle_mapping_instance , role)
            if value == mfo_vehicle_mapping_instance.current_assigned_driver:
                driver_role = role
                break
            
        assigned_driver = vehicle_assigned_driver(
                id = driver_main_instance.id,
                driver_uuid = driver_main_instance.driver_uuid,
                driver_name = driver_main_instance.name,
                driver_role = driver_role,
                driver_profile_image = driver_main_instance.profile_image,
                driver_country_code = driver_main_instance.country_code,
                driver_phone_number = driver_main_instance.phone_number,
                driver_attendance_status = attendance_status,
                driver_verification_status = driver_main_instance.verification_status
        )
        
    driver_roles_columns = ["primary_driver" , "secondary_driver" , "tertiary1_driver" , "tertiary2_driver" , "supervisor_driver"]
    for column in driver_roles_columns:
        value = getattr(mfo_vehicle_mapping_instance, column, None)
        mapped_driver_list.append(value)
        if value and value != assigned_driver_uuid:
            driver_main_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : value})
            mapped_driver.append(mapped_driver_data(
                id = driver_main_instance.id,
                driver_uuid = driver_main_instance.driver_uuid,
                driver_name = driver_main_instance.name,
                driver_role = column,
                driver_profile_image = driver_main_instance.profile_image,
                driver_can_be_assigned = True,
                driver_verification_status = driver_main_instance.verification_status
            ))
            
    other_driver_of_mfo = await fetch_from_table(session , DriverMfoMapping ,["driver_uuid"], {"mfo_uuid" : mfo_uuid , "is_enable" : True})
    for dri in other_driver_of_mfo:
        if dri["driver_uuid"] not in  mapped_driver_list:
            mapping_instance = await get_tuple_instance(session , MfoVehicleMapping , {"current_assigned_driver" : dri["driver_uuid"] ,"is_enable" : True})
            if not mapping_instance:
                driver_leave_instance = await get_tuple_instance(session ,
                                                                 DriverApprovedLeaves ,
                                                                 {"driver_uuid" : dri["driver_uuid"] , "leave_date" : get_utc_time().date()},
                                                                 order_by = [desc(DriverApprovedLeaves.id)],
                                                                 limit = 1
                                                                 )
                if not driver_leave_instance:
                    drive_main_instance= await get_tuple_instance(session , DriverMain , {"driver_uuid" : dri["driver_uuid"] , "is_enable" : True})
                    other_available_driver.append(
                        other_available_driver_data(
                        id = drive_main_instance.id,
                        driver_uuid = drive_main_instance.driver_uuid,
                        driver_name = drive_main_instance.name,
                        driver_profile_image = drive_main_instance.profile_image,
                        driver_verification_status = drive_main_instance.verification_status
                        )
                    )
    response = get_unassigned_vehicle_data_response(
        assigned_driver = assigned_driver,
        mapped_drivers = mapped_driver,
        other_available_drivers = other_available_driver
    )

    return success_response(request , response , message = "Vehicle Assigned Data Get successfully" , round_data=False)

        
        
        

@mfo_vehicle_management_router.get("/getAllVehicles" , response_model= standard_success_response[get_all_vehicle_data_response])
async def getAllVehicles(request:Request,
                         mfo_uuid = Depends(mfo_role_required()),
                         session:AsyncSession = Depends(get_async_db),
                         session_id: str = Header(..., alias="session-id"),
                         device_id: str = Header(..., alias="device-id")
                         ):
    assigned_vehicle_list = []
    unassigned_vehicle_list = []
    
    vehicle_main_unique_attribute = {"mfo_uuid" : mfo_uuid , "is_enable" : True}
    vehicle_attributes = ['id' , 'vehicle_number' , 'vehicle_uuid' , 'vehicle_status' , 'assigned' , 'driver_uuid'  , 'fuel_type' ]
    data_res = await fetch_from_table(session , VehicleMain , vehicle_attributes , vehicle_main_unique_attribute)
    if data_res:
        
        fuel_types_dict = static_table_settings.static_table_data.get('FUEL_TYPES')
        vehicle_status_dict = static_table_settings.static_table_data.get('VEHICLE_STATUS' , "IDLE")
        
        for data in data_res:
            data['vehicle_status'] = vehicle_status_dict[data['vehicle_status']]
            data['fuel_type'] = fuel_types_dict.get(data.get('fuel_type', None) , None)
            vehicle_tag = await get_vehicle_tag(session , data["vehicle_uuid"])

            if data['assigned']:
                driver_instance = await get_tuple_instance(session , DriverMain , {'driver_uuid' : data['driver_uuid'] , "is_enable" : True})

                data['role'] = "Main driver"
                data['driver_name'] = driver_instance.name
                data['driver_profile_image'] = driver_instance.profile_image
                vehicle_current_activity = await get_vehile_activity(session , data["vehicle_uuid"])
                # await get_vehicle_current_activity(session , data["vehicle_status"] , data["vehicle_uuid"] , data["driver_uuid"])
                assigned_vehicle_list.append(assigned_vehicles(
                    id = data["id"],
                    vehicle_number = data["vehicle_number"],
                    vehicle_uuid = data["vehicle_uuid"],
                    vehicle_fuel_type = data["fuel_type"],
                    vehicle_status = data["vehicle_status"],
                    driver_uuid = data["driver_uuid"],
                    driver_name = driver_instance.name,
                    driver_profile_image = driver_instance.profile_image,
                    driver_country_code = driver_instance.country_code,
                    driver_phone_number = driver_instance.phone_number,
                    driver_verification_status = driver_instance.verification_status, 
                    driver_role = data["role"],
                    vehicle_other_drivers_number = vehicle_tag[0],
                    vehicle_current_activity = vehicle_current_activity
                ))
            
            else:
                unassigned_vehicle_list.append(unassigned_vehicles(
                    id = data["id"],
                    vehicle_number = data["vehicle_number"],
                    vehicle_uuid = data["vehicle_uuid"],
                    vehicle_tag = vehicle_tag[1]
                ))
        
            
            
    await session.commit()
    await session.close()
    response =  get_all_vehicle_data_response(
        unassigned_vehicles = unassigned_vehicle_list,
        assigned_vehicles = assigned_vehicle_list
    )
    return success_response(request , response , message = "All Vehicles Get successfully")








@mfo_vehicle_management_router.get("/getVehicleCosting" , response_model=standard_success_response[get_vehicle_costing_response])
async def getVehicleCosting(request:Request,
                            req:get_vehicle_costing_request,
                            mfo_uuid = Depends(mfo_role_required()),
                            session:AsyncSession = Depends(get_async_db),
                            session_id: str = Header(..., alias="session-id"),
                            device_id: str = Header(..., alias="device-id") 
                            ):
    unique_attribute = {'vehicle_uuid' : req.vehicle_uuid ,  "is_enable":True}
    costing_isntance = await get_tuple_instance(session , VehicleCosting , unique_attribute)
    data_res = {}
    driver_salary = 0.0
    vehicle_instance = await get_tuple_instance(session , VehicleMain ,{"vehicle_uuid" : req.vehicle_uuid})
    if vehicle_instance.driver_uuid:
        mapping_instance = await get_tuple_instance(session , DriverMfoMapping , {"mfo_uuid" : mfo_uuid , "driver_uuid" : vehicle_instance.driver_uuid , "is_enable" : True})
        driver_salary = mapping_instance.driver_salary
    if costing_isntance:
        data_res['vehicle_emi'] = round(costing_isntance.vehicle_emi , 2)
        data_res['parking_cost'] = round(costing_isntance.parking_cost , 2)
        data_res['driver_salary'] = round(driver_salary , 2)
        data_res['maintenance'] = round(costing_isntance.maintenance , 2)
        
    await session.commit()
    await session.close()
    response =  get_vehicle_costing_response(**data_res)
    return success_response(request , response , message = "Vehicles Costing Get successfully")
    




@mfo_vehicle_management_router.put("/updateVehicleCosting" , response_model = standard_success_response[update_vehicle_costing_response])
async def updateVehicleCosting(request:Request,
                                   req: update_vehicle_costing_request,
                                   mfo_uuid = Depends(mfo_role_required()),
                                   session:AsyncSession = Depends(get_async_db),
                                   session_id: str = Header(..., alias="session-id"),
                                   device_id: str = Header(..., alias="device-id")
                                   ):
    
    unique_attribute = {"vehicle_uuid": req.vehicle_uuid ,  "is_enable":True}
    costing_instance = await get_tuple_instance(session, VehicleCosting, unique_attribute)

    if costing_instance:
        attributes = req.model_dump(exclude_unset=True)
        # await mfo_db_logger(
        #     session,
        #     payload["uuid"],
        #     VehicleCosting.__tablename__,
        #     "vehicle_uuid",
        #     req.vehicle_uuid,
        #     list(attributes.keys()),
        #     [getattr(costing_instance, attr) for attr in attributes.keys()],
        #     list(attributes.values()),
        #     session_id,
        #     device_id
        # )
        costing_instance.is_enable = False
        costing_instance.disabled_at = get_utc_time()
        
        vehicle_costing_data = {
            "vehicle_uuid": costing_instance.vehicle_uuid,
            "mfo_uuid" : costing_instance.mfo_uuid,
            "vehicle_emi" : req.vehicle_emi if isinstance(req.vehicle_emi , float) or isinstance(req.vehicle_emi , int) else costing_instance.vehicle_emi,
            "parking_cost" : req.parking_cost if  isinstance(req.parking_cost , float) or isinstance(req.parking_cost , int) else costing_instance.parking_cost,
            "maintenance" : req.maintenance if  isinstance(req.maintenance , float) or isinstance(req.maintenance , int) else costing_instance.maintenance,
            "fuel_based_costing_uuid" : costing_instance.fuel_based_costing_uuid
        }
        await insert_into_table(session , VehicleCosting , vehicle_costing_data)

        await session.commit()
        await session.close()
    else:
        await session.close()
        raise NotFoundError("No vehicle found")

    response = update_vehicle_costing_response(updated = True )
    return success_response(request , response , message = "Vehicles Costing updated successfully")





@mfo_vehicle_management_router.put("/unassigneDriverFromVehicle" , response_model = standard_success_response[unassign_driver_from_vehicle_response])
async def unassigneDriverFromVehicle(request:Request,
                                   req: unassign_driver_from_vehicle_request,
                                   mfo_uuid = Depends(mfo_role_required()),
                                   session:AsyncSession = Depends(get_async_db),
                                   session_id: str = Header(..., alias="session-id"),
                                   device_id: str = Header(..., alias="device-id")
                                   ):
    
    vehicle_status_dict = static_table_settings.static_table_data["VEHICLE_STATUS"]
    inactive_status_uuid = next((k for k , v in vehicle_status_dict.items() if v == "Inactive") , None) 
    unique_attribute = {"vehicle_uuid": req.vehicle_uuid , "driver_uuid" : req.driver_uuid , "is_enable" : True}
    vehicle_main_instance = await get_tuple_instance(session , VehicleMain, unique_attribute)
    if vehicle_main_instance:
        vehicle_main_instance.assigned = False
        vehicle_main_instance.driver_uuid = None
        vehicle_main_instance.vehicle_status = inactive_status_uuid
    
    mfo_vehicle_mapping_instance = await get_tuple_instance(session , MfoVehicleMapping , {"vehicle_uuid": req.vehicle_uuid , "current_assigned_driver" : req.driver_uuid , "is_enable" : True})
    
    if mfo_vehicle_mapping_instance:
        mfo_vehicle_mapping_instance.is_enable = False
        mfo_vehicle_mapping_instance.disabled_at = get_utc_time()
        
    new_mapping_data = {
        
        "vehicle_uuid" : mfo_vehicle_mapping_instance.vehicle_uuid,
        "mfo_uuid" : mfo_vehicle_mapping_instance.mfo_uuid,
        
        "primary_driver" : mfo_vehicle_mapping_instance.primary_driver,
        "secondary_driver" : mfo_vehicle_mapping_instance.secondary_driver,
        "tertiary1_driver" : mfo_vehicle_mapping_instance.tertiary1_driver,
        "tertiary2_driver" : mfo_vehicle_mapping_instance.tertiary2_driver,
        "supervisor_driver" : mfo_vehicle_mapping_instance.supervisor_driver
    }
        
    await insert_into_table(session , MfoVehicleMapping ,new_mapping_data)

    driver_working_policy_instance = await get_tuple_instance(session , 
                                                              DriverWorkingPolicy ,
                                                              {"driver_uuid" : req.driver_uuid , "mfo_uuid" : mfo_uuid} , 
                                                              order_by = [desc(DriverWorkingPolicy.id)],
                                                              limit =1
                                                              )
    driver_working_policy_instance.valid_till = get_utc_time()
    await session.commit()
    await session.close()

    return success_response(request , unassign_driver_from_vehicle_response(sucess_status=True) , message = "Driver unassigned successfully")




@mfo_vehicle_management_router.put("/removeDriverFromVehicle" , response_model = standard_success_response[remove_driver_from_vehicle_response])
async def removeDriverFromVehicle(request:Request,
                                   req: remove_driver_from_vehicle_request,
                                   mfo_uuid = Depends(mfo_role_required()),
                                   session:AsyncSession = Depends(get_async_db),
                                   session_id: str = Header(..., alias="session-id"),
                                   device_id: str = Header(..., alias="device-id")
                                   ):
    
    unique_attribute = {"vehicle_uuid": req.vehicle_uuid , "driver_uuid" : req.driver_uuid , "is_enable" : True}
    vehicle_main_instance = await get_tuple_instance(session , VehicleMain, unique_attribute)
    if vehicle_main_instance:
        vehicle_main_instance.assigned = False
        vehicle_main_instance.driver_uuid = None
    
    mfo_vehicle_mapping_instance = await get_tuple_instance(session , MfoVehicleMapping , {"vehicle_uuid": req.vehicle_uuid , "mfo_uuid" : mfo_uuid , "is_enable" : True})
    if mfo_vehicle_mapping_instance:
        mfo_vehicle_mapping_instance.is_enable = False
        mfo_vehicle_mapping_instance.disabled_at = get_utc_time()
         
        driver_roles_columns = ["current_assigned_driver" ,"primary_driver" , "secondary_driver" , "tertiary1_driver" , "tertiary2_driver" , "supervisor_driver"]
        new_mapping_data = {
            "vehicle_uuid" : mfo_vehicle_mapping_instance.vehicle_uuid,
            "mfo_uuid" : mfo_vehicle_mapping_instance.mfo_uuid
        }
        
        for column in driver_roles_columns:
            value = getattr(mfo_vehicle_mapping_instance, column, None)
            if value != req.driver_uuid:
                new_mapping_data[column] = value
                
        await insert_into_table(session , MfoVehicleMapping ,new_mapping_data)  
         
    mapping_instance = await get_tuple_instance(session , DriverVehicleMapping , {"driver_uuid" : req.driver_uuid , "vehicle_uuid" : req.vehicle_uuid , "is_enable" : True})
    if mapping_instance:
        mapping_instance.is_enable = False
        mapping_instance.disabled_at = get_utc_time()
                


    await session.commit()
    await session.close()
    
    return success_response(request , remove_driver_from_vehicle_response(success_status=True) , message = "Driver removed from vehicle successfully")






@mfo_vehicle_management_router.put("/removeVehicle" , response_model = standard_success_response[remove_vehicle_response])
async def removeVehicle(request:Request,
                        req: remove_vehicle_request,
                        mfo_uuid = Depends(mfo_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    
    vehicle_instance = await get_tuple_instance(session  , VehicleMain , {"vehicle_uuid" : req.vehicle_uuid , "mfo_uuid" : mfo_uuid , "is_enable" : True})
    
    if vehicle_instance:
        vehicle_instance.is_enable = False
        vehicle_instance.disabled_at = get_utc_time()
        
    mfo_vehicle_mapping = await get_tuple_instance(session , MfoVehicleMapping , {"vehicle_uuid" : req.vehicle_uuid , "mfo_uuid" : mfo_uuid , "is_enable" : True})
    if mfo_vehicle_mapping:
        mfo_vehicle_mapping.is_enable = False
        mfo_vehicle_mapping.disabled_at = get_utc_time()
        
        
    driver_vehicle_mapping = await fetch_from_table(session , DriverVehicleMapping ,["driver_uuid"], {"vehicle_uuid" : req.vehicle_uuid , "is_enable" : True})
    
    for dri in driver_vehicle_mapping:
        mapping_instance = await get_tuple_instance(session , DriverVehicleMapping , {"vehicle_uuid" : req.vehicle_uuid , "driver_uuid" : dri["driver_uuid"] , "is_enable":True})
        if mapping_instance:
            mapping_instance.is_enable = False
            mapping_instance.disabled_at = get_utc_time()
            
    await session.commit()
    await session.close()
    return success_response(request ,remove_vehicle_response(success_status=True) ,"Vehicle removed successfully")
