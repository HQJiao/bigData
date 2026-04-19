import uuid
from datetime import datetime
from sqlalchemy import Column, String, Text, BigInteger, JSON, DateTime
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Document(Base):
    __tablename__ = "documents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512))
    content = Column(Text)
    status = Column(String(20), default="pending")
    error_message = Column(Text)
    file_size = Column(BigInteger)
    mime_type = Column(String(100))
    parser_type = Column(String(50))

    owner_id = Column(UUID(as_uuid=True))
    owner_group_id = Column(UUID(as_uuid=True))
    access_level = Column(String(20))
    created_by = Column(UUID(as_uuid=True))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_by = Column(UUID(as_uuid=True))
    updated_at = Column(DateTime, onupdate=datetime.utcnow)

    extra_metadata = Column(JSON)
