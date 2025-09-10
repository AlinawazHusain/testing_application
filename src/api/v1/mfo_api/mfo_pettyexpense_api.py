import calendar
from datetime import datetime
from fastapi import APIRouter , Depends, Header, Request
from sqlalchemy import and_, func, select
from auth.dependencies import mfo_role_required
from config.exceptions import InvalidRequestError
from models.assignment_mapping_models import DriverMfoMapping, MfoVehicleMapping
from models.driver_models import DriverMain
from models.petty_expense_models import PettyExpenses
from models.vehicle_models import VehicleMain
from schemas.v1.mfo_schemas.mfo_pettyexpense_schema import add_pettyexpense_request, add_pettyexpense_response, delete_pettyexpense_request, delete_pettyexpense_response, edit_pettyexpense_request, edit_pettyexpense_response, get_driver_pettyexpense, get_driver_pettyexpense_request, get_driver_pettyexpense_response, get_drivers_with_pettycash_request, get_drivers_with_pettycash_response, get_pettyexpense_request, get_pettyexpense_response, get_vehicle_pettyexpense, get_vehicle_pettyexpense_request, get_vehicle_pettyexpense_response, get_vehicle_with_pettycash_request, get_vehicles_with_pettycash_response, individual_petty_expense, petty_expense
from schemas.v1.standard_schema import standard_success_response
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db
from db.database_operations import fetch_from_table, get_tuple_instance, insert_into_table
from utils.response import success_response
from utils.time_utils import get_utc_time 

mfo_pettyexpense_router = APIRouter()






@mfo_pettyexpense_router.get("/getDriversWithPettyCash" , response_model = standard_success_response[get_drivers_with_pettycash_response] )
async def getDriversWithPettyCash(request:Request,
                                  req:get_drivers_with_pettycash_request,
                                  mfo_uuid = Depends(mfo_role_required()),
                                  session:AsyncSession = Depends(get_async_db),
                                  session_id: str = Header(..., alias="session-id"),
                                  device_id: str = Header(..., alias="device-id")
                                  ):
    petty_expense_list = []
    all_drivers = await fetch_from_table(session , DriverMfoMapping , ["driver_uuid"] , {"mfo_uuid" : mfo_uuid , "is_enable" : True})
    
    current_year = req.year
    current_month = req.month

    start_date = datetime(current_year, current_month, 1, 0, 0, 0)

    last_day = calendar.monthrange(current_year, current_month)[1]
    end_date = datetime(current_year, current_month, last_day, 23, 59, 59)
    
    for dri in all_drivers:
        query= select(
                    func.COALESCE(func.SUM(PettyExpenses.expense), 0).label("petty_expense"),
                ).where(
                    PettyExpenses.driver_uuid == dri["driver_uuid"],
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
        vehicle_instance = await get_tuple_instance(session , VehicleMain , {"driver_uuid" : dri["driver_uuid"] , "is_enable" : True})
        driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : dri["driver_uuid"] , "is_enable" : True})
        vehicle_uuid = None
        vehicle_number = None
        
        if vehicle_instance:
            vehicle_uuid = vehicle_instance.vehicle_uuid
            vehicle_number = vehicle_instance.vehicle_number
            
        petty_expense_list.append(
            individual_petty_expense(
                driver_uuid = dri["driver_uuid"],
                vehicle_uuid = vehicle_uuid,
                driver_name = driver_instance.name,
                driver_profile_image = driver_instance.profile_image,
                vehicle_number = vehicle_number,
                pettycash = driver_petty_expense
            )
        )
    
    
    data_res = get_drivers_with_pettycash_response(petty_expenses_per_driver=petty_expense_list)
    await session.commit()
    await session.close()
    return success_response(request , data_res , message = "Petty expense per driver fetched successfully")




