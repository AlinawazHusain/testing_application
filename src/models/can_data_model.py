from datetime import datetime, timezone
from sqlalchemy import TIMESTAMP, Column, String, Integer,  BigInteger,  DOUBLE_PRECISION
from .can_data_example import data  
from db.base import Base

def infer_column_type(value):
    if isinstance(value, int):
        if value > 2**31: 
            return BigInteger
        return DOUBLE_PRECISION
    elif isinstance(value, float):
        return DOUBLE_PRECISION
    elif isinstance(value, str):
        return String
    else:
        raise ValueError(f"Unsupported data type: {type(value)}")

def generate_model_class(class_name: str, fields_dict: dict):
    attrs = {
        "__tablename__": class_name.lower(),
        "id": Column(Integer, primary_key=True, index=True),
    }

    for key, val in fields_dict.items():
        val_type = infer_column_type(val)


        attrs[key] = Column(val_type, default = 0.0)
    attrs["created_at"] = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    return type(class_name, (Base,), attrs)

CANData = generate_model_class("can_data", data)