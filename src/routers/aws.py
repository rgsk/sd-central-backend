import re
from enum import Enum

import boto3
from botocore.config import Config
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from lib.env import env

s3 = boto3.client(
    "s3",
    region_name=env.AWS_REGION,
    aws_access_key_id=env.AWS_ACCESS_KEY,
    aws_secret_access_key=env.AWS_SECRET_ACCESS_KEY,
    config=Config(signature_version="s3v4"),
)


router = APIRouter(prefix="/aws", tags=["aws"])


class S3Access(str, Enum):
    PUBLIC = "public"
    PRIVATE = "private"


class UploadQuery(BaseModel):
    key: str
    access: S3Access = S3Access.PRIVATE


class UrlQuery(BaseModel):
    url: str


s3_url_re = re.compile(
    r"^https://(?P<bucket>[\w.-]+)\.s3(?:\.(?P<region>[\w-]+))?\.amazonaws\.com/(?P<key>.+)$"
)


def parse_s3_url(url: str):
    m = s3_url_re.match(url)
    if not m:
        raise HTTPException(status_code=400, detail="Invalid S3 URL")
    return m.group("bucket"), m.group("key")


@router.get("/upload-url")
def get_upload_url(q: UploadQuery = Depends()):
    bucket = env.AWS_PUBLIC_BUCKET if q.access == S3Access.PUBLIC else env.AWS_PRIVATE_BUCKET
    url = s3.generate_presigned_url(
        "put_object",
        Params={"Bucket": bucket, "Key": q.key},
        ExpiresIn=3600,
    )
    return {"url": url}


@router.get("/download-url")
def get_download_url(q: UrlQuery = Depends()):
    bucket, key = parse_s3_url(q.url.split("?")[0])
    url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=86400,
    )
    return {"url": url}


@router.delete("/s3-url")
def delete_s3_url(q: UrlQuery = Depends()):
    bucket, key = parse_s3_url(q.url.split("?")[0])
    s3.delete_object(Bucket=bucket, Key=key)
    return {"status": "deleted", "bucket": bucket, "key": key}
