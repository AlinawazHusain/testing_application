from fastapi import APIRouter , Request, Depends,File, Form,UploadFile
from fastapi.templating import Jinja2Templates
from sqlalchemy.ext.asyncio import AsyncSession
from db.db import get_async_db

#  Importing internal modules
from Bots.porter_data_bot import porter_data_handler
from db.db import  get_async_db
from config.exceptions import *
from schemas.basic_schema import AdminLoginRequest
from integrations.aws_utils import upload_file_to_s3
from utils.data_read_utils import read_file


ui_router = APIRouter()

templates = Jinja2Templates(directory="templates")


@ui_router.get("/apiTestingDocs")
async def api_testing_docs(request: Request):
    """Returns API Testing Documentation."""
    return templates.TemplateResponse("apiTesterLogin.html", {"request": request})

@ui_router.post("/getDocs")
async def get_docs(data: AdminLoginRequest, request: Request):
    """Handles API Documentation Login."""
    if data.username == "admin" and data.password == 'root':
        return templates.TemplateResponse("apiPlayground.html", {"request": request, "username": data.username})
    else:
        raise UnauthorizedError("Invalid Admin Credentials")
    
    
    
    

@ui_router.get("/uploadAsset")
async def asset_uploader(request:Request):
    return templates.TemplateResponse("assetsUploader.html" , {"request" : request})

@ui_router.post("/assetUploader")
async def asset_uploader(request: Request, 
                          asset_name: str = Form(...),
                          asset: UploadFile = File(...)):
    UPLOAD_FOLDER_DRIVER = "assets"
    file_extension = asset.filename.split('.')[-1].lower()
    file_path = f"{UPLOAD_FOLDER_DRIVER}/{asset_name}.{file_extension}"
    path_to_s3 = await upload_file_to_s3(asset, file_path)
    
    return templates.TemplateResponse("assetsUploader.html", {"request": request, "path_to_s3": path_to_s3})





@ui_router.get("/getPorterDataUploader")
async def api_testing_docs(request: Request):
    return templates.TemplateResponse("porterDataUploader.html" , {"request" : request})



@ui_router.post("/uploadPorterData")
async def upload_files(order_data: UploadFile = File(...), driver_data: UploadFile = File(...) , session:AsyncSession = Depends(get_async_db)):
    order_df = await read_file(order_data)
    
    driver_df = await read_file(driver_data)
    await porter_data_handler(session , order_df , driver_df)    
    await session.commit()
    await session.close()

    return {"Success" : "YES"}