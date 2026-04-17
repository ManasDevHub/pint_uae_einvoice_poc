import os
import shutil
from typing import BinaryIO, Optional
import boto3
from botocore.exceptions import ClientError
from app.core.config import settings

class StorageService:
    """
    Unified Storage Service handles files locally or on S3.
    This abstraction allows for zero-cost local development and 
    enterprise AWS S3 production deployment.
    """
    def __init__(self, use_s3: bool = False):
        self.use_s3 = use_s3
        self.local_base = "storage"
        if use_s3:
            self.s3_client = boto3.client(
                's3',
                region_name=settings.aws_region,
                aws_access_key_id=settings.aws_access_key,
                aws_secret_access_key=settings.aws_secret_key
            )
            self.bucket_name = settings.s3_bucket_name

    def upload_file(self, folder: str, filename: str, content: BinaryIO, client_id: str):
        """Uploads a file to /{client_id}/{folder}/{filename}"""
        path = f"clients/{client_id}/{folder}/{filename}"
        
        if self.use_s3:
            try:
                self.s3_client.upload_fileobj(content, self.bucket_name, path)
                return f"s3://{self.bucket_name}/{path}"
            except ClientError as e:
                print(f"S3 Upload Error: {e}")
                return None
        else:
            # Local fallback
            full_path = os.path.join(self.local_base, path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(content)
            return full_path

    def get_file_content(self, folder: str, filename: str, client_id: str) -> Optional[bytes]:
        """Retrieves file bytes from storage."""
        path = f"clients/{client_id}/{folder}/{filename}"
        
        if self.use_s3:
            try:
                obj = self.s3_client.get_object(Bucket=self.bucket_name, Key=path)
                return obj['Body'].read()
            except ClientError:
                return None
        else:
            full_path = os.path.join(self.local_base, path)
            if os.path.exists(full_path):
                with open(full_path, "rb") as f:
                    return f.read()
            return None

# Singleton-like instance
storage_service = StorageService(use_s3=False) # Switch to True in prod
