from typing import Optional
from pydantic import BaseModel

class send_nudge_response_request(BaseModel):
    nudge_response:bool
    action_type : str
    overlay_text : str
    
class send_nudge_response_response(BaseModel):
    success:Optional[bool] = True