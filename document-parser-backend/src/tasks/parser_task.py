import tempfile
import uuid
from pathlib import Path

from celery import Task
from sqlalchemy.orm import Session

from src.core.celery import celery_app
from src.core.database import SessionLocal
from src.core.minio import minio_client
from src.core.models import Document
from src.core.logging import get_logger
from src.parsers.registry import parser_registry

logger = get_logger("parser-task")


class CallbackTask(Task):
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        document_id = args[0] if args else None
        logger.error(
            "parser_task_failed",
            extra={"document_id": str(document_id), "error": str(exc)},
        )
        self._update_document_status(document_id, "failed", str(exc))

    def on_success(self, retval, task_id, args, kwargs):
        document_id = args[0] if args else None
        logger.info("parser_task_success", extra={"document_id": str(document_id)})

    def _update_document_status(self, document_id: str, status: str, error_message: str = None):
        db = SessionLocal()
        try:
            document = db.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
            if document:
                document.status = status
                if error_message:
                    document.error_message = error_message
                db.commit()
        finally:
            db.close()


@celery_app.task(bind=True, base=CallbackTask, max_retries=3, default_retry_delay=60)
def parse_document(self, document_id: str):
    logger.info("parse_document_started", extra={"document_id": document_id})

    db = SessionLocal()
    try:
        document = db.query(Document).filter(Document.id == uuid.UUID(document_id)).first()
        if not document:
            logger.error("document_not_found", extra={"document_id": document_id})
            return

        document.status = "processing"
        db.commit()

        file_data = minio_client.download_file(document.file_path)

        with tempfile.NamedTemporaryFile(delete=False, suffix=document.filename) as tmp_file:
            tmp_file.write(file_data)
            tmp_path = Path(tmp_file.name)

        try:
            parsed = parser_registry.parse_file(tmp_path)

            document.content = parsed.text
            document.parser_type = parsed.parser_type
            document.status = "completed"
            document.extra_metadata = parsed.metadata
            db.commit()

            logger.info(
                "document_parsed",
                extra={
                    "document_id": document_id,
                    "parser_type": parsed.parser_type,
                    "content_length": len(parsed.text),
                },
            )
        finally:
            tmp_path.unlink(missing_ok=True)

    except Exception as e:
        logger.error("parse_document_error", extra={"document_id": document_id, "error": str(e)})
        document.status = "failed"
        document.error_message = str(e)
        db.commit()
        raise self.retry(exc=e)
    finally:
        db.close()
