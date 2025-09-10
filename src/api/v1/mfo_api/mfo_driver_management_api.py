import calendar
from fastapi import APIRouter ,  Depends, Header, Request
from datetime import datetime, timedelta, time
from sqlalchemy import  and_, desc, func, select
from auth.dependencies import mfo_role_required
from auth.otp_service import send_otp, verify_otp
from config.exceptions import NotFoundError
from db.database_operations import fetch_from_table, get_tuple_instance, insert_into_table
from helpers.mfo_helpers.mfo_driver_helper import get_driver_status_and_current_activity
from integrations.location_service import get_location_name
from models.assignment_mapping_models import DriverFutureArrangement, DriverMfoMapping, DriverVehicleMapping, MfoVehicleMapping
from models.attendace_models import DriverAttendance, DriverAttendanceSummary
from models.costing_models import VehicleCosting
from models.driver_models import  DriverLocation, DriverMain
from models.petty_expense_models import PettyExpenses
from models.task_management_models import Schedules, TaskScheduleMapping, Tasks
from fastapi import HTTPException , status
from schemas.v1.standard_schema import standard_success_response
from schemas.v1.mfo_schemas.mfo_driver_management_schema import (
    assign_driver_for_future_request, assign_driver_for_future_response, assigned_driver, assigned_vehicle, driver_distance_utilization, driver_time_utilization, get_all_drivers_response, get_driver_docs_request, get_driver_docs_response, get_driver_profile_app_bar, get_driver_profile_assigned_vehicle, get_driver_profile_driver_attendance_summary, get_driver_profile_driver_card, get_driver_profile_driver_incentive_programme_summary, get_driver_profile_driver_location, get_driver_profile_driver_performance, get_driver_profile_driver_sla_policy, get_driver_profile_driver_work_summary_and_policy, get_driver_profile_monthly_salary_and_expense, get_driver_profile_other_mapped_vehicle, get_driver_profile_request, get_driver_profile_response, get_unassigned_driver_data_request, get_unassigned_driver_data_response, mapped_vehicle, other_available_vehicle, register_or_add_driver_request,
    register_or_add_driver_response, remove_driver_request, remove_driver_response, unassigned_driver, update_driver_salary_request, update_driver_salary_response, verify_and_add_driver_request, 
    verify_and_add_driver_response
)
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db
from models.vehicle_models import VehicleMain
from settings.static_data_settings import static_table_settings
from utils.driver_activity_rule_engine import get_driver_activity
from utils.response import success_response
from utils.time_utils import  convert_utc_to_ist, get_utc_time






mfo_driver_management_router = APIRouter()




name_role_mapping = {
        'primary_driver' : "Primary",
        "secondary_driver" : "Secondary",
        "tertiary1_driver" : "Tertiary1",
        "tertiary2_driver" : "Tertiary2",
        "supervisor_driver" : "Supervisor"
    }












@mfo_driver_management_router.post("/registerOrAddDriver" , response_model= standard_success_response[register_or_add_driver_response], status_code=200)
async def register_or_add_driver(request:Request,
                                 req: register_or_add_driver_request ,
                                mfo_uuid = Depends(mfo_role_required()),
                                session_id: str = Header(..., alias="session-id"),
                                device_id: str = Header(..., alias="device-id")
                        ):
    res =  await send_otp(req.country_code , req.driver_phone_number)
    data_res = register_or_add_driver_response(request_id = res)
    
    return success_response(request , data_res , message = "Otp sended to Driver successfully")
    







