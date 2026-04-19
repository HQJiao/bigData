import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import Response
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from pydantic import BaseModel

MAX_UPLOAD_SIZE = 50 * 1024 * 1024  # 50MB

from src.core.database import get_db, init_db
from src.core.models import Document
from src.core.minio import minio_client
from src.core.logging import get_logger
from src.parsers.registry import parser_registry
from src.tasks.parser_task import parse_document

import src.parsers.docx_parser
import src.parsers.excel_parser
import src.parsers.pdf_parser
import src.parsers.ocr_parser
import src.parsers.eml_parser
import src.parsers.msg_parser
import src.parsers.text_parser

logger = get_logger("api")

app = FastAPI(
    title="文档解析存储系统",
    description="支持多种格式文档上传、解析、存储",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "文档解析存储系统 API"}


@app.on_event("startup")
async def startup_event():
    init_db()

    frontend_dist = Path(__file__).parent.parent.parent.parent / "big-data-frontend" / "dist"
    if frontend_dist.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="static")
        logger.info("frontend_static_files_mounted", extra={"directory": str(frontend_dist)})

    logger.info("application_started")


class DocumentResponse(BaseModel):
    id: str
    filename: str
    status: str
    parser_type: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentDetailResponse(DocumentResponse):
    content: Optional[str] = None
    error_message: Optional[str] = None
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class DocumentListResponse(BaseModel):
    items: list[DocumentResponse]
    total: int


@app.get("/files", response_model=DocumentListResponse)
async def list_documents(
    page: int = 1,
    page_size: int = 20,
    db: Session = Depends(get_db),
):
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20

    total = db.query(Document).count()
    documents = (
        db.query(Document)
        .order_by(Document.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )

    items = [
        DocumentResponse(
            id=str(doc.id),
            filename=doc.filename,
            status=doc.status,
            parser_type=doc.parser_type,
        )
        for doc in documents
    ]

    return DocumentListResponse(items=items, total=total)


@app.post("/files", response_model=DocumentResponse)
async def upload_file(file: UploadFile = File(...), db: Session = Depends(get_db)):
    file_data = await file.read()
    file_size = len(file_data)
    if file_size > MAX_UPLOAD_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds 50MB limit")

    ext = Path(file.filename).suffix.lower()
    if not parser_registry.is_supported(Path(file.filename)):
        logger.warning(
            "unsupported_file_format", extra={"file_name": file.filename, "extension": ext}
        )
        raise HTTPException(status_code=400, detail=f"Unsupported file format: {ext}")

    object_path = minio_client.upload_file(file_data, file.filename)

    document = Document(
        id=uuid.uuid4(),
        filename=file.filename,
        file_path=object_path,
        file_size=file_size,
        mime_type=file.content_type,
        status="pending",
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    parse_document.delay(str(document.id))

    logger.info(
        "file_uploaded",
        extra={
            "document_id": str(document.id),
            "file_name": file.filename,
            "size": file_size,
        },
    )

    return DocumentResponse(
        id=str(document.id),
        filename=document.filename,
        status=document.status,
    )


@app.get("/files/{document_id}", response_model=DocumentDetailResponse)
async def get_document(document_id: str, db: Session = Depends(get_db)):
    try:
        doc_id = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    logger.info("document_retrieved", extra={"document_id": document_id, "status": document.status})

    return DocumentDetailResponse(
        id=str(document.id),
        filename=document.filename,
        status=document.status,
        parser_type=document.parser_type,
        content=document.content,
        error_message=document.error_message,
        file_size=document.file_size,
        mime_type=document.mime_type,
    )


class ContentUpdateRequest(BaseModel):
    content: str


@app.put("/files/{document_id}/content")
async def update_document_content(
    document_id: str,
    body: ContentUpdateRequest,
    db: Session = Depends(get_db),
):
    try:
        doc_id = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    document.content = body.content
    document.status = "completed"
    db.commit()
    db.refresh(document)

    logger.info("document_content_updated", extra={"document_id": document_id})
    return {"message": "Content updated successfully"}


@app.get("/files/{document_id}/content")
async def get_document_content(document_id: str, db: Session = Depends(get_db)):
    try:
        doc_id = uuid.UUID(document_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid document ID")

    document = db.query(Document).filter(Document.id == doc_id).first()
    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    if document.status != "completed":
        raise HTTPException(status_code=400, detail="Document parsing not completed")

    from urllib.parse import quote

    logger.info("document_content_retrieved", extra={"document_id": document_id})

    filename = document.filename.rsplit(".", 1)[0] + ".txt"
    encoded_name = quote(filename)
    return Response(
        content=document.content,
        media_type="text/plain",
        headers={"Content-Disposition": f"attachment; filename*=UTF-8''{encoded_name}"},
    )


@app.get("/health")
async def health_check():
    return {"status": "healthy"}
