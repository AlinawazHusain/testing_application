from typing import Optional
from pydantic import BaseModel
from datetime import date


class getMonthlyCalendarEventsRequest(BaseModel):
    """
    Request model for retrieving the monthly leaves
    and work on off days requests details.

    Attributes:
        year (int): Year for which fetch the records.
        month (int): Month for which fetch the records.
    """
    month:int
    year:int



class Activity(BaseModel):
    """
    Data of a particular date and its event.

    Attributes:
        event (str): Event of the corresponding date.
        event_status (str): Event status of corresponding date.
    """
    event:str
    event_status:Optional[str] = None




class MonthlySummary(BaseModel):
    """
    Response model for retrieving summary of month for driver.

    Attributes:
        leaves (int): A list of leave records for the month.
        overtimes (int): A list of work on off days request for the month.
        presents (int) : A list of all days of present marked by driver.
    """
    leaves:int
    overtimes:int
    presents:int
    final_achieved_days:int
    monthly_working_days:int
    




class getMonthlyCalendarEventsRespoonse(BaseModel):
    """
    Response model for retrieving the monthly leaves
    and work on off days requests details.

    Attributes:
        monthly_events (list): A list of monthly events (Activities).
        monthly_summary (MonthlySummary): summary of monthly data.
    """
    monthly_calendar_events:dict[int , Activity]
    monthly_summary:MonthlySummary
    monthly_activities:dict[int , Activity]
    




class GetMonthlyLeavesResponse(BaseModel):
    """
    Response model for retrieving the monthly leave details.

    Attributes:
        leaves (list): A list of leave records for the month.
    """
    leaves: list
    

class RequestLeaveRequest(BaseModel):
    """
    Request model for submitting a leave request.

    Attributes:
        mfo_uuid (str): The unique identifier for the MFO (Mobile Field Operator) requesting leave.
        start_date (date): The start date of the requested leave.
        end_date (date): The end date of the requested leave.
        reason (str): The reason for the leave request.
        leave_type (str): The type of leave requested (e.g., vacation, sick leave).
    """
    start_date: date
    end_date: date
    reason: str
    leave_type: str
    

class RequestLeaveResponse(BaseModel):
    """
    Response model for confirming a leave request.

    Attributes:
        start_date (date): The start date of the approved leave.
        end_date (date): The end date of the approved leave.
        reason (str): The reason for the leave request.
        leave_type (str): The type of leave approved.
    """
    start_date: date
    end_date: date
    reason: str
    leave_type: str


class GetLeaveStatusResponse(BaseModel):
    """
    Response model for retrieving the leave status.

    Attributes:
        leaves (list): A list of leave records showing the status of each leave request.
    """
    leaves: list
    

class RequestWorkOnOffDayRequest(BaseModel):
    """
    Request model for submitting a request to work during a leave period.

    Attributes:
        mfo_uuid (str): The unique identifier for the MFO requesting to work during their leave.
        working_date (date): The date on which the MFO intends to work during their leave.
        reason (str): The reason for the work request during the leave period.
    """
    working_date: date
    reason: str
    


class RequestWorkOnOffDayResponse(BaseModel):
    """
    Response model for confirming a work request during leave.

    Attributes:
        working_date (date): The date on which the work during leave is approved.
        reason (str): The reason for approving work on leave.
    """
    working_date: date
    reason: str
    
    
class GetWorkOnOffDayRequestStatusResponse(BaseModel):
    """
    Response model for retrieving the status of work requests made during leave.

    Attributes:
        work_requests (list): A list of work requests and their respective status.
    """
    work_requests: list