@mfo_driver_management_router.post("/verifyAndAddDriver" , response_model = standard_success_response[verify_and_add_driver_response], status_code=201)
async def verify_and_add_driver(request:Request,
                                req: verify_and_add_driver_request,
                                mfo_uuid= Depends(mfo_role_required()),
                                session:AsyncSession = Depends(get_async_db),
                                session_id: str = Header(..., alias="session-id"),
                                device_id: str = Header(..., alias="device-id")
                                ):
    await verify_otp(req.otp , req.request_id)
    final_response = {
        "driver_uuid" : None,
        "driver_name" : None,
        "driver_profile_image" : None,
        "driver_verification_status" : None
    }
    name_role_mapping = {
        'primary_driver' : "Primary",
        "secondary_driver" : "Secondary",
        "tertiary1_driver" : "Tertiary1",
        "tertiary2_driver" : "Tertiary2",
        "supervisor_driver" : "Supervisor"
    }
    async with session.begin():
        driver_instance = await get_tuple_instance(session , DriverMain , {'phone_number' : req.driver_phone_number , "is_enable" : True})
        if driver_instance:
            driver_uuid = driver_instance.driver_uuid
            final_response['driver_uuid'] = driver_uuid
            final_response['driver_name'] = driver_instance.name
            final_response['driver_profile_image'] = driver_instance.profile_image
            final_response['driver_verification_status'] = driver_instance.verification_status
        else: 
            driver_data = {
                    'country_code'  :  req.country_code,
                    'phone_number' : req.driver_phone_number,
                    'name' :  req.driver_name
            }
            driver_instance = await insert_into_table(session , DriverMain , driver_data)
            driver_uuid = driver_instance.driver_uuid
            final_response['driver_uuid'] = driver_uuid
            final_response['driver_name'] = driver_instance.name
            final_response['driver_profile_image'] = driver_instance.profile_image
            final_response['driver_verification_status'] = driver_instance.verification_status
            
        mapping_exist = await get_tuple_instance(session , DriverMfoMapping , {'driver_uuid': driver_uuid ,'mfo_uuid': mfo_uuid , "is_enable" : True})
        if mapping_exist:
            raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = f"Driver already exists with you as Driver uuid =  {driver_uuid}"
            )
        else:
            mapping_data = {
                'driver_uuid': driver_uuid,
                'mfo_uuid' : mfo_uuid
            }
            mapping_instance = await insert_into_table(session , DriverMfoMapping , mapping_data)
        
        mfo_vehilce_mapping_data = {}
        if req.vehicle_uuid:
            mfo_vehicle_instance = await get_tuple_instance(session , MfoVehicleMapping , {'vehicle_uuid' : req.vehicle_uuid})
            get_loc = False
            driver_role = None
            drivers = ["primary_driver" , "secondary_driver" , "tertiary1_driver" , "tertiary2_driver" , "supervisor_driver"]
            for col in drivers:
                value = getattr(mfo_vehicle_instance, col)  
                if value is None:
                    mfo_vehilce_mapping_data[col] = driver_uuid
                    driver_role = col
                    get_loc = True
                    break
            
            if not get_loc:
                i = 3
                mfo_vehilce_mapping_data[drivers[i]] = driver_uuid
                driver_role = drivers[i]
            
            
            
            
            
            driver_roles_dict = static_table_settings.static_table_data['DRIVER_ROLES']
            driver_role_uuid = next((k for k , v in driver_roles_dict.items() if v == name_role_mapping[driver_role]))
            
            vehicle_driver_mapping_data = DriverVehicleMapping(
                driver_uuid = driver_uuid,
                vehicle_uuid = req.vehicle_uuid,
                driver_role = driver_role_uuid
            )
            session.add(vehicle_driver_mapping_data)
            
            
            if driver_role == 'primary_driver':
                mfo_vehilce_mapping_data['current_assigned_driver'] = driver_uuid
                task_instance = await get_tuple_instance(session , Tasks ,{"vehicle_uuid" : req.vehicle_uuid , "mfo_uuid" : mfo_uuid})
                task_instance.driver_uuid = driver_uuid
                query = select(
                Schedules.schedule_start_time
                ).join(
                    TaskScheduleMapping , Schedules.schedule_uuid == TaskScheduleMapping.schedule_uuid
                ).where(
                    TaskScheduleMapping.task_uuid == task_instance.task_uuid
                )
                result = await session.execute(query)
                schedule_start_time = result.scalar()
                current_date = get_utc_time().date()
                attendance_trigger_time = datetime.combine(current_date, schedule_start_time) - timedelta(hours = 2)
                attendance_states_dict = static_table_settings.static_table_data['ATTENDANCE_STATES']
                driver_vehicle_connected_time_state_dict = static_table_settings.static_table_data['DRIVER_VEHICLE_CONNECTED_TIME_STATES']
                
                no_action_attendance_status_uuid = next((k for k,v in attendance_states_dict.items() if v == "No action") , None)
                no_action_driver_attendance_vehicle_connected_time_state_uuid = next((k for k , v in driver_vehicle_connected_time_state_dict.items() if v == "No action") , None)
                
                
                attendence_data = {
                'driver_uuid' : driver_uuid,
                'vehicle_uuid' : req.vehicle_uuid,
                'mfo_uuid' : mfo_uuid,
                "attendance_state_uuid" : no_action_attendance_status_uuid,
                "attendance_trigger_time" : attendance_trigger_time,
                "expected_time_stamp" : time(0, 30, 0),
                "driver_attendance_vehicle_connected_time_state_uuid" : no_action_driver_attendance_vehicle_connected_time_state_uuid
                }
                
                session.add(DriverAttendance(**attendence_data))
                
                
                vehicle_main_instance = await get_tuple_instance(session , VehicleMain ,{'vehicle_uuid': req.vehicle_uuid} )
                vehicle_main_instance.assigned = True
                vehicle_main_instance.driver_uuid = driver_uuid
            
            
            if mfo_vehicle_instance:
                for key, value in mfo_vehilce_mapping_data.items():
                    setattr(mfo_vehicle_instance, key, value)
                
            
        # await session.commit()
    data_res = verify_and_add_driver_response(**final_response)
    return success_response(request , data_res , message = "Driver added successfully")
        
        
        


