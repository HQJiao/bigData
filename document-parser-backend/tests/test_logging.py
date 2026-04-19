import pytest
import logging
import json
from io import StringIO

from src.core.logging import setup_logging, get_logger


def test_setup_logging():
    logger = setup_logging("test-logger", level=logging.INFO)
    assert logger.name == "test-logger"
    assert logger.level == logging.INFO


def test_get_logger():
    logger = get_logger("test")
    assert logger.name == "document-parser.test"


def test_json_logging():
    logger = logging.getLogger("test-json")
    logger.setLevel(logging.INFO)
    
    stream = StringIO()
    handler = logging.StreamHandler(stream)
    handler.setFormatter(logging.Formatter('%(message)s'))
    logger.addHandler(handler)
    
    logger.info("test message")
    
    output = stream.getvalue()
    assert "test message" in output