@mfo_pettyexpense_router.get("/getVehiclesWithPettyCash" , response_model = standard_success_response[get_vehicles_with_pettycash_response])
async def getVehiclesWithPettyCash(request:Request,
                                   req:get_vehicle_with_pettycash_request,
                          mfo_uuid = Depends(mfo_role_required()),
                          session:AsyncSession = Depends(get_async_db),
                          session_id: str = Header(..., alias="session-id"),
                          device_id: str = Header(..., alias="device-id")
                          ):
    petty_expense_list = []
    all_vehicles = await fetch_from_table(session , MfoVehicleMapping , ["vehicle_uuid"] , {"mfo_uuid" : mfo_uuid , "is_enable" : True})
    
    current_year = req.year
    current_month = req.month


    start_date = datetime(current_year, current_month, 1, 0, 0, 0)

    last_day = calendar.monthrange(current_year, current_month)[1]
    end_date = datetime(current_year, current_month, last_day, 23, 59, 59)
    
    for veh in all_vehicles:
        query= select(
                    func.COALESCE(func.SUM(PettyExpenses.expense), 0).label("petty_expense"),
                ).where(
                    PettyExpenses.vehicle_uuid == veh["vehicle_uuid"],
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
        vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : veh["vehicle_uuid"] , "is_enable" : True})
        driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : vehicle_instance.driver_uuid , "is_enable" : True})
        driver_uuid = None
        driver_name = None
        driver_profile_image = None
        
        if driver_instance:
            driver_uuid = driver_instance.driver_uuid
            driver_name = driver_instance.name
            driver_profile_image = driver_instance.profile_image
            
        petty_expense_list.append(
            individual_petty_expense(
                driver_uuid = driver_uuid,
                vehicle_uuid =  veh["vehicle_uuid"],
                driver_name = driver_name,
                driver_profile_image = driver_profile_image,
                vehicle_number = vehicle_instance.vehicle_number,
                pettycash = driver_petty_expense
            )
        )
    
    
    data_res = get_vehicles_with_pettycash_response(petty_expense_per_vehicle=petty_expense_list)
    await session.commit()
    await session.close()
    return success_response(request , data_res , message = "Petty expense per vehicle fetched  successfully")







@mfo_pettyexpense_router.post("/addPettyexpense" , response_model = standard_success_response[add_pettyexpense_response] )
async def addPettyexpense(request:Request,
                          req:add_pettyexpense_request,
                         mfo_uuid = Depends(mfo_role_required()),
                         session:AsyncSession = Depends(get_async_db),
                         session_id: str = Header(..., alias="session-id"),
                         device_id: str = Header(..., alias="device-id")
                         ):
    
    if not req.vehicle_uuid and not req.driver_uuid:
        raise InvalidRequestError("Both Driver UUID and Vehicle UUID cant be null , required atleast any one")
    
    if req.expense <=0:
        raise InvalidRequestError("Invalid expense value ! , Expense should be greater than zero")
    expense_date =  datetime(req.expense_year, req.expense_month, req.expense_date)
    petty_expense_data = {
        "mfo_uuid": mfo_uuid,
        "driver_uuid" : req.driver_uuid,
        "vehicle_uuid" : req.vehicle_uuid,
        "expense_currency" : req.expense_currency,
        "expense" : req.expense,
        "expense_description" : req.expense_description, 
        "expense_date" : expense_date
    }
    petty_expense_instance = await insert_into_table(session , PettyExpenses , petty_expense_data)
    
    data_res = add_pettyexpense_response(**{
        "petty_expense_uuid" : petty_expense_instance.petty_expense_uuid,
        "driver_uuid" : req.driver_uuid,
        "vehicle_uuid" : req.vehicle_uuid,
        "expense_currency" : req.expense_currency,
        "expense" : req.expense,
        "expense_description" : req.expense_description}
    )
    await session.commit()
    await session.close()
    return success_response(request , data_res , message = "Petty expense added successfully")






