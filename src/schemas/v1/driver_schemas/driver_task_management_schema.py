from datetime import datetime
from pydantic import BaseModel
from typing import Any, Optional


class Task(BaseModel):
    model_type:str
    sub_model_type:str
    task_start_time:datetime
    task_end_time:datetime
    task_details:Optional[Any] = None
    
    

class currentPorterTrip(BaseModel):
    """_summary_

    Attributes:
        trip_uuid (str): UUID of porter_trip
    """
    porter_trip_uuid : Optional[str] = None
    porter_trip_on_time : Optional[Any] = None
    current_porter_trip_running_time:Optional[Any] = None

class get_tasks_response(BaseModel):
    
    """
    Request model for getting tasks .

    Attributes:
        points_earned_today (int): Total points earned on a particular day (Today).
        incentive_earned_today (int): Total incentives earned on a particular day (Today).
        present_status (bool): Status of present marked today or not.
        vehicle_connected_status(bool): Status of connected to vehicle or not 
        new_points_earned_now (bool): Status that new points earned for any task or not. 
        points_earned_now (int) : If new points earned then how much earned.
        tasks (Task) : List of today tasks
    """
    
    points_earned_today : Optional[int] = 0
    incentive_earned_today : Optional[float] = 0
    
    have_attendance:bool
    have_pending_request:bool
    present_status:bool
    vehicle_connected_status:bool
    vehicle_uuid:Optional[str] = None
    attendance_trigger_time:Optional[datetime] = None
    points_to_earn_on_task:Optional[int] = 0
    tasks : list[Task]
    current_trip : currentPorterTrip
    points_to_earn_on_trip :Optional[int] = 0