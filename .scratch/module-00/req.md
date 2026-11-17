Problem Statement: Some teams have Databricks notebooks that work but that they don't understand: no comments, cryptic names, rules scattered across cells. The file `testdata/cash_application_engine.py` is one of them. It allocates incoming bank receipts to open invoices.

I want to build a localhost-hosted web app as a portfolio project. The user will point it at a local file (hardcode default this to the same `cash_application_engine.py`). It must generate 3 docs tailored to the following audiences:

- a non-technical manager: a business explanation of the notebook logic, along with potential issues
- a new developer: acts as an onboarding guide and explains the notebook structure, the data flows and the business rules
- an AI coding agent: purpose, invariants, risky areas, and how to verify that changes are safe. In this doc, favor conciseness. Sacrifice grammar for terseness, but do not compromise on accuracy and correctness.

Every factual claim MUST cite the cell and line(s), and provide a link that navigates to that cell and highlights the line(s). 

Document the purpose and design decisions in `README.md`

The cwd's `.env` file should allow choosing a model. The model MUST have the naming convention `<provider>/<model_name_in_groq>`, where provider can be `openrouter` or `groq`.

# LLM Providers

The API Keys are in the `.env` file, and are called GROQ_API_KEY and OPENROUTER_API_KEY. Use the following fallback chain to locate the `.env` file, in this order

- `$LLM_PROVIDERS/.env`, where LLM_PROVIDERS is an env var 
- `.env` in the cwd

Model choice itself sits strictly in the cwd's `.env`. The reason is that I develop multiple LLM-dependent apps on this machine. I want to keep the LLM Provider configs centralised, but let each app choose its own model

Cache the LLM responses based on the hash of the sys prompt, file hash and model name. That way, I don't need to pay if I'm testing the same file twice against the same model

Evals: separate the eval suite from the deterministic test suite/fixtures. That way, I can test the deterministic parts independently without having to pay for LLM tokens. 

# Logging

Use file based logging. Log file location is chosen as:

- `$BRICKSPLAIN_LOG_PATH`
- `$XDG_LOCAL_STATE/bricksplain/`
- `$HOME/.local/state/bricksplain/`

logfile can be named as `log_YYYYMMDD_hhmmss` according to the app start time. Log all LLM failures, rate limits. 
Default logging level is INFO.

# Coding standards

Python, with `uv` for package management. Prefer `uv add` over `pip ...` commands
Use a modern `src` layout, and during dev use editable installs. 

Use `just` recipes for commonly used commands like starting the server, testing etc

All system prompts MUST be stored in a dedicated directory and treated like code. Do NOT hardcode system prompts, load at runtime.

# Access

You are running in a Docker container, and do not have access to my home directory. For anything that you need to do/check on my host machine, ask me. 
