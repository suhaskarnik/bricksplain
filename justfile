serve:
    uv run bricksplain

test:
    uv run pytest

lint:
    uv run ruff check .

fmt:
    uv run ruff format .

# Serve with logs inside the project so an AI assistant can read them.
serve-debug:
    BRICKSPLAIN_LOG_LLM_RESPONSES=1 BRICKSPLAIN_LOG_PATH=.logs uv run bricksplain

# Live evaluation against the real configured provider. Not part of `just test`.
eval:
    uv run python -m evals.run
