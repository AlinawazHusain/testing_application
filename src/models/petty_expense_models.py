from datetime import datetime, timezone
from sqlalchemy import DOUBLE_PRECISION, Boolean, Column, Integer, Sequence, String, TIMESTAMP, ForeignKey, text
from db.base import Base

class PettyExpenses(Base):
    __tablename__ = 'petty_expenses'
    
    petty_expense_seq = Sequence('petty_expense_seq', start=1, increment=1, metadata=Base.metadata)
    
    id = Column(Integer, primary_key=True, index=True)
    petty_expense_uuid = Column(String, unique=True, nullable=False, index=True,server_default=text("'PETTY_EXPENSE-' || nextval('petty_expense_seq'::regclass)"))
    mfo_uuid = Column(String , ForeignKey('mfo_main.mfo_uuid' , ondelete = 'SET NULL'))
    driver_uuid = Column(String, ForeignKey('driver_main.driver_uuid', ondelete="SET NULL"), nullable=True)
    vehicle_uuid = Column(String, ForeignKey('vehicle_main.vehicle_uuid', ondelete="SET NULL"), nullable=True)
    expense_currency = Column(String , default = 'INR')
    expense = Column(DOUBLE_PRECISION , nullable = False)
    expense_description = Column(String , nullable = True)
    expense_date = Column(TIMESTAMP , nullable = False)
    created_at = Column(TIMESTAMP, nullable=False, default=lambda: datetime.now(timezone.utc).replace(tzinfo=None))
    is_enable = Column(Boolean , default = True)
    disabled_at = Column(TIMESTAMP , nullable = True)