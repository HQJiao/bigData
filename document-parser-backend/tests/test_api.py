import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from fastapi.testclient import TestClient
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import Base
from src.app.main import app


TEST_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def db_session():
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(db_session):
    from src.core.database import get_db
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_root_endpoint(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


@patch("src.app.main.minio_client")
@patch("src.app.main.parse_document")
def test_upload_file(mock_task, mock_minio, client, db_session):
    mock_minio.upload_file.return_value = "test/path/test.docx"
    mock_task.delay.return_value = None

    files = {"file": ("test.docx", b"test content", "application/vnd.openxmlformats-officedocument.wordprocessingml.document")}
    response = client.post("/files", files=files)

    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert data["filename"] == "test.docx"
    assert data["status"] == "pending"


def test_upload_unsupported_file(client):
    files = {"file": ("test.exe", b"malicious", "application/x-msdownload")}
    response = client.post("/files", files=files)
    assert response.status_code == 400


@patch("src.app.main.minio_client")
def test_get_document_not_found(mock_minio, client, db_session):
    response = client.get("/files/00000000-0000-0000-0000-000000000000")
    assert response.status_code == 404


def test_get_document_invalid_id(client):
    response = client.get("/files/invalid-id")
    assert response.status_code == 400