@mfo_pettyexpense_router.get("/getPettyexpense" , response_model = standard_success_response[get_pettyexpense_response] , status_code=200)
async def getPettyexpense(request:Request,
                          req:get_pettyexpense_request,
                          mfo_uuid = Depends(mfo_role_required()),
                          session:AsyncSession = Depends(get_async_db),
                          session_id: str = Header(..., alias="session-id"),
                          device_id: str = Header(..., alias="device-id")
                         ):
    start_date = datetime(req.expense_year, req.expense_month, 1)
    last_day = calendar.monthrange(req.expense_year, req.expense_month)[1]
    end_date = datetime(req.expense_year, req.expense_month, last_day , 23 , 59)
    petty_expense_data = await fetch_from_table(session ,
                                                PettyExpenses ,
                                                ["petty_expense_uuid" , "vehicle_uuid" ,"driver_uuid", "expense_date" ,"expense_currency", "expense" ,"expense_description"],
                                                filters=[
                                                    PettyExpenses.mfo_uuid == mfo_uuid,
                                                    PettyExpenses.is_enable == True,
                                                    PettyExpenses.expense_date >= start_date,
                                                    PettyExpenses.expense_date <= end_date
                                                ],
                                                order_by= "id"
                                                )
    petty_expense_list = []
    for exp in petty_expense_data:
        petty_expense_list.append(
        petty_expense(
            petty_expense_uuid = exp["petty_expense_uuid"],
            vehicle_uuid = exp["vehicle_uuid"],
            driver_uuid = exp["driver_uuid"],
            expense_date = exp["expense_date"],
            expense_currency = exp["expense_currency"],
            expense = exp["expense"],
            expense_description =exp["expense_description"]
            ) 
        )
    
    data_res = get_pettyexpense_response(petty_expenses = petty_expense_list)
    return success_response(request , data_res , message = "Petty expenses get successfully")






@mfo_pettyexpense_router.put("/editPettyExpense" , response_model = standard_success_response[edit_pettyexpense_response] , status_code=200)
async def editPettyexpense(request:Request,
                          req:edit_pettyexpense_request,
                          mfo_uuid = Depends(mfo_role_required()),
                          session:AsyncSession = Depends(get_async_db),
                          session_id: str = Header(..., alias="session-id"),
                          device_id: str = Header(..., alias="device-id")
                         ):
    petty_expense_instance = await get_tuple_instance(session  , PettyExpenses , {"petty_expense_uuid" :req.petty_expense_uuid , "mfo_uuid" : mfo_uuid , "is_enable" : True} )
    if petty_expense_instance:
        if req.expense:
            petty_expense_instance.expense = req.expense
        if req.expense_description:
            petty_expense_instance.expense_description = req.expense_description
            
    await session.commit()
    await session.close()
    data_res = edit_pettyexpense_response(edit_status = True)
    return success_response(request , data_res , message = "Petty expense edited successfully")



@mfo_pettyexpense_router.delete("/deletePettyExpense" , response_model = standard_success_response[delete_pettyexpense_response] , status_code=200)
async def deletePettyexpense(request:Request,
                          req:delete_pettyexpense_request,
                          mfo_uuid = Depends(mfo_role_required()),
                          session:AsyncSession = Depends(get_async_db),
                          session_id: str = Header(..., alias="session-id"),
                          device_id: str = Header(..., alias="device-id")
                          ):
    petty_expense_instance = await get_tuple_instance(session  , PettyExpenses , {"petty_expense_uuid" :req.petty_expense_uuid , "mfo_uuid" : mfo_uuid , "is_enable" : True} )
    if petty_expense_instance:
        petty_expense_instance.is_enable = False
        petty_expense_instance.disabled_at = get_utc_time()
        
    await session.commit()
    await session.close()
    data_res = delete_pettyexpense_response(delete_status = True)
    return success_response(request , data_res , message = "Petty expense deleted successfully")









