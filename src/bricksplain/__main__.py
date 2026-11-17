import uvicorn

from .app import create_app


def main() -> None:
    # Localhost only: never expose the app beyond this machine.
    uvicorn.run(create_app(), host="127.0.0.1", port=8000)


if __name__ == "__main__":
    main()
