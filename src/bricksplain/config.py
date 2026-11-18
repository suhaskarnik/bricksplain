"""Configuration resolution: which LLM, and which API key, from `.env` files."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import dotenv_values

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
    sources = []
    if central := environ.get("LLM_PROVIDERS"):
        sources.append(
            dotenv_values(Path(central).expanduser() / ".env", interpolate=False)
        )
    sources.append(cwd_env)
    for values in sources:
        if key := values.get(key_name):
            return Config(provider, model, key)
    raise ConfigError(
        f"{key_name} is not set. Put it in the .env under the directory named by "
        f"LLM_PROVIDERS, or in the .env in the working directory."
    )
