import os
import sys
from pathlib import Path

import uvicorn

from .app import create_app
from .config import ConfigError, load_config
from .logging_setup import setup_logging


def main() -> None:
    try:
        config = load_config(Path.cwd(), os.environ)
    except ConfigError as e:
        sys.exit(f"Configuration error: {e}")
    try:
        log_path = setup_logging(config, os.environ)
    except ConfigError as e:
        sys.exit(f"Configuration error: {e}")
    print(f"Logging to {log_path}")
    # Localhost only: never expose the app beyond this machine.
    uvicorn.run(create_app(config), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
