"""Per-start log file with secret redaction. Never logs prompts or Notebook content."""

import errno
import logging
import os
import re
from collections.abc import Mapping
from datetime import datetime
from pathlib import Path

from .config import Config, ConfigError

LOGGER_NAME = "bricksplain"
# Server errors from uvicorn belong in the same (redacted) file.
LOGGER_NAMES = (LOGGER_NAME, "uvicorn.error", "uvicorn.access")
_KEY_SHAPED = re.compile(
    r"\bBearer\s+\S+|\bgsk_[A-Za-z0-9_-]+|\bsk-[A-Za-z0-9_-]+"
    r"|\bxai-[A-Za-z0-9_-]+|\bAIza[A-Za-z0-9_-]+"
)
_MASK = "[REDACTED]"
_MIN_SECRET_LEN = 8  # shorter values would shred ordinary log text


class _RedactingFormatter(logging.Formatter):
    """Redacts the fully formatted text, so tracebacks and %-args are covered too."""

    def __init__(self, secrets: list[str]):
        super().__init__("%(asctime)s %(levelname)s %(name)s: %(message)s")
        self._secrets = [s for s in secrets if len(s) >= _MIN_SECRET_LEN]

    def format(self, record: logging.LogRecord) -> str:
        text = super().format(record)
        for secret in self._secrets:
            text = text.replace(secret, _MASK)
        return _KEY_SHAPED.sub(_MASK, text)


def resolve_log_dir(environ: Mapping[str, str]) -> Path:
    if override := environ.get("BRICKSPLAIN_LOG_PATH"):
        return Path(override).expanduser()
    xdg = environ.get("XDG_STATE_HOME")
    if xdg and Path(xdg).is_absolute():  # the XDG spec says to ignore relative values
        return Path(xdg) / "bricksplain"
    home = Path(environ["HOME"]) if environ.get("HOME") else Path.home()
    return home / ".local" / "state" / "bricksplain"


def _create_log_file(directory: Path, now: datetime) -> Path:
    """Create a private file, never reusing one from an earlier start."""
    stem = f"log_{now:%Y%m%d_%H%M%S}"
    for n in range(100):
        path = directory / (f"{stem}.log" if n == 0 else f"{stem}_{n}.log")
        try:
            os.close(os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600))
            return path
        except FileExistsError:
            continue
    raise OSError(errno.EEXIST, "too many log files for this second")


def setup_logging(
    config: Config, environ: Mapping[str, str], now: datetime | None = None
) -> Path:
    """Start this run's log file and return its path."""
    now = now or datetime.now()
    level = (environ.get("LOG_LEVEL") or "INFO").upper()
    if level not in logging.getLevelNamesMapping():
        raise ConfigError(f"LOG_LEVEL {level!r} is not a valid logging level.")
    directory = resolve_log_dir(environ)
    try:
        directory.mkdir(parents=True, exist_ok=True, mode=0o700)
        path = _create_log_file(directory, now)
    except OSError as e:
        raise ConfigError(f"Cannot create a log file in {directory}: {e.strerror}.")

    handler = logging.FileHandler(path, encoding="utf-8")
    handler.setFormatter(_RedactingFormatter([config.api_key]))
    handler.set_name("bricksplain-file")
    if not environ.get("BRICKSPLAIN_LOG_LLM_RESPONSES"):
        # LLM response bodies (records tagged llm_response) need explicit opt-in.
        handler.addFilter(lambda r: not getattr(r, "llm_response", False))

    for name in LOGGER_NAMES:
        logger = logging.getLogger(name)
        for old in list(logger.handlers):
            if old.get_name() == "bricksplain-file":
                old.close()
                logger.removeHandler(old)
        logger.addHandler(handler)
    app_logger = logging.getLogger(LOGGER_NAME)
    app_logger.setLevel(level)
    app_logger.propagate = False
    return path
