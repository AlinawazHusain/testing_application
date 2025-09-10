from pydantic import BaseModel


class Coordinate(BaseModel):
    lat:float
    lng:float
    


class get_hotspot_request(BaseModel):
    driver_lat: float
    driver_lng: float
    
    
class get_hotspot_response(BaseModel):
    start: Coordinate
    end: Coordinate
    distance_meters:float
    distance_text:str
    duration_seconds: float
    duration_text : str
    overview_polyline:str
    overview_navigation : list[Coordinate]
    navigation : list
    hotspot_route_uuid : str