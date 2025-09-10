# from geoalchemy2.shape import from_shape
# from shapely.geometry import Point
# from sqlalchemy import desc
# from db.database_operations import get_tuple_instance, insert_into_table
# from models.log_models import VehicleMonitoringLogs
# from db.db import get_async_db
# from utils.driver_activity_rule_engine import get_driver_activity

# async def update_vehicle_monitoring(vehicle_uuid , driver_uuid):
    
    
#     async for session in get_async_db():
#         prev_vehicle_log = await get_tuple_instance(session ,
#                                                     VehicleMonitoringLogs ,
#                                                     {"vehicle_uuid" : vehicle_uuid},
#                                                     order_by=[desc(VehicleMonitoringLogs.id)],
#                                                     limit = 1
#                                                     )
#         current_activity = await get_driver_activity(session , driver_uuid , None , vehicle_uuid)
#         if prev_vehicle_log and prev_vehicle_log.event == current_activity[1]:
#             await session.commit()
#             await session.close()
#             continue
#         monitoring_data = {
#             vehicle_uuid = Column(String , ForeignKey('vehicle_main.vehile_uuid', ondelete = 'CASCADE'))
#                 driver_uuid = Column(String , ForeignKey('driver_main.driver_uuid' , ondelete = 'SET NULL'))
#                 event = Column(String , nullable = False)
#                 vehicle_lat = Column(DOUBLE_PRECISION)
#                 vehicle_lng = Column(DOUBLE_PRECISION)
#                 vehicle_location = Column(Geometry(geometry_type='POINT', srid=4326))
#                 driver_lat = Column(DOUBLE_PRECISION)
#                 driver_lng = Column(DOUBLE_PRECISION)
#                 driver_location
#         }
#         await insert_into_table(session , VehicleMonitoringLogs , monitoring_data)
#         await session.commit()
#         await session.close()