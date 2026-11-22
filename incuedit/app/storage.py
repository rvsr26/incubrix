from __future__ import annotations
import os
from pathlib import Path


def upload_output(path: Path, key: str, content_type: str) -> str | None:
    endpoint=os.getenv("S3_ENDPOINT_URL","").strip()
    if not endpoint:
        return None
    try:
        import boto3
    except ImportError as exc:
        raise RuntimeError("S3 storage is configured but boto3 is not installed.") from exc
    client=boto3.client("s3",endpoint_url=endpoint,aws_access_key_id=os.getenv("S3_ACCESS_KEY","minioadmin"),
                        aws_secret_access_key=os.getenv("S3_SECRET_KEY","minioadmin"),region_name=os.getenv("S3_REGION","us-east-1"))
    bucket=os.getenv("S3_BUCKET","incuedit")
    try: client.head_bucket(Bucket=bucket)
    except Exception: client.create_bucket(Bucket=bucket)
    client.upload_file(str(path),bucket,key,ExtraArgs={"ContentType":content_type})
    return client.generate_presigned_url("get_object",Params={"Bucket":bucket,"Key":key},ExpiresIn=3600)
