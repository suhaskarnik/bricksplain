"""One Generate run: one concurrent task per Audience, each with its own state."""

import logging
import threading
import uuid
from dataclasses import dataclass, field

from .audience_doc import AUDIENCES, Audience, AudienceDoc, DocError, generate_doc
from .llm import LLMClient, LLMError
from .notebook import Notebook

log = logging.getLogger("bricksplain")

PENDING, RUNNING, DONE, FAILED = "pending", "running", "done", "failed"


@dataclass
class DocState:
    audience: Audience
    state: str = PENDING
    doc: AudienceDoc | None = None
    error: str | None = None


@dataclass
class Job:
    id: str
    path: str
    notebook: Notebook
    docs: dict[str, DocState] = field(default_factory=dict)


class JobRunner:
    def __init__(self, llm: LLMClient):
        self._llm = llm
        self._lock = threading.Lock()
        self.jobs: dict[str, Job] = {}

    def start(self, path: str, notebook: Notebook) -> Job:
        job = Job(uuid.uuid4().hex, path, notebook)
        job.docs = {a.key: DocState(a) for a in AUDIENCES}
        with self._lock:
            self.jobs[job.id] = job
        for a in AUDIENCES:
            threading.Thread(
                target=self._run, args=(job, job.docs[a.key]), daemon=True
            ).start()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self.jobs.get(job_id)

    def _run(self, job: Job, ds: DocState) -> None:
        ds.state = RUNNING
        try:
            ds.doc = generate_doc(self._llm, job.notebook, ds.audience)
            ds.state = DONE
        except (LLMError, DocError) as e:
            log.error("%s doc failed: %s", ds.audience.key, e)
            ds.error = f"The {ds.audience.title} doc could not be generated: {e}"
            ds.state = FAILED
        except Exception:
            log.exception("%s doc crashed", ds.audience.key)
            ds.error = (
                f"The {ds.audience.title} doc could not be generated: unexpected error."
            )
            ds.state = FAILED
