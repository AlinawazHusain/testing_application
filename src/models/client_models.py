from sqlalchemy import TIMESTAMP, Column, Integer, String, Sequence, text
from db.base import Base 
from datetime import datetime , timezone

class ClientMain(Base):
    __tablename__ = 'client_main'
    # Sequence for generating client IDs
    client_seq = Sequence('client_seq', start=1, increment=1, metadata=Base.metadata)

    # Defining the columns of the table
    id = Column(Integer, primary_key=True, index=True)
    client_uuid = Column(String, unique=True, index = True,server_default=text("'CLI-' || nextval('client_seq'::regclass)"))
    name = Column(String, nullable=True)
    phone_number = Column(String)
    email = Column(String)
    billing_address = Column(String)
    added = Column(String)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    last_updated_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None), onupdate=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    