@mfo_driver_management_router.get("/getAllDrivers", response_model=standard_success_response[get_all_drivers_response], status_code=200)
async def getAllDrivers(request:Request,
                        mfo_uuid=Depends(mfo_role_required()),
                        session: AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    unassigned_driver_list = []
    assigned_driver_list = []
    
    all_drivers = await fetch_from_table(session , DriverMfoMapping , ["driver_uuid"] , {"mfo_uuid" : mfo_uuid , "is_enable" : True})
    
    mfo_vehicle_mapping_instance = await fetch_from_table(session , MfoVehicleMapping , None,{"mfo_uuid" : mfo_uuid , "is_enable" : True})
    vehicle_uuid_for_mfo = [i["vehicle_uuid"] for i in mfo_vehicle_mapping_instance]
    driver_roles_columns = ["primary_driver" , "secondary_driver" , "tertiary1_driver" ,"tertiary2_driver" , "supervisor_driver" ]
    
    
    for driver in all_drivers:
        driver_uuid = driver["driver_uuid"]
        assigned = False
        vehicle_uuid = None
        driver_role = None
        
        for mapping in mfo_vehicle_mapping_instance:
            if mapping["current_assigned_driver"] == driver_uuid:
                assigned = True
                vehicle_uuid = mapping["vehicle_uuid"]
                driver_role = "Main driver"
                break
        
        mapped_vehicles = await fetch_from_table(session , DriverVehicleMapping , ["vehicle_uuid"] , {"driver_uuid" : driver_uuid , "is_enable" : True})
        mapped_vehicles_count = 0
        for i in mapped_vehicles:
            if i["vehicle_uuid"] in vehicle_uuid_for_mfo:
                mapped_vehicles_count +=1
        driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : driver_uuid , "is_enable" : True})
        if assigned:
            driver_status_and_activity = await get_driver_activity(session ,driver_uuid , mfo_uuid)
            # await get_driver_status_and_current_activity(session , driver_uuid)
            vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : vehicle_uuid , "is_enable" : True})
            assigned_driver_list.append(assigned_driver(
                id = driver_instance.id,
                driver_uuid = driver_uuid,
                driver_name = driver_instance.name,
                driver_profile_image = driver_instance.profile_image,
                driver_country_code = driver_instance.country_code,
                driver_phone_number = driver_instance.phone_number,
                driver_verification_status = driver_instance.verification_status,
                driver_status = driver_status_and_activity[0],
                vehicle_uuid = vehicle_uuid,
                vehicle_number = vehicle_instance.vehicle_number,
                driver_current_activity = driver_status_and_activity[1],
                driver_role = driver_role,
                driver_tag  = f"+{mapped_vehicles_count-1} vehicles mapped" if mapped_vehicles_count-1 > 1 else f"+{mapped_vehicles_count-1} vehicle mapped"
            ))
        
        else:
            unassigned_driver_list.append(unassigned_driver(
                id = driver_instance.id,
                driver_uuid = driver_uuid,
                driver_name = driver_instance.name,
                driver_profile_image = driver_instance.profile_image,
                driver_country_code = driver_instance.country_code,
                driver_phone_number = driver_instance.phone_number,
                driver_verification_status = driver_instance.verification_status,
                driver_tag  = f"+{mapped_vehicles_count} vehicles mapped" if mapped_vehicles_count >0 else "no vehicle mapped"
    
            ))
    await session.commit()
    await session.close()
            
    data_res = get_all_drivers_response(
        unassigned_drivers = unassigned_driver_list,
        assigned_drivers = assigned_driver_list
    )
    return success_response(request , data_res , message = "All Drivers data Get successfully")








