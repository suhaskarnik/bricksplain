import pytest

from bricksplain.config import ConfigError, load_config


def write_env(directory, **values):
    directory.mkdir(parents=True, exist_ok=True)
    (directory / ".env").write_text("".join(f"{k}={v}\n" for k, v in values.items()))
    return directory


@pytest.fixture
def dirs(tmp_path):
    return tmp_path / "cwd", tmp_path / "central"


def test_model_split_on_first_slash_and_remainder_verbatim(dirs):
    cwd, _central = dirs
    write_env(
        cwd,
        BRICKSPLAIN_MODEL="openrouter/meta-llama/llama-3:free",
        OPENROUTER_API_KEY="k",
    )
    cfg = load_config(cwd, {})
    assert cfg.provider == "openrouter"
    assert cfg.model == "meta-llama/llama-3:free"
    assert cfg.api_key == "k"


def test_model_ignored_in_central_file_and_process_environment(dirs):
    cwd, central = dirs
    write_env(cwd, OPENROUTER_API_KEY="k")
    write_env(central, BRICKSPLAIN_MODEL="groq/x", GROQ_API_KEY="g")
    env = {"LLM_PROVIDERS": str(central), "BRICKSPLAIN_MODEL": "groq/y"}
    with pytest.raises(ConfigError, match="BRICKSPLAIN_MODEL"):
        load_config(cwd, env)


@pytest.mark.parametrize("value", ["gemini/x", "groq", "/x", "groq/"])
def test_bad_model_values_fail_with_clear_message(dirs, value):
    cwd, _ = dirs
    write_env(cwd, BRICKSPLAIN_MODEL=value, GROQ_API_KEY="secret-value")
    with pytest.raises(ConfigError) as e:
        load_config(cwd, {})
    assert "BRICKSPLAIN_MODEL" in str(e.value)
    assert "secret-value" not in str(e.value)


def test_central_key_wins_over_cwd_key(dirs):
    cwd, central = dirs
    write_env(cwd, BRICKSPLAIN_MODEL="groq/m", GROQ_API_KEY="cwd-key")
    write_env(central, GROQ_API_KEY="central-key")
    assert load_config(cwd, {"LLM_PROVIDERS": str(central)}).api_key == "central-key"


def test_key_falls_back_per_key_to_cwd(dirs):
    cwd, central = dirs
    write_env(cwd, BRICKSPLAIN_MODEL="groq/m", GROQ_API_KEY="cwd-key")
    write_env(central, OPENROUTER_API_KEY="other")
    assert load_config(cwd, {"LLM_PROVIDERS": str(central)}).api_key == "cwd-key"


def test_only_selected_providers_key_is_required(dirs):
    cwd, _ = dirs
    write_env(cwd, BRICKSPLAIN_MODEL="groq/m", GROQ_API_KEY="g")
    assert load_config(cwd, {}).provider == "groq"


def test_missing_key_error_names_key_and_leaks_no_values(dirs):
    cwd, central = dirs
    write_env(cwd, BRICKSPLAIN_MODEL="groq/m", OPENROUTER_API_KEY="other-secret")
    write_env(central, SOMETHING="central-secret")
    with pytest.raises(ConfigError) as e:
        load_config(cwd, {"LLM_PROVIDERS": str(central)})
    assert "GROQ_API_KEY" in str(e.value)
    assert "secret" not in str(e.value)


def test_missing_cwd_env_file_is_a_clear_error(dirs):
    cwd, _ = dirs
    with pytest.raises(ConfigError, match="BRICKSPLAIN_MODEL"):
        load_config(cwd, {})


def test_env_interpolation_cannot_pull_model_or_key_from_process_environment(dirs):
    cwd, _ = dirs
    cwd.mkdir(parents=True)
    (cwd / ".env").write_text(
        "BRICKSPLAIN_MODEL=groq/${PROC_MODEL}\nGROQ_API_KEY=${PROC_KEY}\n"
    )
    cfg = load_config(cwd, {"PROC_MODEL": "evil", "PROC_KEY": "leaked"})
    assert cfg.model == "${PROC_MODEL}"
    assert cfg.api_key == "${PROC_KEY}"
