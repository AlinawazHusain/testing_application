from pydantic import BaseModel

class get_today_porter_pnl_response(BaseModel):
    summary_data : dict
    per_vehicle_data : list


class get_yesterday_porter_pnl_response(BaseModel):
    summary_data : dict
    per_vehicle_data : list
    
class get_monthly_porter_pnl_response(BaseModel):
    summary_data : dict
    per_vehicle_data : list