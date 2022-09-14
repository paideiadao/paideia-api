import datetime
import os

from fastapi import APIRouter, Depends
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from pydantic import BaseModel
from starlette.responses import JSONResponse
from config import Config, Network  # api specific config
from core.auth import get_current_active_user, get_current_active_superuser
from cache.cache import cache
from aws.s3 import S3

CFG = Config[Network]

util_router = r = APIRouter()

@r.post("/upload_file", name="util:upload-file-to-S3")
def upload(fileobject: UploadFile = File(...), current_user=Depends(get_current_active_user)):
    """
    Upload files to s3 bucket
    """
    try:
        filename = fileobject.filename
        current_time = datetime.datetime.now()
        # split the file name into two different path (string + extention)
        split_file_name = os.path.splitext(filename)
        # for realtime application you must have genertae unique name for the file
        file_name_unique = split_file_name[0] + "." + \
            str(current_time.timestamp()).replace('.', '')
        file_extension = split_file_name[1]  # file extention
        data = fileobject.file._file  # Converting tempfile.SpooledTemporaryFile to io.BytesIO
        filename_mod = CFG.s3Key + "." + file_name_unique + file_extension
        uploads3 = S3.Bucket(CFG.s3Bucket).put_object(
            Key=filename_mod, Body=data, ACL='public-read')
        if uploads3:
            s3_url = f"https://{CFG.s3Bucket}.s3.{CFG.awsRegion}.amazonaws.com/{filename_mod}"
            return {"status": "success", "image_url": s3_url}  # response added
        else:
            return JSONResponse(status_code=400, content="Failed to upload to S3")
    except Exception as e:
        return JSONResponse(status_code=400, content=f"ERR::S3_upload_file::{str(e)}")


class InvalidateCacheRequest(BaseModel):
    key: str


@r.post("/force_invalidate_cache", name="util:cache-invalidate")
def forceInvalidateCache(req: InvalidateCacheRequest, current_user=Depends(get_current_active_superuser)):
    try:
        return {'status': 'success', 'detail': cache.invalidate(req.key)}
    except Exception as e:
        return JSONResponse(status_code=400, content=f"ERR::invalidate_cache::{str(e)}")
