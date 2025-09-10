from pydantic import BaseModel


class getMonthlyOverviewReqeust(BaseModel):
    """
    Request model for retrieving the monthly overview

    Attributes:
        year (int): Year for which fetch the records.
        month (int): Month for which fetch the records.
    """
    month:int
    year:int
    
    
class getMonthlyOverviewResponse(BaseModel):
    """
    Response model for retrieving the monthly overview

    Attributes:
        earned_incentive_earned (int): Total earned incentive a particular month.
        total_incentive_points (int): Total incentive points a particular month.
        working_days (int): Total working days of policy.
        present_days (int): Total present marked this month till now.
        leaves (int): Total leaves of a particular month.
        work_on_off_days (int): Total work on off days in a particular month.
    """
    earned_incentive:int
    total_incentive:int
    points_earned:int
    total_points :int
    working_days:int
    present_days:int
    leaves:int
    work_on_off_days:int