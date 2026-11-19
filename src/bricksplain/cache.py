"""On-disk cache of Audience Docs, one entry per (Notebook, model, prompt, Audience)."""

import hashlib
import json
import logging
from pathlib import Path

from .audience_doc import (
    CHECKLIST_PROMPT,
    SUPPORT_PROMPT,
    Audience,
    AudienceDoc,
    Item,
    Section,
    load_prompt,
)
from .notebook import Notebook

log = logging.getLogger("bricksplain")


def _sha(*parts: str) -> str:
    h = hashlib.sha256()
    for p in parts:
        h.update(p.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


class DocCache:
    def __init__(self, directory: Path, model: str):
        self._dir = directory
        self._model = model

    def _path(self, notebook: Notebook, audience: Audience) -> Path:
        key = _sha(
            "\n".join(notebook.lines),
            self._model,
            load_prompt(audience.prompt),
            load_prompt(SUPPORT_PROMPT),
            load_prompt(CHECKLIST_PROMPT),
            audience.key,
            repr(audience.sections),
        )
        return self._dir / f"{audience.key}-{key[:32]}.json"

    def get(self, notebook: Notebook, audience: Audience) -> AudienceDoc | None:
        path = self._path(notebook, audience)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            doc = AudienceDoc(
                [
                    Section(s["key"], s["title"], [Item(**i) for i in s["items"]])
                    for s in data["sections"]
                ],
                data["dropped"],
                data["failures"],
            )
        except FileNotFoundError:
            log.info("cache miss: %s", audience.key)
            return None
        except (OSError, ValueError, KeyError, TypeError):
            log.warning("cache entry unreadable, treating as miss: %s", path.name)
            return None
        log.info("cache hit: %s", audience.key)
        return doc

    def put(self, notebook: Notebook, audience: Audience, doc: AudienceDoc) -> None:
        data = {
            "sections": [
                {
                    "key": s.key,
                    "title": s.title,
                    "items": [i.model_dump() for i in s.items],
                }
                for s in doc.sections
            ],
            "dropped": doc.dropped,
            "failures": doc.failures,
        }
        path = self._path(notebook, audience)
        try:
            self._dir.mkdir(parents=True, exist_ok=True)
            tmp = path.with_suffix(".tmp")
            tmp.write_text(json.dumps(data), encoding="utf-8")
            tmp.replace(path)
        except OSError as e:
            log.warning("could not write cache entry %s: %s", path.name, e)
