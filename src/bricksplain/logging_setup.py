"""Per-start log file with secret redaction. Never logs prompts or Notebook content."""

import logging
import re
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from .config import Config

LOGGER_NAME = "bricksplain"
_KEY_SHAPED = re.compile(
    r"Bearer\s+\S+|\bgsk_[A-Za-z0-9]+|\bsk-[A-Za-z0-9_-]+", re.IGNORECASE
)
_MASK = "[REDACTED]"


class _RedactingFormatter(logging.Formatter):
    """Redacts the fully formatted text, so tracebacks and %-args are covered too."""

    def __init__(self, secrets: list[str]):
        super().__init__("%(asctime)s %(levelname)s %(name)s: %(message)s")
        self._secrets = [s for s in secrets if s]

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        for secret in self._secrets:
            text = text.replace(secret, _MASK)
        return _KEY_SHAPED.sub(_MASK, text)


def resolve_log_dir(environ: Mapping[str, str]) -> Path:
    if override := environ.get("BRICKSPLAIN_LOG_PATH"):
        return Path(override).expanduser()
    if xdg := environ.get("XDG_STATE_HOME"):
        return Path(xdg) / "bricksplain"
    home = Path(environ["HOME"]) if environ.get("HOME") else Path.home()
    return home / ".local" / "state" / "bricksplain"


def setup_logging(
    config: Config, environ: Mapping[str, str], now: datetime | None = None
) -> Path:
    """Start this run's log file and return its path."""
    now = now or datetime.now()
    directory = resolve_log_dir(environ)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"log_{now:%Y%m%d_%H%M%S}.log"

    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(_RedactingFormatter([config.api_key]))
    if not environ.get("BRICKSPLAIN_LOG_LLM_RESPONSES"):
        # LLM response bodies (records tagged llm_response) need explicit opt-in.
        handler.addFilter(lambda r: not getattr(r, "llm_response", False))

    logger = logging.getLogger(LOGGER_NAME)
    for old in list(logger.handlers):
        old.close()
        logger.removeHandler(old)
    logger.addHandler(handler)
    logger.setLevel((environ.get("LOG_LEVEL") or "INFO").upper())
    logger.propagate = False
    return path
