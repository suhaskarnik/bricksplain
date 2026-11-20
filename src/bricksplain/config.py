"""Configuration resolution: which LLM, and which API key, from `.env` files."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

REASONING_EFFORTS = ("none", "minimal", "low", "medium", "high")

SUPPORT_KEY_NAME = "OPENROUTER_API_KEY"

PROVIDER_KEYS = {
    "groq": "GROQ_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "google": "GOOGLE_API_KEY",
}


class ConfigError(Exception):
    """A startup misconfiguration, worded for the user. Never contains secret values."""


@dataclass(frozen=True)
class Config:
    provider: str
    model: str
    api_key: str = field(repr=False)
    # OpenRouter only: caps hidden "thinking" tokens. None leaves the model default.
    reasoning_effort: str | None = None
    # OpenRouter key for the Support Check's decision model, whatever the provider.
    support_api_key: str = field(default="", repr=False)
    # Opt-in: BRICKSPLAIN_SUPPORT_CHECK=1 in the working directory .env.
    support_check: bool = False


def _model_error(detail: str) -> ConfigError:
    providers = ", ".join(PROVIDER_KEYS)
    return ConfigError(
        f"BRICKSPLAIN_MODEL {detail}. Set it in the .env in the working directory "
        f"as <provider>/<model id>, where provider is one of: {providers}."
    )


def _resolve_model(cwd_env: Mapping[str, str | None]) -> tuple[str, str]:
    raw = cwd_env.get("BRICKSPLAIN_MODEL") or ""
    if not raw:
        raise _model_error("is not set")
    provider, slash, model = raw.partition("/")
    if not slash:
        raise _model_error("must contain a slash between provider and model id")
    if provider not in PROVIDER_KEYS:
        raise _model_error("has an unknown provider")
    if not model:
        raise _model_error("is missing the model id after the slash")
    return provider, model


def load_config(cwd: Path, environ: Mapping[str, str]) -> Config:
    cwd_env = dotenv_values(cwd / ".env", interpolate=False)
    provider, model = _resolve_model(cwd_env)
    key_name = PROVIDER_KEYS[provider]
    effort = (cwd_env.get("BRICKSPLAIN_REASONING_EFFORT") or "").strip().lower() or None
    if effort is not None and effort not in REASONING_EFFORTS:
        raise ConfigError(
            f"BRICKSPLAIN_REASONING_EFFORT must be one of: {', '.join(REASONING_EFFORTS)}."
        )
    sources = []
    if central := environ.get("LLM_PROVIDERS"):
        sources.append(
            dotenv_values(Path(central).expanduser() / ".env", interpolate=False)
        )
    sources.append(cwd_env)

    def find(name: str) -> str | None:
        return next((v[name] for v in sources if v.get(name)), None)

    where = (
        "Put it in the .env under the directory named by LLM_PROVIDERS, "
        "or in the .env in the working directory."
    )
    api_key = find(key_name)
    if api_key is None:
        raise ConfigError(f"{key_name} is not set. {where}")
    enabled = (cwd_env.get("BRICKSPLAIN_SUPPORT_CHECK") or "").strip().lower() in (
        "1",
        "true",
        "yes",
        "on",
    )
    support_key = find(SUPPORT_KEY_NAME)
    if not enabled:
        return Config(provider, model, api_key, effort, support_key or "", False)
    if support_key is None:
        raise ConfigError(
            f"{SUPPORT_KEY_NAME} is not set. The Support Check's decision model is "
            f"only available on OpenRouter, whichever provider writes the docs. {where}"
        )
    return Config(provider, model, api_key, effort, support_key, True)
