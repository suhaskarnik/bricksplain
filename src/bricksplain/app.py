from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from . import notebook as nb

DEFAULT_PATH = "testdata/cash_application_engine.py"
templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))


def create_app(default_path: str = DEFAULT_PATH) -> FastAPI:
    app = FastAPI(title="Bricksplain")

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, path: str | None = None):
        return templates.TemplateResponse(
            request, "index.html", {"path": path or default_path}
        )

    @app.get("/source", response_class=HTMLResponse)
    def source(
        request: Request,
        path: str = "",
        cell: str | None = None,
        start: str | None = None,
        end: str | None = None,
    ):
        ctx: dict = {"path": path, "notebook": None, "error": None, "message": None}
        try:
            notebook = nb.load(path)
        except nb.NotebookError as e:
            ctx["error"] = str(e)
            return templates.TemplateResponse(request, "source.html", ctx)

        ctx["notebook"] = notebook
        highlight, ctx["message"] = notebook.resolve_line_range(cell, start, end)
        ctx["highlight"] = highlight
        ctx["first_highlight"] = min(highlight) if highlight else None
        return templates.TemplateResponse(request, "source.html", ctx)

    return app
