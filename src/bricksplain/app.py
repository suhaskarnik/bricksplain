import os
from pathlib import Path

from fastapi import FastAPI, Form, HTTPException, Request
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates

from . import notebook as nb
from .audience_doc import to_markdown
from .cache import DocCache
from .config import Config
from .jobs import JobRunner
from .llm import LLMClient, OpenAICompatClient

DEFAULT_PATH = "examples/cash_application_engine.py"
DEFAULT_CACHE_DIR = ".cache/bricksplain"
TEMPLATE_DIR = str(Path(__file__).parent / "templates")


def create_app(
    config: Config,
    default_path: str = DEFAULT_PATH,
    llm_client: LLMClient | None = None,
    cache_dir: Path | None = None,
) -> FastAPI:
    cache_dir = cache_dir or Path(
        os.environ.get("BRICKSPLAIN_CACHE_PATH") or DEFAULT_CACHE_DIR
    )
    cache = DocCache(cache_dir, f"{config.provider}/{config.model}")
    runner = JobRunner(llm_client or OpenAICompatClient(config), cache)
    app = FastAPI(title="Bricksplain")
    templates = Jinja2Templates(directory=TEMPLATE_DIR)
    templates.env.globals["llm_label"] = f"{config.provider} / {config.model}"

    @app.get("/", response_class=HTMLResponse)
    def index(request: Request, path: str | None = None):
        return templates.TemplateResponse(
            request, "index.html", {"path": path or default_path}
        )

    @app.post("/generate", response_class=HTMLResponse)
    def generate(request: Request, path: str = Form(""), regenerate: str = Form("")):
        ctx: dict = {"path": path, "job": None, "error": None}
        try:
            notebook = nb.load(path)
        except nb.NotebookError as e:
            ctx["error"] = str(e)
            return templates.TemplateResponse(request, "index.html", ctx)
        ctx["warnings"] = notebook.warnings
        ctx["job"] = runner.start(path, notebook, regenerate=bool(regenerate))
        return templates.TemplateResponse(request, "index.html", ctx)

    @app.get("/jobs/{job_id}/{audience}", response_class=HTMLResponse)
    def job_doc(request: Request, job_id: str, audience: str):
        job = runner.get(job_id)
        if job is None or audience not in job.docs:
            raise HTTPException(404, "Unknown job or audience.")
        return templates.TemplateResponse(
            request, "_doc.html", {"job": job, "ds": job.docs[audience]}
        )

    @app.get("/jobs/{job_id}/{audience}/download.md")
    def job_markdown(job_id: str, audience: str):
        job = runner.get(job_id)
        ds = job.docs.get(audience) if job else None
        if ds is None or ds.doc is None:
            raise HTTPException(404, "Unknown job or audience, or doc not ready.")
        return Response(
            to_markdown(ds.doc, ds.audience, job.path, ds.coverage),
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="bricksplain-{audience}.md"'
            },
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
