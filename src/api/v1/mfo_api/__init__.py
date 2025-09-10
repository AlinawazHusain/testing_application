from fastapi import APIRouter
from .mfo_onboarding_api import mfo_onboarding_router
from .mfo_account_management_api import mfo_account_management_router
from .mfo_get_basic_data_api import mfo_get_basic_data_router
from .mfo_vehicle_management_api import mfo_vehicle_management_router
from .mfo_driver_management_api import mfo_driver_management_router
from .mfo_leave_management_api import mfo_leave_management_router
from .mfo_get_porter_pnl_api import mfo_get_porter_pnl_router
from .mfo_pettyexpense_api import mfo_pettyexpense_router
from .mfo_hub_management_api import mfo_hub_management_router

mfo_api_v1_router = APIRouter(tags = ["MFO api v1 router"])


mfo_api_v1_router.include_router(mfo_onboarding_router , tags=["MFO onboarding api"])
mfo_api_v1_router.include_router(mfo_account_management_router , tags=["MFO account management api"])
mfo_api_v1_router.include_router(mfo_get_basic_data_router , tags=["MFO basic data getting api"])
mfo_api_v1_router.include_router(mfo_vehicle_management_router , tags=["MFO vehicle management api"])
mfo_api_v1_router.include_router(mfo_driver_management_router , tags=["MFO driver management api"])
mfo_api_v1_router.include_router(mfo_leave_management_router , tags=["MFO drivers leave management api"])
mfo_api_v1_router.include_router(mfo_get_porter_pnl_router , tags=["MFO porter PnL getting api"])
mfo_api_v1_router.include_router(mfo_pettyexpense_router , tags=["MFO Petty Expense api"])
mfo_api_v1_router.include_router(mfo_hub_management_router , tags=["MFO Hub managementapi"])