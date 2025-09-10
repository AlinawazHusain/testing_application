from pydantic import BaseModel


class TaskWSSchema(BaseModel):
    event : str
    points_earned: int