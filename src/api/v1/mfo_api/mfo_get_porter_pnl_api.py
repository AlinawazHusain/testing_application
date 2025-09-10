from fastapi import APIRouter , Depends, Header, Request
from datetime import timedelta
from sqlalchemy import and_, func, select 
from auth.dependencies import mfo_role_required
from db.database_operations import fetch_from_table, get_tuple_instance
from models.assignment_mapping_models import DriverMfoMapping
from models.costing_models import VehicleCosting
from models.driver_models import DriverMain
from models.petty_expense_models import PettyExpenses
from models.porter_models import AvaronnPorterTrip , PorterPnL
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db
from models.vehicle_models import VehicleMain
from schemas.v1.standard_schema import standard_success_response
from settings.static_data_settings import static_table_settings
from schemas.v1.mfo_schemas.mfo_porter_pnl_schema import(
    get_monthly_porter_pnl_response, get_today_porter_pnl_response,
    get_yesterday_porter_pnl_response
    )
from utils.response import success_response
from utils.time_utils import get_utc_time





mfo_get_porter_pnl_router = APIRouter()








@mfo_get_porter_pnl_router.get("/getTodayPorterPnL", response_model= standard_success_response[get_today_porter_pnl_response], status_code=200)
async def get_today_porterpnl(request:Request,
                              mfo_uuid=Depends(mfo_role_required()),
                        session: AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    
    vehicle_data = []
    
    vehicle_main_unique_attribute = {"mfo_uuid": mfo_uuid , "is_enable" : True}
    vehicle_attributes = ['vehicle_number', 'vehicle_uuid' , 'vehicle_status' , 'driver_uuid']
    
    vehicles = await fetch_from_table(session, VehicleMain, vehicle_attributes, vehicle_main_unique_attribute)
    vehicles_on_road = 0
    vehicle_data = []
    trips_completed = 0
    variable_cost = 0
    earning = 0
    petty_expense = 0
    total_distance = 0
    costing = 0
    today = get_utc_time()
    last_day_of_month = ((today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)).date()
    
    today = get_utc_time().date()
    
    
    if vehicles:
        vehicle_status_dict = static_table_settings.static_table_data['VEHICLE_STATUS']
        for vehicle in vehicles:
            vehicle_uuid = vehicle['vehicle_uuid']
            query = select(
                func.COALESCE(func.SUM(AvaronnPorterTrip.expected_earning), 0).label("total_expected_earning"),
                func.COALESCE(func.SUM(AvaronnPorterTrip.expected_distance_km), 0).label("total_expected_distance_km"),
                func.COALESCE(func.SUM(AvaronnPorterTrip.expected_cost), 0).label("total_expected_cost"),
                func.COUNT(AvaronnPorterTrip.id).label("total_trips")
            ).where(
                AvaronnPorterTrip.vehicle_uuid == vehicle_uuid,
                func.DATE(AvaronnPorterTrip.trip_on_time) == func.DATE(get_utc_time())
            )

            result = await session.execute(query)
            summed_values = result.fetchone()
            query= select(
                func.COALESCE(func.SUM(PettyExpenses.expense), 0).label("petty_expense"),
            ).where(
                PettyExpenses.mfo_uuid == mfo_uuid,
                PettyExpenses.vehicle_uuid == vehicle_uuid,
                PettyExpenses.is_enable == True,
                and_(
                    func.DATE(PettyExpenses.expense_date) == today
                    
                )
            )

            result = await session.execute(query)
            summed_values_petty = result.fetchone()
                    
                    
            petty_expenses = summed_values_petty.petty_expense
            petty_expense+= petty_expenses
            
            vehicle_costing_instance = await get_tuple_instance(session , VehicleCosting , {"vehicle_uuid" : vehicle_uuid ,  "is_enable":True})
            driver_salary = 0.0
            if vehicle["driver_uuid"]:
                mapping_instance = await get_tuple_instance(session , DriverMfoMapping , {"mfo_uuid" : mfo_uuid , "driver_uuid" : vehicle["driver_uuid"] , "is_enable" : True})
                if mapping_instance:
                    driver_salary = mapping_instance.driver_salary
            cost = (vehicle_costing_instance.vehicle_emi +  vehicle_costing_instance.parking_cost + driver_salary + vehicle_costing_instance.maintenance)/int(last_day_of_month.day)
            cost += petty_expenses
            
            vehicle_earning = summed_values.total_expected_earning
            earning += vehicle_earning
            vehicle_total_distance = summed_values.total_expected_distance_km
            
            vehicle_costing = summed_values.total_expected_cost + cost
            costing += vehicle_costing - petty_expenses
            
            total_distance += vehicle_total_distance
            trips_completed += summed_values.total_trips
            
            driver_name = await fetch_from_table(session , DriverMain , ['name'] , {'driver_uuid' : vehicle['driver_uuid'] , "is_enable" : True})
            vehicle_data.append({
                "vehicle_number" : vehicle['vehicle_number'],
                "vehicle_uuid" : vehicle_uuid,
                "earning" :vehicle_earning,
                "costing" : vehicle_costing,
                "driver_name" : driver_name[0]['name'] if driver_name else 'Unknown',
                "driver_uuid" : vehicle['driver_uuid'],
                "profit/loss" : vehicle_earning-vehicle_costing,
                "vehicle_status" : vehicle_status_dict[vehicle['vehicle_status']],
                
                "distance_km": vehicle_total_distance,
            })
            if vehicle_status_dict[vehicle['vehicle_status']] in ["Idle", "Running"]:
                vehicles_on_road += 1
    
    header_data = {
        "profit/loss" : earning - costing,
        "costing" : costing,
        "earning" : earning,
        "petty_expense" : petty_expense,
        "variable_cost" : variable_cost,
        "trips_completed" : trips_completed,
        "vehicles_on_road" : vehicles_on_road,
        "total_distance" : total_distance
    }
    await session.commit()
    await session.close()

    
    data_res = get_today_porter_pnl_response(
        summary_data = header_data,
        per_vehicle_data = vehicle_data
    )
    return success_response(request , data_res , message = "Today Porter Pnl Get successfully")











@mfo_get_porter_pnl_router.get("/getYesterdayPorterPnL", response_model=standard_success_response[get_yesterday_porter_pnl_response], status_code=200)
async def get_yesterday_porter_pnl(request:Request,
                                   mfo_uuid=Depends(mfo_role_required()),
                        session: AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
            
        vehicle_main_unique_attribute = {"mfo_uuid": mfo_uuid }
        vehicle_attributes = ['vehicle_number', 'vehicle_uuid' , 'vehicle_status' , 'driver_uuid' , "created_at" , "is_enable"]
            
        vehicles = await fetch_from_table(session, VehicleMain, vehicle_attributes, vehicle_main_unique_attribute)
            
        vehicle_data = []
        trips_completed = 0
        earning_predicted = 0
        total_distance_predicted = 0
        costing_predicted = 0
        vehicles_on_road = 0
        
        petty_expense = 0
        
        earning_actual = 0
        total_distance_actual = 0
        costing_actual = 0

        yesterday_date = (get_utc_time() - timedelta(days=1)).date()
        today = get_utc_time()
        last_day_of_month = ((today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)).date()
        
        

        if vehicles:
            vehicle_status_dict = static_table_settings.static_table_data['VEHICLE_STATUS']
            fuel_based_costing_dict = static_table_settings.static_table_data['FUEL_BASED_COSTING']
            for vehicle in vehicles:
                if vehicle["created_at"].date() == today:
                    continue
                vehicle_uuid = vehicle['vehicle_uuid']
                query1 = select(
                    func.COALESCE(func.SUM(AvaronnPorterTrip.expected_earning), 0).label("total_expected_earning"),
                    func.COALESCE(func.SUM(AvaronnPorterTrip.expected_distance_km), 0).label("total_expected_distance_km"),
                    func.COALESCE(func.SUM(AvaronnPorterTrip.expected_cost), 0).label("total_expected_cost"),
                    func.COUNT(AvaronnPorterTrip.id).label("total_trips")
                ).where(
                    AvaronnPorterTrip.vehicle_uuid == vehicle_uuid,
                    func.DATE(AvaronnPorterTrip.trip_on_time) == yesterday_date
                )
                
                result1 = await session.execute(query1)
                summed_values_predicted = result1.fetchone()
                
                query= select(
                    func.COALESCE(func.SUM(PettyExpenses.expense), 0).label("petty_expense")
                ).where(
                    PettyExpenses.mfo_uuid == mfo_uuid,
                    PettyExpenses.vehicle_uuid == vehicle_uuid,
                    PettyExpenses.is_enable == True,
                    and_(
                        func.DATE(PettyExpenses.expense_date) == yesterday_date
                        
                    )
                )

                result = await session.execute(query)
                summed_values_petty = result.fetchone()
                
                petty_expenses = summed_values_petty.petty_expense
                petty_expense+= petty_expenses
                
                vehicle_costing_instance = await get_tuple_instance(session , VehicleCosting , {"vehicle_uuid" : vehicle_uuid ,  "is_enable":True})
                per_km_cost = fuel_based_costing_dict[vehicle_costing_instance.fuel_based_costing_uuid]
                driver_salary = 0.0
                if vehicle["driver_uuid"]:
                    mapping_instance = await get_tuple_instance(session , DriverMfoMapping , {"mfo_uuid" : mfo_uuid , "driver_uuid" : vehicle["driver_uuid"] , "is_enable" : True})
                    if mapping_instance:
                        driver_salary = mapping_instance.driver_salary
                
                cost = (vehicle_costing_instance.vehicle_emi +  vehicle_costing_instance.parking_cost + vehicle_costing_instance.maintenance + driver_salary)/int(last_day_of_month.day)
                cost += petty_expenses

                vehicle_earning_predicted = summed_values_predicted.total_expected_earning
                earning_predicted += vehicle_earning_predicted
                vehicle_total_distance_predicted = summed_values_predicted.total_expected_distance_km
                total_distance_predicted += vehicle_total_distance_predicted
                
                vehicle_costing_predicted = summed_values_predicted.total_expected_cost + cost
                costing_predicted += vehicle_costing_predicted - petty_expenses
                
                trips_completed += summed_values_predicted.total_trips
                
                query2 = select(
                    func.COALESCE(func.SUM(PorterPnL.trip_earnings), 0).label("total_earning"),
                    func.COALESCE(func.SUM(PorterPnL.distance_km), 0).label("total_distance_km"),
                    func.COUNT(PorterPnL.id).label("total_trips")
                ).where(
                    PorterPnL.vehicle_uuid == vehicle_uuid,
                    func.DATE(PorterPnL.date) == yesterday_date
                )
                result2 = await session.execute(query2)
                summed_values_actual = result2.fetchone()
                
                vehicle_earning_actual = summed_values_actual.total_earning
                earning_actual += vehicle_earning_actual
                vehicle_total_distance_actual = summed_values_actual.total_distance_km
                total_distance_actual += vehicle_total_distance_actual
                
                vehicle_costing_actual = (vehicle_total_distance_actual * per_km_cost) + cost
                costing_actual += vehicle_costing_actual
                
                

                driver_name = await fetch_from_table(session, DriverMain, ['name'], {'driver_uuid': vehicle['driver_uuid']})
                
                vehicle_data.append({
                    "vehicle_number": vehicle['vehicle_number'],
                    "vehicle_uuid": vehicle_uuid,
                    "earning_actual": vehicle_earning_actual,
                    "earning_predicted": vehicle_earning_predicted,
                    
                    "costing_actual": vehicle_costing_actual,
                    "costing_predicted": vehicle_costing_predicted,
                    
                    "driver_name": driver_name[0]['name'] if driver_name else 'Unknown',
                    "driver_uuid": vehicle['driver_uuid'],
                    
                    "profit/loss_actual": vehicle_earning_actual - vehicle_costing_actual,
                    "profit/loss_predicted": vehicle_earning_predicted - vehicle_costing_predicted,
                    
                    "vehicle_status" : vehicle_status_dict[vehicle['vehicle_status']],
                    
                    "distance_km_actual": vehicle_total_distance_actual,
                    "distance_km_predicted": vehicle_total_distance_predicted,
                })
                if vehicle_status_dict[vehicle['vehicle_status']] in ["Idle", "Running"] and vehicle["is_enable"]:
                    vehicles_on_road += 1
        header_data = {
            "profit/loss_predicted": earning_predicted - costing_predicted,
            "profit/loss_actual" : earning_actual - costing_actual,
            
            "costing_predicted": costing_predicted,
            "costing_actual": costing_actual,
            
            "earning_predicted": earning_predicted,
            "earning_actual": earning_actual,
            "petty_expense" : petty_expense,
            
            "trips_completed": trips_completed,
            "vehicles_on_road": vehicles_on_road,
            
            "total_distance_predicted": total_distance_predicted,
            "total_distance_actual": total_distance_actual,
        }

        await session.commit()
        await session.close()
            
       
        data_res = get_yesterday_porter_pnl_response(
            summary_data = header_data,
            per_vehicle_data = vehicle_data
        )
        return success_response(request , data_res , message = "Yesterday Porter Pnl Get successfully")







@mfo_get_porter_pnl_router.get("/getMonthlyPorterPnL", response_model=standard_success_response[get_monthly_porter_pnl_response], status_code=200)
async def get_monthly_porter_pnl(request:Request,
                                 mfo_uuid=Depends(mfo_role_required()),
                        session: AsyncSession = Depends(get_async_db),
                        session_id: str = Header(..., alias="session-id"),
                        device_id: str = Header(..., alias="device-id")
                        ):
    
    vehicle_main_unique_attribute = {"mfo_uuid": mfo_uuid}
    vehicle_attributes = ['vehicle_number', 'vehicle_uuid' , 'vehicle_status' , 'driver_uuid' , 'created_at' , "is_enable"]
        
    vehicles = await fetch_from_table(session, VehicleMain, vehicle_attributes, vehicle_main_unique_attribute)
        
    vehicle_data = []
    trips_completed = 0
    earning = 0
    petty_expense = 0
    total_distance = 0
    costing = 0
    vehicles_on_road = 0

    today = get_utc_time()
    
    first_day_of_month = today.replace(day=1).date() 
    last_day_of_month = ((today.replace(day=28) + timedelta(days=4)).replace(day=1) - timedelta(days=1)).date()
    
    
    if vehicles:
        vehicle_status_dict = static_table_settings.static_table_data['VEHICLE_STATUS']
        fuel_based_costing_dict = static_table_settings.static_table_data['FUEL_BASED_COSTING']
        for vehicle in vehicles:
            cost_start_date = first_day_of_month if vehicle["created_at"].date() <  first_day_of_month else  vehicle["created_at"].date()
            total_cost_days = int(today.day) - int(cost_start_date.day)+1
            vehicle_uuid = vehicle['vehicle_uuid']
            
            query= select(
                func.COALESCE(func.SUM(PorterPnL.trip_earnings), 0).label("total_earning"),
                    func.COALESCE(func.SUM(PorterPnL.distance_km), 0).label("total_distance_km"),
                    func.COUNT(PorterPnL.id).label("total_trips")
            ).where(
                PorterPnL.vehicle_uuid == vehicle['vehicle_uuid'],
                and_(
                    func.DATE(PorterPnL.date) >= first_day_of_month,
                    func.DATE(PorterPnL.date) <= last_day_of_month
                )
            )

            result = await session.execute(query)
            summed_values = result.fetchone()
            
            query1= select(
                    func.COALESCE(func.SUM(PettyExpenses.expense), 0).label("petty_expense")
                ).where(
                    PettyExpenses.mfo_uuid == mfo_uuid,
                    PettyExpenses.vehicle_uuid == vehicle_uuid,
                    PettyExpenses.is_enable == True,
                    and_(
                        func.DATE(PettyExpenses.expense_date) >= first_day_of_month,
                        func.DATE(PettyExpenses.expense_date) <= last_day_of_month  
                    )
                )

            result1 = await session.execute(query1)
            summed_values_petty = result1.fetchone()
                
            petty_expenses = summed_values_petty.petty_expense
            petty_expense+= petty_expenses
            vehicle_costing_instance = await get_tuple_instance(session , VehicleCosting , {"vehicle_uuid" : vehicle_uuid , "is_enable":True})
            driver_salary = 0.0
            if vehicle["driver_uuid"]:
                mapping_instance = await get_tuple_instance(session , DriverMfoMapping , {"mfo_uuid" : mfo_uuid , "driver_uuid" : vehicle["driver_uuid"] , "is_enable" : True})
                if mapping_instance:
                    driver_salary = mapping_instance.driver_salary
            per_km_cost = fuel_based_costing_dict[vehicle_costing_instance.fuel_based_costing_uuid]
            cost = ((vehicle_costing_instance.vehicle_emi +  vehicle_costing_instance.parking_cost + driver_salary + vehicle_costing_instance.maintenance)/int(last_day_of_month.day))*total_cost_days
            cost += petty_expenses
            
            trips_completed += summed_values.total_trips
            vehicle_earning = summed_values.total_earning
            earning += vehicle_earning
            vehicle_total_distance = summed_values.total_distance_km
            total_distance += vehicle_total_distance
            
            vehicle_costing = (vehicle_total_distance * per_km_cost) + cost
            costing += vehicle_costing - petty_expenses
            

            driver_name = await fetch_from_table(session, DriverMain, ['name'], {'driver_uuid': vehicle['driver_uuid']})
            
            vehicle_data.append({
                "vehicle_number": vehicle['vehicle_number'],
                "vehicle_uuid": vehicle_uuid,
                "earning_": vehicle_earning,
                "costing": vehicle_costing,
                "driver_name": driver_name[0]['name'] if driver_name else 'Unknown',
                "driver_uuid": vehicle['driver_uuid'],
                "profit/loss": vehicle_earning - vehicle_costing,
                "vehicle_status" : vehicle_status_dict[vehicle['vehicle_status']],
                "distance_km": vehicle_total_distance
            })
            if vehicle_status_dict[vehicle['vehicle_status']] in ["Idle", "Running"] and vehicle["is_enable"]:
                    vehicles_on_road += 1

    header_data = {
        "profit/loss": earning - costing,
        "costing": costing,
        "earning": earning,
        "petty_expense" : petty_expense,
        "trips_completed": trips_completed,
        "vehicles_on_road": vehicles_on_road,
        "total_distance": total_distance,
    }

    await session.commit()
    await session.close()
        
    
        
    data_res = get_monthly_porter_pnl_response(
        summary_data = header_data,
        per_vehicle_data = vehicle_data
    )
    return success_response(request , data_res , message = "Monthly Porter Pnl Get successfully")