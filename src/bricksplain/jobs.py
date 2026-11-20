"""One Generate run: one concurrent task per Audience, each with its own state."""

import logging
import threading
import uuid
from dataclasses import dataclass, field

from .audience_doc import (
    AUDIENCES,
    Audience,
    AudienceDoc,
    Coverage,
    DocError,
    compute_coverage,
    generate_doc,
)
from .cache import DocCache
from .decision import SupportJudge
from .llm import LLMClient, LLMError
from .notebook import Notebook

log = logging.getLogger("bricksplain")

PENDING, RUNNING, DONE, FAILED = "pending", "running", "done", "failed"


@dataclass
class DocState:
    audience: Audience
    state: str = PENDING
    doc: AudienceDoc | None = None
    coverage: Coverage | None = None
    error: str | None = None


@dataclass
class Job:
    id: str
    path: str
    notebook: Notebook
    docs: dict[str, DocState] = field(default_factory=dict)


class JobRunner:
    def __init__(self, llm: LLMClient, judge: SupportJudge, cache: DocCache):
        self._llm = llm
        self._judge = judge
        self._cache = cache
        self._lock = threading.Lock()
        self.jobs: dict[str, Job] = {}

    def start(self, path: str, notebook: Notebook, regenerate: bool = False) -> Job:
        job = Job(uuid.uuid4().hex, path, notebook)
        job.docs = {a.key: DocState(a) for a in AUDIENCES}
        with self._lock:
            self.jobs[job.id] = job
        for a in AUDIENCES:
            threading.Thread(
                target=self._run, args=(job, job.docs[a.key], regenerate), daemon=True
            ).start()
        return job

    def get(self, job_id: str) -> Job | None:
        with self._lock:
            return self.jobs.get(job_id)

    def _run(self, job: Job, ds: DocState, regenerate: bool) -> None:
        ds.state = RUNNING
        try:
            if regenerate:
                log.info("cache bypassed (regenerate): %s", ds.audience.key)
            doc = None if regenerate else self._cache.get(job.notebook, ds.audience)
            if doc is None:
                doc = generate_doc(self._llm, self._judge, job.notebook, ds.audience)
                self._cache.put(job.notebook, ds.audience, doc)
            ds.doc = doc
            ds.coverage = compute_coverage(doc, job.notebook)
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
