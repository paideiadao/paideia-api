import datetime
import os
import logging
import traceback

from fastapi import APIRouter, Depends
from fastapi.datastructures import UploadFile
from fastapi.param_functions import File
from pydantic import BaseModel
from starlette.responses import JSONResponse
from config import Config, Network  # api specific config
from core.auth import get_current_active_user, get_current_active_superuser
from cache.cache import cache
from aws.s3 import S3
from util.image_optimizer import pillow_image_optimizer
from util.util import generate_slug

CFG = Config[Network]

util_router = r = APIRouter()


def upload_file_s3(key, bytes):
    try:
        bytes.seek(0)
        S3.upload_fileobj(
            bytes, CFG.s3_bucket, key,
            ExtraArgs={'ACL': 'public-read'},
        )
        return True
    except:
        return False


@r.post("/upload_file", name="util:upload-file-to-S3")
def upload(
    fileobject: UploadFile = File(...), current_user=Depends(get_current_active_user)
):
    """
    Upload files to s3 bucket
    """
    try:
        if len(fileobject.file.read()) >= 2097152:
            return JSONResponse(status_code=413, content="file size must be less than 2MB")
        filename = fileobject.filename
        current_time = datetime.datetime.now()
        # split the file name into two different path (string + extention)
        split_file_name = os.path.splitext(filename)
        # for realtime application you must have generate unique name for the file
        file_name_unique = generate_slug(
            split_file_name[0] + "." + str(current_time.timestamp()).replace(".", "")
        )
        file_extension = split_file_name[1]  # file extention
        data = (
            fileobject.file._file
        )  # Converting tempfile.SpooledTemporaryFile to io.BytesIO
        filename_mod = CFG.s3_key + "." + file_name_unique + file_extension
        uploads3 = upload_file_s3(filename_mod, data)
        if uploads3:
            s3_url = f"https://{CFG.s3_bucket}.s3.{CFG.aws_region}.amazonaws.com/{filename_mod}"
            return {"status": "success", "image_url": s3_url}  # response added
        else:
            return JSONResponse(status_code=400, content="failed to upload to S3")
    except Exception as e:
        logging.error(traceback.format_exc())
        return JSONResponse(status_code=400, content=f"ERR::S3_upload_file::{str(e)}")


image_compression_config = {
    "xs": 40,
    "s": 120,
    "m": 240,
    "l": 720,
    "original": None
}


@r.post("/upload_image/{compression_type}", name="util:upload-image-to-S3")
def upload_image(
    compression_type: str, fileobject: UploadFile = File(...), current_user=Depends(get_current_active_user)
):
    """
    Upload images to s3 bucket

    compression_type options (max px for long side): 
    xs: 40px
    s: 120px
    m: 240px
    l: 720px
    original: no compression

    eg: 100 x 200 image with xs compression would be resized to 20 x 40
    """
    try:
        if len(fileobject.file.read()) >= 2097152:
            return JSONResponse(status_code=413, content="file size must be less than 2MB")
        if compression_type not in image_compression_config:
            return JSONResponse(status_code=400, content="invalid compression type")
        if compression_type == "original":
            return upload(fileobject, current_user)
        filename = fileobject.filename
        current_time = datetime.datetime.now()
        split_file_name = os.path.splitext(filename)
        file_name_unique = generate_slug(
            split_file_name[0] + "." + str(current_time.timestamp()).replace(".", "") + "." + compression_type
        )
        file_extension = split_file_name[1]
        if file_extension.lower() not in (".jpeg", ".jpg", ".png"):
            return JSONResponse(status_code=415, content="please upload a jpg or png file")
        data = pillow_image_optimizer.compress(
            fileobject.file._file, image_compression_config[compression_type]
        )
        filename_mod = CFG.s3_key + "." + file_name_unique + file_extension
        uploads3 = upload_file_s3(filename_mod, data)
        if uploads3:
            s3_url = f"https://{CFG.s3_bucket}.s3.{CFG.aws_region}.amazonaws.com/{filename_mod}"
            return {"status": "success", "image_url": s3_url}
        else:
            return JSONResponse(status_code=400, content="failed to upload to S3")
    except Exception as e:
        logging.error(traceback.format_exc())
        return JSONResponse(status_code=400, content=f"ERR::S3_image_file::{str(e)}")


@r.post("/upload_image_markdown", name="util:upload-image-to-S3-markdown")
def upload_image_markdown(
    fileobject: UploadFile = File(...), current_user=Depends(get_current_active_user)
):
    """
    Upload images to s3 bucket for markdown-based text area
    """
    try:
        # l maps to 720px
        ret = upload_image("l", fileobject, current_user)
        if type(ret) == JSONResponse:
            return ret
        return {"status": ret["status"], "filePath": ret["image_url"]}
    except Exception as e:
        logging.error(traceback.format_exc())
        return JSONResponse(status_code=400, content=f"ERR::S3_image_file::{str(e)}")


class InvalidateCacheRequest(BaseModel):
    key: str


@r.post("/force_invalidate_cache", name="util:cache-invalidate")
def forceInvalidateCache(
    req: InvalidateCacheRequest, current_user=Depends(get_current_active_superuser)
):
    try:
        return {"status": "success", "detail": cache.invalidate(req.key)}
    except Exception as e:
        logging.error(traceback.format_exc())
        return JSONResponse(status_code=400, content=f"ERR::invalidate_cache::{str(e)}")
