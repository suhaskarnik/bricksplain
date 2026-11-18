from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from bricksplain.app import create_app
from bricksplain.config import Config

FIXTURES = Path(__file__).parent / "fixtures"


@pytest.fixture(autouse=True)
def _isolated_cache(tmp_path, monkeypatch):
    monkeypatch.setenv("BRICKSPLAIN_CACHE_PATH", str(tmp_path / "cache"))


@pytest.fixture
def fixtures() -> Path:
    return FIXTURES


@pytest.fixture
def client(fixtures) -> TestClient:
    return TestClient(
        create_app(
            Config("groq", "llama-3.3-70b", "test-key"),
            default_path=str(fixtures / "small.py"),
        )
    )