@mfo_driver_management_router.get("/getDriverProfile", response_model=standard_success_response[get_driver_profile_response], status_code=200)
async def getDriverProfile(req:get_driver_profile_request,
                        request:Request,
                        mfo_uuid=Depends(mfo_role_required()),
                        session: AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : req.driver_uuid , "is_enable" : True})
    vehicle_status_dict = static_table_settings.static_table_data["VEHICLE_STATUS"]
    driver_status_and_activity = await get_driver_activity(session , req.driver_uuid , mfo_uuid)
    # await get_driver_status_and_current_activity(session , req.driver_uuid)
    app_bar = get_driver_profile_app_bar(
        driver_name = driver_instance.name,
        driver_country_code = driver_instance.country_code,
        driver_phone_number = driver_instance.phone_number,
        driver_status = driver_status_and_activity[0],
        driver_current_activity = driver_status_and_activity[1]
    )
    driver_years_of_experience = 0.0
    if driver_instance.years_of_experience:
        current_date = get_utc_time()
        delta = current_date - driver_instance.years_of_experience
        driver_years_of_experience = round(delta.days / 365.25, 2)
        
    driver_profile = get_driver_profile_driver_card(
        driver_name = driver_instance.name,
        driver_verification_status = driver_instance.verification_status,
        driver_score = driver_instance.score,
        driver_years_of_experience = driver_years_of_experience,
        driver_distance_drivern_km = driver_instance.distance_driven,
        driver_task_completed = driver_instance.assignments_completed
    )
    
    assigned_vehicle_data = {
        "vehicle_uuid" :None,
        "vehicle_number" :None
    }
    
    assigned_vehicle_instance = await get_tuple_instance(session , MfoVehicleMapping , {"mfo_uuid" : mfo_uuid , "current_assigned_driver" : req.driver_uuid , "is_enable" : True} , limit = 1)
    assigned_vehicle_uuid = None
    driver_monthly_salary  = 0.0
    driver_mfo_mapping = await get_tuple_instance(session , DriverMfoMapping , {"mfo_uuid" : mfo_uuid ,"driver_uuid" : req.driver_uuid,  "is_enable":True})
    driver_monthly_salary = driver_mfo_mapping.driver_salary
    if assigned_vehicle_instance:
        vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : assigned_vehicle_instance.vehicle_uuid , "is_enable" : True})
        assigned_vehicle_data["vehicle_uuid"] = assigned_vehicle_instance.vehicle_uuid
        assigned_vehicle_data["vehicle_number"] = vehicle_instance.vehicle_number
        assigned_vehicle_uuid = assigned_vehicle_instance.vehicle_uuid
       
        
        
    assigned_vehicle = get_driver_profile_assigned_vehicle(**assigned_vehicle_data)
    
    
    other_mapped_vehicles_list = []
    mfo_vehicle_mapping_instance = await fetch_from_table(session , MfoVehicleMapping , ["vehicle_uuid"],{"mfo_uuid" : mfo_uuid , "is_enable" : True})
    vehicle_uuid_for_mfo = [i["vehicle_uuid"] for i in mfo_vehicle_mapping_instance]
    
    mapped_vehicles = await fetch_from_table(session  , DriverVehicleMapping , ["vehicle_uuid"] , {"driver_uuid" : req.driver_uuid , "is_enable" : True})
    
    for veh  in mapped_vehicles:
        if veh["vehicle_uuid"] in vehicle_uuid_for_mfo and veh["vehicle_uuid"] != assigned_vehicle_uuid:
            vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : veh["vehicle_uuid"] , "is_enable" : True})
            mapped_driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : vehicle_instance.driver_uuid , "is_enable" : True})
            other_mapped_vehicles_list.append(get_driver_profile_other_mapped_vehicle(
                vehicle_uuid = vehicle_instance.vehicle_uuid,
                vehicle_number = vehicle_instance.vehicle_number,
                mapped_driver_name = mapped_driver_instance.name if mapped_driver_instance else None,
                vehicle_status = vehicle_status_dict.get(vehicle_instance.vehicle_status , None)
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
                PettyExpenses.driver_uuid == req.driver_uuid,
                PettyExpenses.mfo_uuid == mfo_uuid,
                PettyExpenses.is_enable == True,
                and_(
                    func.DATE(PettyExpenses.expense_date) >= start_date,
                    func.DATE(PettyExpenses.expense_date) <= end_date
                    
                )
            )

    result = await session.execute(query)
    summed_values = result.fetchone()
            
            
    driver_petty_expense = summed_values.petty_expense

    monthly_salary_and_expense = get_driver_profile_monthly_salary_and_expense(
        driver_monthly_salary = driver_monthly_salary,
        driver_petty_expense = driver_petty_expense
    )
    
    
    driver_attendance_summary_instance = await get_tuple_instance(session , DriverAttendanceSummary , 
                                                                  {"driver_uuid" : req.driver_uuid , "month" : current_month , "year" : current_year},
                                                                  order_by=[desc(DriverAttendanceSummary.id)],
                                                                  limit =1
                                                                  )
    driver_attendance = get_driver_profile_driver_attendance_summary(
            present_count = 0,
            absent_count = 0
        )
    if driver_attendance_summary_instance:
        driver_attendance = get_driver_profile_driver_attendance_summary(
                present_count = driver_attendance_summary_instance.total_present_days + driver_attendance_summary_instance.total_worked_on_leave_days,
                absent_count = driver_attendance_summary_instance.total_leave_days + driver_attendance_summary_instance.unauthorised_off
            )
    work_summary_and_policy = get_driver_profile_driver_work_summary_and_policy(
        driver_incentive_programme_summary = get_driver_profile_driver_incentive_programme_summary(
            incentive_summary = {
                "1-1500" : 1.5,
                "1500-2000" : 2,
                "2000 - above " : 2.5
                }),
        driver_sla_policy = get_driver_profile_driver_sla_policy(updated_at = get_utc_time().date()),
        driver_attendance_summary = driver_attendance
    )
    
    
    monthly_time_utilization = driver_time_utilization(
        
        total_time_hr = 3.9,
        idle_time_hr = 2.1,
        earning_time = 1.8
    )

    monthly_distance_utilization =  driver_distance_utilization(
        total_distance_km = 130.0,
        idle_distance_km = 100.0,
        earning_distance_km = 30.0
    )
    
    today_time_utilization = driver_time_utilization(
        
        total_time_hr = 3.9,
        idle_time_hr = 2.1,
        earning_time = 1.8
    )

    today_distance_utilization =  driver_distance_utilization(
        total_distance_km = 130.0,
        idle_distance_km = 100.0,
        earning_distance_km = 30.0
    )
    
    performace = get_driver_profile_driver_performance(
        time_utilization_monthly = monthly_time_utilization,
        distance_utilization_monthly = monthly_distance_utilization,
        time_utilization_today = today_time_utilization,
        distance_utilization_today = today_distance_utilization
    )
    
    driver_location_instance = await get_tuple_instance(session , 
                                                        DriverLocation , 
                                                        {"driver_uuid" : req.driver_uuid} ,
                                                        order_by = [desc(DriverLocation.id)],
                                                        limit = 1
                                                        )
    
    driver_location = None
    
    if driver_location_instance:
        driver_location = get_driver_profile_driver_location(
            driver_lat = driver_location_instance.lat,
            driver_lng = driver_location_instance.lng,
            # driver_location = await get_location_name(driver_location_instance.lat , driver_location_instance.lng),
            driver_location = "driver location"
            # driver_location_updated_at =  convert_utc_to_ist(driver_location_instance.created_at)
        )
    
    await session.commit()
    await session.close()
    data_res = get_driver_profile_response(
        app_bar = app_bar,
        driver_profile = driver_profile,
        assigned_vehicle = assigned_vehicle,
        other_mapped_vehicles = other_mapped_vehicles_list,
        monthly_salary_and_expense = monthly_salary_and_expense,
        work_summary_and_policy = work_summary_and_policy,
        performance_insight = performace,
        driver_location = driver_location
    )
    return success_response(request , data_res , message = "Driver profile get sucessfully")









@mfo_driver_management_router.get("/getUnassignedVehicleList", response_model=standard_success_response[get_unassigned_driver_data_response])
async def getUnassignedVehicleList(request:Request,
                                 req: get_unassigned_driver_data_request,
                                 mfo_uuid = Depends(mfo_role_required()),
                                 session:AsyncSession = Depends(get_async_db),
                                 session_id: str = Header(..., alias="session-id"),
                                 device_id: str = Header(..., alias="device-id")
                                 ):
    
    mapped_vehicles = []
    other_available_vehicles = []
    
    assigned_vehicle_data = None
    assigned_vehicle_uuid = None
    mapped_veh_list = []
    

    
    fuel_type_dict = static_table_settings.static_table_data["FUEL_TYPES"]
    mfo_vehicle_mapping_instance = await get_tuple_instance(session , MfoVehicleMapping , {"mfo_uuid" : mfo_uuid , "current_assigned_driver" : req.driver_uuid , "is_enable" : True})
    
    if mfo_vehicle_mapping_instance:
        vehicle_uuid = mfo_vehicle_mapping_instance.vehicle_uuid
        assigned_vehicle_uuid = vehicle_uuid
        vehicle_main_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : vehicle_uuid , "is_enable" : True})
        driver_main_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : req.driver_uuid , "is_enable" : True})
        assigned_vehicle_data = assigned_vehicle(
            vehicle_uuid = vehicle_uuid,
            vehicle_number = vehicle_main_instance.vehicle_number,
            driver_name = driver_main_instance.name,
            vehicle_model = vehicle_main_instance.vehicle_model,
            vehicle_fuel_type = fuel_type_dict.get(vehicle_main_instance.fuel_type , None)
        )
        
        
    mapped_vehicles_of_mfo = await fetch_from_table(session , MfoVehicleMapping , ["vehicle_uuid"] , {"mfo_uuid" : mfo_uuid , "is_enable" : True})
    mapped_vehicles_of_driver = await fetch_from_table(session , DriverVehicleMapping , ["vehicle_uuid"] , {"driver_uuid" : req.driver_uuid , "is_enable" : True})
    
    for veh in mapped_vehicles_of_driver: 
        if veh["vehicle_uuid"] in mapped_vehicles_of_mfo:
            mapped_veh_list.append(veh["vehicle_uuid"])
            if veh["vehicle_uuid"] != assigned_vehicle_uuid:
                vehicle_main_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : veh["vehicle_uuid"] , "is_enable" : True})
                driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : vehicle_main_instance.driver_uuid , "is_enable" : True})
                mapped_vehicles.append(
                    mapped_vehicle(
                        vehicle_uuid = veh["vehicle_uuid"],
                        vehicle_number = vehicle_main_instance.vehicle_number, 
                        driver_name = driver_instance.name if driver_instance else None,
                        vehicle_model = vehicle_main_instance.vehicle_model,
                        vehicle_fuel_type = fuel_type_dict.get(vehicle_main_instance.fuel_type , None),
                        can_be_assigned = True
                    )
                )
                
    other_vehicles_of_mfo = await fetch_from_table(session , MfoVehicleMapping , ["vehicle_uuid"] , {"mfo_uuid" : mfo_uuid , "is_enable" : True})
    
    for veh in other_vehicles_of_mfo:
        if veh["vehicle_uuid"] not in mapped_veh_list:
            vehicle_main_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : veh["vehicle_uuid"] , "is_enable" : True})
            if not vehicle_main_instance.assigned:
                other_available_vehicles.append(
                    other_available_vehicle(
                        vehicle_uuid = veh["vehicle_uuid"],
                        vehicle_number = vehicle_main_instance.vehicle_number, 
                        driver_name = None,
                        vehicle_model = vehicle_main_instance.vehicle_model,
                        vehicle_fuel_type = fuel_type_dict.get(vehicle_main_instance.fuel_type , None),
                    )
                )
            
            
    response = get_unassigned_driver_data_response(
        assigned_vehicle = assigned_vehicle_data,
        mapped_vehicles = mapped_vehicles,
        other_available_vehicles = other_available_vehicles
    )

    return success_response(request , response , message = "Unassigned Driver Data Get successfully" , round_data=False)

        
        
        
        
