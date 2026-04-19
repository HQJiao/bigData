import uuid
from io import BytesIO
from typing import Optional
from minio import Minio
from minio.error import S3Error
from pydantic_settings import BaseSettings

from src.core.logging import get_logger

logger = get_logger("minio")


class Settings(BaseSettings):
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket: str = "documents"
    minio_secure: bool = False

    class Config:
        env_file = ".env"


settings = Settings()


class MinioClient:
    def __init__(self):
        self._client = None
        self.bucket = settings.minio_bucket

    @property
    def client(self) -> Minio:
        if self._client is None:
            self._client = Minio(
                settings.minio_endpoint,
                access_key=settings.minio_access_key,
                secret_key=settings.minio_secret_key,
                secure=settings.minio_secure,
            )
            self._create_bucket_if_not_exists()
        return self._client

    def _create_bucket_if_not_exists(self) -> None:
        try:
            if not self._client.bucket_exists(self.bucket):
                self._client.make_bucket(self.bucket)
                logger.info("bucket_created", extra={"bucket": self.bucket})
        except S3Error as e:
            logger.error("bucket_creation_failed", extra={"error": str(e)})
            raise

    def upload_file(self, file_data: bytes, filename: str) -> str:
        object_name = f"{uuid.uuid4()}/{filename}"
        try:
            self.client.put_object(
                self.bucket,
                object_name,
                BytesIO(file_data),
                length=len(file_data),
            )
            logger.info("file_uploaded", extra={"object_name": object_name, "size": len(file_data)})
            return object_name
        except S3Error as e:
            logger.error("file_upload_failed", extra={"error": str(e), "file_name": filename})
            raise

    def download_file(self, object_name: str) -> bytes:
        try:
            response = self.client.get_object(self.bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info("file_downloaded", extra={"object_name": object_name})
            return data
        except S3Error as e:
            logger.error("file_download_failed", extra={"error": str(e), "object_name": object_name})
            raise

    def delete_file(self, object_name: str) -> None:
        try:
            self.client.remove_object(self.bucket, object_name)
            logger.info("file_deleted", extra={"object_name": object_name})
        except S3Error as e:
            logger.error("file_delete_failed", extra={"error": str(e), "object_name": object_name})
            raise


minio_client = MinioClient()
