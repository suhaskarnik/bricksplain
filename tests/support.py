"""Shared helpers: drive Generate over HTTP and wait for every tab to finish."""

import re
import time
from types import SimpleNamespace

from fastapi.testclient import TestClient

from bricksplain.app import create_app
from bricksplain.audience_doc import AUDIENCE_BY_KEY, load_prompt
from bricksplain.config import Config

EMPTY = "{}"


class AllSupported:
    """A SupportJudge that backs every Claim."""

    def score(self, claim, quotes):
        return 1.0


def panel_ids(page: str) -> list[tuple[str, str]]:
    return re.findall(r'data-job="(\w+)" data-audience="(\w+)"', page)


def panel(client: TestClient, job: str, audience: str) -> str:
    return client.get(f"/jobs/{job}/{audience}").text


def wait_done(
    client: TestClient, page: str, timeout: float = 10.0, only: tuple[str, ...] = ()
) -> dict[str, str]:
    """Poll every panel until it is done or failed; return html per audience."""
    deadline = time.monotonic() + timeout
    out = {}
    for job, aud in panel_ids(page):
        if only and aud not in only:
            continue
        while True:
            html = panel(client, job, aud)
            if 'data-doc-state="done"' in html or 'data-doc-state="failed"' in html:
                out[aud] = html
                break
            assert time.monotonic() < deadline, f"{aud} never finished"
            time.sleep(0.01)
    return out


def generate(client: TestClient, path: str, **form: str):
    """POST /generate, wait for all docs, return a response whose text has everything."""
    r = client.post("/generate", data={"path": path, **form})
    docs = wait_done(client, r.text)
    return SimpleNamespace(
        status_code=r.status_code,
        page=r.text,
        docs=docs,
        text=r.text + "".join(docs.values()),
    )


def llm_for(audience_key: str, llm):
    """Route only one Audience's calls to `llm`; the others get an empty doc."""
    return Only(AUDIENCE_BY_KEY[audience_key].prompt, llm)


class Only:
    def __init__(self, prompt_name: str, llm):
        self._system = load_prompt(prompt_name)
        self._llm = llm

    def complete(self, system: str, user: str) -> str:
        if system == self._system:
            return self._llm.complete(system, user)
        return EMPTY

    def score(self, claim, quotes):
        return 1.0


def make_client(config_llm, path: str) -> TestClient:
    """The fake LLM doubles as the SupportJudge when it has a `score` method."""
    return TestClient(
        create_app(
            Config("groq", "m", "test-key"),
            default_path=path,
            llm_client=config_llm,
            support_judge=config_llm
            if hasattr(config_llm, "score")
            else AllSupported(),
        )
    )
