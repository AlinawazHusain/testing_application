from fastapi import APIRouter
from .driver_onboarding_api import driver_onboarding_router
from .driver_account_management_api import driver_account_management_router
from .driver_get_basic_data_api import driver_get_basic_data_router
from .driver_attendance_management_api import driver_attendance_management_router
from .driver_leave_management_api import driver_leave_management_router
from .driver_porter_trips_management_api import driver_porter_trips_management_router
from .driver_task_management_api import driver_task_management_router
from .driver_dashboard_api import driver_dashboard_router
from .driver_hotspot_api import driver_hotspot_router
from .driver_nudges_input_api import driver_nudges_input_router

driver_api_v1_router = APIRouter(tags = ["Driver api v1 router"])

driver_api_v1_router.include_router(driver_onboarding_router, tags=["Driver onboarding api"])
driver_api_v1_router.include_router(driver_account_management_router, tags=["Driver account management api"])
driver_api_v1_router.include_router(driver_get_basic_data_router, tags=["Driver basic data getting api"])
driver_api_v1_router.include_router(driver_attendance_management_router, tags=["Driver atttendance management api"])
driver_api_v1_router.include_router(driver_leave_management_router, tags=["Driver leave management api"])
driver_api_v1_router.include_router(driver_porter_trips_management_router, tags=["Driver porter trips management api"])
driver_api_v1_router.include_router(driver_task_management_router, tags=["Driver task management api"])
driver_api_v1_router.include_router(driver_dashboard_router, tags=["Driver dashboard api"])
driver_api_v1_router.include_router(driver_hotspot_router, tags=["Driver hotspot api"])
driver_api_v1_router.include_router(driver_nudges_input_router, tags=["Driver nudges input api"])