@mfo_driver_management_router.post("/assignDriverForFuture" , response_model= standard_success_response[assign_driver_for_future_response], status_code=200)
async def register_or_add_driver(request:Request,
                                req: assign_driver_for_future_request ,
                                mfo_uuid = Depends(mfo_role_required()),
                                session:AsyncSession = Depends(get_async_db),
                                session_id: str = Header(..., alias="session-id"),
                                device_id: str = Header(..., alias="device-id")
                        ):
    
    future_assignment_list =[]
    start_date = datetime(req.start_year, req.start_month, req.start_day)
    end_date = datetime(req.end_year, req.end_month, req.end_day)
    
    
    current_date = start_date
    while current_date <= end_date:
        assignment_data = {
            "driver_uuid": req.driver_uuid,
            "vehicle_uuid": req.vehicle_uuid,
            "arrangement_for": current_date.date()
        }
        future_assignment_list.append(assignment_data)
        current_date += timedelta(days=1)
    
    current_driver_uuid = None
    assignment_data = {
            "driver_uuid": current_driver_uuid,
            "vehicle_uuid": req.vehicle_uuid,
            "arrangement_for": current_date.date()
        }
    future_assignment_list.append(assignment_data)
    await session.execute(DriverFutureArrangement.__table__.insert(), future_assignment_list)
    await session.commit()
    
    response_data = {
        "driver_uuid" : req.driver_uuid,
        "vehicle_uuid" : req.vehicle_uuid,
        "start_date" : start_date,
        "end_date" : end_date
    }
    
    data_res = assign_driver_for_future_response(**response_data)
    return success_response(request , data_res , message = "Otp sended to Driver successfully")
    





