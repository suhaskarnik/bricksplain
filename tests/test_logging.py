import logging
from datetime import datetime

import pytest

from bricksplain.config import Config, ConfigError
from bricksplain.logging_setup import setup_logging

SECRET = "super-secret-key-value"
NOW = datetime(2026, 11, 17, 9, 5, 7)


@pytest.fixture
def cfg():
    return Config("groq", "m", SECRET)


@pytest.fixture(autouse=True)
def _reset_logger():
    yield
    for name in ("bricksplain", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        for h in list(logger.handlers):
            h.close()
            logger.removeHandler(h)
    logging.getLogger("bricksplain").setLevel(logging.NOTSET)
    logging.getLogger("bricksplain").propagate = True


def start(cfg, tmp_path, **env):
    env.setdefault("HOME", str(tmp_path / "home"))
    return setup_logging(cfg, env, now=NOW)


def test_log_file_named_from_start_time(cfg, tmp_path):
    path = start(cfg, tmp_path, BRICKSPLAIN_LOG_PATH=str(tmp_path / "logs"))
    assert path == tmp_path / "logs" / "log_20261117_090507.log"
    assert path.exists()


def test_override_directory_wins_over_xdg_and_home(cfg, tmp_path):
    path = start(
        cfg,
        tmp_path,
        BRICKSPLAIN_LOG_PATH=str(tmp_path / "override"),
        XDG_STATE_HOME=str(tmp_path / "xdg"),
    )
    assert path.parent == tmp_path / "override"


def test_xdg_state_home_used_when_no_override(cfg, tmp_path):
    path = start(cfg, tmp_path, XDG_STATE_HOME=str(tmp_path / "xdg"))
    assert path.parent == tmp_path / "xdg" / "bricksplain"


def test_home_fallback_when_nothing_else_set(cfg, tmp_path):
    path = start(cfg, tmp_path)
    assert path.parent == tmp_path / "home" / ".local" / "state" / "bricksplain"


def test_empty_variables_are_treated_as_unset(cfg, tmp_path):
    path = start(cfg, tmp_path, BRICKSPLAIN_LOG_PATH="", XDG_STATE_HOME="")
    assert path.parent == tmp_path / "home" / ".local" / "state" / "bricksplain"


def test_default_level_is_info_and_log_level_overrides(cfg, tmp_path):
    log = logging.getLogger("bricksplain.test")
    path = start(cfg, tmp_path, BRICKSPLAIN_LOG_PATH=str(tmp_path / "a"))
    log.debug("quiet-debug")
    log.info("loud-info")
    text = path.read_text()
    assert "loud-info" in text and "quiet-debug" not in text

    path = start(
        cfg, tmp_path, BRICKSPLAIN_LOG_PATH=str(tmp_path / "b"), LOG_LEVEL="DEBUG"
    )
    log.debug("now-visible")
    assert "now-visible" in path.read_text()


def test_configured_key_value_never_appears_in_log(cfg, tmp_path):
    log = logging.getLogger("bricksplain.test")
    path = start(cfg, tmp_path, BRICKSPLAIN_LOG_PATH=str(tmp_path / "l"))
    log.info("calling with key %s", SECRET)
    log.info(f"fstring {SECRET}")
    try:
        raise RuntimeError(f"boom {SECRET}")
    except RuntimeError:
        log.exception("failed")
    assert SECRET not in path.read_text()


@pytest.mark.parametrize(
    "leak",
    [
        "Bearer abc.def-123",
        "gsk_AbCdEf1234567890",
        "sk-or-v1-0123456789abcdef",
    ],
)
def test_key_shaped_strings_are_redacted(cfg, tmp_path, leak):
    path = start(cfg, tmp_path, BRICKSPLAIN_LOG_PATH=str(tmp_path / "l"))
    logging.getLogger("bricksplain.test").info("header: %s", f"Authorization: {leak}")
    text = path.read_text()
    assert leak.split()[-1] not in text
    assert "header" in text


def test_llm_response_bodies_only_logged_with_explicit_opt_in(cfg, tmp_path):
    log = logging.getLogger("bricksplain.test")
    path = start(
        cfg,
        tmp_path,
        BRICKSPLAIN_LOG_PATH=str(tmp_path / "off"),
        LOG_LEVEL="DEBUG",
    )
    log.debug("body-text", extra={"llm_response": True})
    assert "body-text" not in path.read_text()

    path = start(
        cfg,
        tmp_path,
        BRICKSPLAIN_LOG_PATH=str(tmp_path / "on"),
        LOG_LEVEL="DEBUG",
        BRICKSPLAIN_LOG_LLM_RESPONSES="1",
    )
    log.debug("body-text", extra={"llm_response": True})
    assert "body-text" in path.read_text()


def test_restarting_does_not_duplicate_lines(cfg, tmp_path):
    start(cfg, tmp_path, BRICKSPLAIN_LOG_PATH=str(tmp_path / "x"))
    path = start(cfg, tmp_path, BRICKSPLAIN_LOG_PATH=str(tmp_path / "y"))
    logging.getLogger("bricksplain.test").info("once")
    assert path.read_text().count("once") == 1


def test_invalid_log_level_is_a_clear_startup_error(cfg, tmp_path):
    with pytest.raises(ConfigError, match="LOG_LEVEL"):
        start(cfg, tmp_path, BRICKSPLAIN_LOG_PATH=str(tmp_path / "l"), LOG_LEVEL="loud")


def test_unwritable_location_is_a_clear_startup_error(cfg, tmp_path):
    blocker = tmp_path / "file"
    blocker.write_text("")
    with pytest.raises(ConfigError, match="log file"):
        start(cfg, tmp_path, BRICKSPLAIN_LOG_PATH=str(blocker))


def test_two_starts_in_same_second_get_separate_files(cfg, tmp_path):
    env = {"BRICKSPLAIN_LOG_PATH": str(tmp_path / "l")}
    assert start(cfg, tmp_path, **env) != start(cfg, tmp_path, **env)


def test_relative_xdg_state_home_is_ignored(cfg, tmp_path):
    path = start(cfg, tmp_path, XDG_STATE_HOME="relative/dir")
    assert path.parent == tmp_path / "home" / ".local" / "state" / "bricksplain"


def test_server_errors_reach_the_redacted_log(cfg, tmp_path):
    path = start(cfg, tmp_path, BRICKSPLAIN_LOG_PATH=str(tmp_path / "l"))
    logging.getLogger("uvicorn.error").error("crash %s", SECRET)
    text = path.read_text()
    assert "crash" in text and SECRET not in text
