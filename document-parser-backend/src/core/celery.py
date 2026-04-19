from celery import Celery
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    redis_url: str = "redis://localhost:6379/0"

    class Config:
        env_file = ".env"


settings = Settings()

celery_app = Celery(
    "document-parser",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["src.tasks.parser_task"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

import src.parsers.docx_parser
import src.parsers.excel_parser
import src.parsers.pdf_parser
import src.parsers.ocr_parser
import src.parsers.eml_parser
import src.parsers.msg_parser
import src.parsers.text_parser