@mfo_driver_management_router.get("/getDriverDocs" , response_model=standard_success_response[get_driver_docs_response])
async def getDriverDocs(request:Request,
                         req:get_driver_docs_request,
                         mfo_uuid = Depends(mfo_role_required()),
                         session:AsyncSession = Depends(get_async_db),
                         session_id: str = Header(..., alias="session-id"),
                         device_id: str = Header(..., alias="device-id")
                         ):
    unique_attribute = {'driver_uuid' : req.driver_uuid , "is_enable" : True}
    attributes = ["aadhar_card" , "pan_card" , "driving_license" , "aadhar_card_back" ]
    data_res = await fetch_from_table(session , DriverMain , attributes , unique_attribute)
    await session.commit()
    await session.close()
    response =  get_driver_docs_response(**data_res[0])
    return success_response(request , response , message = "Vehicle Docs Get successfully")




@mfo_driver_management_router.put("/updateDriverSalary" , response_model=standard_success_response[update_driver_salary_response])
async def updateDriverSalary(request:Request,
                         req:update_driver_salary_request,
                         mfo_uuid = Depends(mfo_role_required()),
                         session:AsyncSession = Depends(get_async_db),
                         session_id: str = Header(..., alias="session-id"),
                         device_id: str = Header(..., alias="device-id")
                         ):
    mapping_instance = await get_tuple_instance(session , DriverMfoMapping , {"driver_uuid" : req.driver_uuid , "mfo_uuid" : mfo_uuid, "is_enable" : True})
    
    if not mapping_instance:
        raise NotFoundError("No Driver Mapping found with this driver")
    
    mapping_instance.is_enable = False
    mapping_instance.disabled_at = get_utc_time()
    mapping_data = {
        "mfo_uuid" :mfo_uuid,
        "driver_uuid":req.driver_uuid,
        "driver_salary" : req.driver_salary
    }
    await insert_into_table(session , DriverMfoMapping , mapping_data)
    await session.commit()
    await session.close()
    response =  update_driver_salary_response(driver_uuid = req.driver_uuid , driver_salary = req.driver_salary)
    return success_response(request , response , message = "Driver Salary updated successfully")




