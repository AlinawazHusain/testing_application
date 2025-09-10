import asyncio
import json
from sqlalchemy import desc
from Bots.eular_data_bot import update_vehicle
from db.database_operations import get_tuple_instance
from config.environment_configs import KAFKA_BOOTSTRAP_SERVER
from db.db import get_async_db
from models.vehicle_models import VehicleLocation
from aiokafka import AIOKafkaConsumer
from models.can_data_model import CANData
from geoalchemy2.shape import from_shape
from shapely.geometry import Point


serial_number_to_vehile_number_mapping = {
    "CE015AA103250122" : "DL51GD2875",
    "CE015AA103250123" : "DL51GD2881",
    "CE015AA103250131" : "DL51GD2899",
    "CE015AA103250143" : "DL51GD1770",
    "CE015AA104250163" : "DL51GD2880",
    "CE015AA104250176" : "DL51GD0102",
    "CE015AA104250213" : "DL51GD0109",
    "CE015AA104250166" : "DL51GD0164",
    "CE015AA103250145" : "DL51GD3539",
    "CE015AA112240026" : "DL51GD1342",
    "CE015AA103250140" : "DL51GD2804",
    "CE015AA104250196" : "DL1LZ7164"
}




async def consume_can_data():
    def safe_deserializer(m):
        try:
            if not m:
                return None
            return json.loads(m.decode('utf-8'))
        except json.JSONDecodeError as e:
            print(f"[ERROR] Invalid JSON message: {e}")
            return None

    consumer = AIOKafkaConsumer(
        'vehicle-data',
        bootstrap_servers=KAFKA_BOOTSTRAP_SERVER,
        group_id="avaronn_vehicle_data_logger",
        auto_offset_reset='latest',
        enable_auto_commit=True,
        value_deserializer=safe_deserializer
    )

    await consumer.start()
    print("[Kafka] CAN data consumer started")

    try:
        async for msg in consumer:
            if msg.value is None:
                continue

            data = msg.value
            data_to_push = None
            serial_number = data.get("serial_number")
            lat = 0
            lng = 0
            speed = 0
            if serial_number:
                vehicle_number = serial_number_to_vehile_number_mapping.get(serial_number)
                if vehicle_number:
                    lat = data.get("lat")
                    lng = data.get("lng",None)
                    if not lng:
                        lng = data.get("Long")
                    if not lat:
                        lat = data.get("Lat")
                    speed = data.get("Speedometer" , 0.0)
                    odometer = data.get("Odometer_Reading")
                    soc = data.get("SOC")
                    location = from_shape(Point(lng, lat))
                    data_to_push = {
                        "vehicle_number" : vehicle_number,
                        "lat" : lat,
                        "lng" : lng,
                        "location" : location,
                        "speed" : speed,
                        "odometer" : odometer
                    }
                    can_data = {
                        "vehicle_number" : vehicle_number,
                        "soc_value" : soc,
                        "vehicle_speed_value" : speed
                    }
                
            if data_to_push:
                async for session in get_async_db():
                    session.add(VehicleLocation(**data_to_push))
                    session.add(CANData(**can_data))
                    await update_vehicle(session , vehicle_number , speed , lat , lng)
                    await session.commit()
                    await session.close()
    except Exception as e:
        print(f"[Kafka] Consumer Error: {e}")
    finally:
        await consumer.stop()
        print("[Kafka] CAN data consumer stopped")
