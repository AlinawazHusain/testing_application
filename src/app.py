import asyncio
from contextlib import asynccontextmanager
from os import getenv
from fastapi import  Depends, FastAPI
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
from Bots.attendance_monitoring_bot import monitor_attendances
from Bots.eular_data_bot import eular_data_logger
from Bots.kafka_consume_bot import consume_can_data
from Bots.nudges_bot import monitor_for_nudges
from Bots.telematics_data_bot import start_telematics_data
from config.firebase_config import initialize_firebase
# from db.migrate import run_alembic_migrations
from integrations.appyflow import get_gst_Address
from settings.static_data_settings import initialize_static_data
from ui_routes import ui_router
from db.db import create_db_and_tables, get_async_db
from Bots.attendance_scheduler_bot import attendance_scheduler
from middlewares.request_logging import RequestLoggingMiddleware
from config.exceptions import *
from api.v1.driver_api import driver_api_v1_router
from api.v1.mfo_api import mfo_api_v1_router
# from utils.push_porter_final_data import push_porter_processed_data_into_db
# from sqlalchemy.ext.asyncio import AsyncSession
from utils.time_utils import get_utc_time
from web_sockets.v1.driver_sockets import driver_websocket_v1_router
from web_sockets.v1.mfo_sockets import mfo_websocket_v1_router
import asyncio
from starlette.requests import Request
from dotenv import load_dotenv
from os import getenv
load_dotenv()







"""
Main FastAPI application for Avaronn Backend API.

This FastAPI application serves as the backend for Avaronn, handling multiple routes, background tasks, 
database connections, and middleware configuration. It includes API routes for driver, MFO, vehicle management, 
and attendance and leave management, along with exception handling, CORS configuration, and background job scheduling.

Key Features:
- **Background Scheduler**: Runs scheduled tasks such as the attendance job using `apscheduler`.
- **Database and Firebase Initialization**: Sets up and connects to the database, performs migrations, and initializes Firebase.
- **Exception Handling**: Global exception handlers for different types of errors to maintain a clean response structure.
- **CORS Middleware**: Configured to allow cross-origin resource sharing (CORS) for all origins, methods, and headers.
- **Static File Serving**: Supports serving static files from the `/static` directory.
- **API Routes**: Includes multiple routers for different API functionalities, including drivers, vehicles, MFOs, and more.
- **Lifespan Management**: Defines startup and shutdown logic, ensuring proper initialization of resources and cleanup.

Modules Included:
- `driver_controller`, `mfo_controller`, `vehicle_controller`: Routers for managing drivers, MFOs, and vehicles.
- `attendance_scheduler_bot`: A background job for managing attendance-related tasks.
- `request_logging`: Middleware to log incoming requests.
- `db`: Database operations including table creation, migration, and connection management.
- `api.v1.driver_api.attendance_and_leave_management_api`: Handles attendance and leave management for drivers.
- `sockets`: WebSocket communication for real-time updates.

Startup Process:
1. Initializes Firebase and connects to the database.
2. Creates necessary database tables if they do not already exist.
3. Starts the background scheduler for attendance management.

Shutdown Process:
1. Shuts down the scheduler to ensure all background tasks are gracefully completed.
2. Closes any open database sessions.

Background Jobs:
- The application schedules an attendance job to run at 12:01 AM UTC every day.

"""





#  Background Scheduler
scheduler = BackgroundScheduler(timezone="UTC")
loop = None  

#  Async Attendance Job
async def run_job():
    """Runs the async attendance job."""
    async for session in get_async_db():
        try:
            print("here11")
            await attendance_scheduler(session)
            print("DONE")
            await session.commit()
        except Exception as e:
            print(str(e))
            # logger.error(f"Attendance Job Failed: {e}")
            await session.rollback()
        finally:
            await session.close()

def run_scheduled_job():
    """Schedules the job inside FastAPI's event loop safely."""
    if loop and loop.is_running():
        loop.create_task(run_job()) 



@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles startup and shutdown logic."""
    global loop
    loop = asyncio.get_running_loop() 
    await asyncio.to_thread(initialize_firebase)
    await create_db_and_tables(skip_insertion_static_data=True) #set skip_insertino_static_data to False if want to initialize static data in table 
    # run_alembic_migrations()
    await initialize_static_data()
    asyncio.create_task(consume_can_data())
    asyncio.create_task(eular_data_logger())
    asyncio.create_task(monitor_attendances())
    asyncio.create_task(monitor_for_nudges())
    # if getenv("SERVER") == "PRODUCTION":
    #     asyncio.create_task(start_telematics_data("Avaronn_pull" , "avaronn@123"))
    scheduler.start()
    yield
    scheduler.shutdown(wait=False) 


app = FastAPI(
    lifespan=lifespan,
    title="Avaronn API",
    description="Backend API for Avaronn",
    version="1.0.0",
    docs_url=None,
    redoc_url=None,
    openapi_url="/openapi.json"
)

#  CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


#  Mount Static Files
app.mount("/static", StaticFiles(directory="static"), name="static")



#  Register Exception Handlers
exception_handlers = [
    Exception, DatabaseError, ServiceUnavailableError, InvalidRequestError, 
    UnauthorizedError, ForbiddenError, NotFoundError, ConflictError,
    RateLimitError, TimeoutError, BadGatewayError, InternalServerError,
    UnprocessableEntityError , NoCredentialsError , PartialCredentialsError
]
for exc in exception_handlers:
    app.add_exception_handler(exc, global_exception_handler)


# app.add_middleware(RequestLoggingMiddleware)


@app.middleware("http")
async def add_custom_param(request: Request, call_next):
    """
    Add API execution start time to calculate execution time 
    for meta in response.

    Args:
        request (Request): FastAPI Request Object.
        call_next (_type_): requested API.

    Returns:
        response : Response from the API.
    """
    request.state.start_time = get_utc_time()
    response = await call_next(request)
    return response






#v1 Apis
app.include_router(driver_api_v1_router , prefix = '/v1/driver')
app.include_router(driver_websocket_v1_router , prefix = '/v1/driver')

app.include_router(mfo_api_v1_router , prefix = '/v1/mfo')
app.include_router(mfo_websocket_v1_router , prefix = '/v1/mfo')








# @app.get("/" , include_in_schema=False)
# async def makeAttendances(session:AsyncSession = Depends(get_async_db)):
#     # title = "Vehicle Update"
#     # message = f"Your server just started"
#     # send_fcm_notification("fxtNWAFXSmChJfreY_7rZt:APA91bHkztMTv_Pq44ijqmZBT41Xw8aGF9PPl2yrI5HJ3nGPVF04rzseL9i628V5Fcc0k5H103Hsc2QXy6UqJd5E1XZtMylQKK__GppIgzmpQlzEgseb6gw",title , message)
#     # await run_job()
#     # attestr_data = await get_gst_Address("O7AAQFT4346N1ZF")
#     # print(attestr_data)
#     # await push_porter_processed_data_into_db(session)
#     return "Done"

@app.get("/")
async def root():
    return JSONResponse(content={"message": "App is running"}, status_code=200)

@app.get("/healthCheck")
async def health_check():
    return JSONResponse(content={"status": "ok"}, status_code=200)

app.include_router(ui_router)

#  Schedule Attendance Job
scheduler.add_job(run_scheduled_job, "cron", hour=0, minute=1)