@mfo_driver_management_router.put("/removeDriver" , response_model = standard_success_response[remove_driver_response])
async def removeDriver(request:Request,
                        req: remove_driver_request,
                        mfo_uuid = Depends(mfo_role_required()),
                        session:AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    
    vehicle_instance = await get_tuple_instance(session  , VehicleMain , {"driver_uuid" : req.driver_uuid , "mfo_uuid" : mfo_uuid , "is_enable" : True})
    
    if vehicle_instance:
        vehicle_instance.assigned = False
        vehicle_instance.driver_uuid = None
    
    driver_mfo_mapping = await get_tuple_instance(session , DriverMfoMapping , {"driver_uuid" : req.driver_uuid , "mfo_uuid" : mfo_uuid , "is_enable" :  True})
    if driver_mfo_mapping:
        driver_mfo_mapping.is_enable = False
        driver_mfo_mapping.disabled_at = get_utc_time()
        
    
    driver_vehicle_mapppings = await fetch_from_table(session , DriverVehicleMapping ,["vehicle_uuid"], {"driver_uuid" : req.driver_uuid , "is_enable" : True})
    driver_roles = ["primary_driver" ,"secondary_driver" ,"tertiary1_driver" ,"tertiary2_driver" ,"supervisor_driver","current_assigned_driver"]
    for veh in driver_vehicle_mapppings:
        veh_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : veh["vehicle_uuid"] , "mfo_uuid" : mfo_uuid , "is_enable" : True})
        if veh_instance:
            driver_vehicle_mapping = await get_tuple_instance(session , DriverVehicleMapping , {"vehicle_uuid" : veh["vehicle_uuid"] , "driver_uuid" : req.driver_uuid , "is_enable" : True})
            if driver_vehicle_mapping:
                driver_vehicle_mapping.is_enable = False
                driver_vehicle_mapping.disabled_at = get_utc_time()
            
            mfo_vehicle_instance = await get_tuple_instance(session , MfoVehicleMapping , {"mfo_uuid" : mfo_uuid , "vehicle_uuid" : veh["vehicle_uuid"] , "is_enable" : True})
            if mfo_vehicle_instance:
                for i in driver_roles:
                    driver = getattr(mfo_vehicle_instance , i)
                    if driver == req.driver_uuid:
                        setattr(mfo_vehicle_instance , i , None)
                
            
    await session.commit()
    await session.close()
    return success_response(request ,remove_driver_response(success_status=True) ,"Driver removed successfully")
