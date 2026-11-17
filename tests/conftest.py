from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bricksplain.app import create_app

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def client(fixtures) -> TestClient:
    return TestClient(create_app(default_path=str(fixtures / "small.py")))