@mfo_pettyexpense_router.get("/getVehiclePettyexpenses" , response_model = standard_success_response[get_vehicle_pettyexpense_response])
async def getVehiclePettyexpenses(request:Request,
                                   req:get_vehicle_pettyexpense_request,
                                   mfo_uuid = Depends(mfo_role_required()),
                                   session:AsyncSession = Depends(get_async_db),
                                   session_id: str = Header(..., alias="session-id"),
                                   device_id: str = Header(..., alias="device-id")
                                   ):
    petty_expense_list = []

    current_year = req.year
    current_month = req.month

    start_date = datetime(current_year, current_month, 1, 0, 0, 0)

    last_day = calendar.monthrange(current_year, current_month)[1]
    end_date = datetime(current_year, current_month, last_day, 23, 59, 59)
    
    petty_expenses = await fetch_from_table(session ,
                                            PettyExpenses,
                                            None,
                                            filters=[
                                                PettyExpenses.vehicle_uuid == req.vehicle_uuid,
                                                PettyExpenses.mfo_uuid == mfo_uuid,
                                                PettyExpenses.is_enable == True,
                                                PettyExpenses.expense_date >= start_date,
                                                PettyExpenses.expense_date <= end_date,
                                            ],
                                            order_by = "-id"
                                            )
    
    vehicle_instance = await get_tuple_instance(session , VehicleMain , {"vehicle_uuid" : req.vehicle_uuid , "is_enable" : True})
    for exp in petty_expenses:
        petty_expense_list.append(
            get_vehicle_pettyexpense(
                petty_expense_uuid = exp["petty_expense_uuid"],
                vehicle_number = vehicle_instance.vehicle_number,
                pettycash = exp["expense"],
                expense_description = exp["expense_description"],
                expense_date = exp["expense_date"].date()
            )
        )
    
    
    data_res = get_vehicle_pettyexpense_response(vehicle_pettyexpense=petty_expense_list)
    await session.commit()
    await session.close()
    return success_response(request , data_res , message = "Petty expense of  vehicle fetched  successfully")








@mfo_pettyexpense_router.get("/getDriverPettyexpenses" , response_model = standard_success_response[get_driver_pettyexpense_response])
async def getDriverPettyexpenses(request:Request,
                                   req:get_driver_pettyexpense_request,
                                   mfo_uuid = Depends(mfo_role_required()),
                                   session:AsyncSession = Depends(get_async_db),
                                   session_id: str = Header(..., alias="session-id"),
                                   device_id: str = Header(..., alias="device-id")
                                   ):
    petty_expense_list = []
    
    current_year = req.year
    current_month = req.month

    start_date = datetime(current_year, current_month, 1, 0, 0, 0)

    last_day = calendar.monthrange(current_year, current_month)[1]
    end_date = datetime(current_year, current_month, last_day, 23, 59, 59)
    
    petty_expenses = await fetch_from_table(session ,
                                            PettyExpenses,
                                            None,
                                            filters=[
                                                PettyExpenses.driver_uuid == req.driver_uuid,
                                                PettyExpenses.mfo_uuid == mfo_uuid,
                                                PettyExpenses.is_enable == True,
                                                PettyExpenses.expense_date >= start_date,
                                                PettyExpenses.expense_date <= end_date
                                            ],
                                            order_by = "-id"
                                            )
    
    driver_instance = await get_tuple_instance(session , DriverMain , {"driver_uuid" : req.driver_uuid , "is_enable" : True})
    for exp in petty_expenses:
        petty_expense_list.append(
            get_driver_pettyexpense(
                petty_expense_uuid =  exp["petty_expense_uuid"],
                driver_name = driver_instance.name,
                driver_profile_image = driver_instance.profile_image,
                pettycash = exp["expense"],
                expense_description = exp["expense_description"],
                expense_date = exp["expense_date"].date()
            )
        )
    
    
    data_res = get_driver_pettyexpense_response(driver_pettyexpense=petty_expense_list)
    await session.commit()
    await session.close()
    return success_response(request , data_res , message = "Petty expense of  vehicle fetched  successfully")





