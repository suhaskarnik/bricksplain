"""Manager Audience Doc: schema, verification of Citations, and prompt loading."""

import json
import logging
from dataclasses import dataclass, field
from importlib import resources
from typing import Literal

from pydantic import BaseModel, StrictInt, ValidationError, model_validator

from .notebook import Notebook

log = logging.getLogger("bricksplain")

SECTIONS = (
    ("summary", "Summary"),
    ("how_it_works", "How it works in business terms"),
    ("outcomes", "Outcomes and impact"),
    ("potential_issues", "Potential issues"),
)


class DocError(Exception):
    """The LLM output could not be turned into a document."""


class Citation(BaseModel):
    cell: StrictInt
    start: StrictInt
    end: StrictInt
    quote: str


class Item(BaseModel):
    type: Literal["fact", "concern", "context"]
    text: str
    severity: Literal["low", "medium", "high"] | None = None
    citations: list[Citation] = []

    @model_validator(mode="after")
    def _shape(self):
        if self.type == "context":
            self.citations = []
            self.severity = None
        elif not self.citations:
            raise ValueError("a Claim needs a Citation")
        elif self.type == "concern" and self.severity is None:
            raise ValueError("a Concern needs a severity")
        elif self.type == "fact":
            self.severity = None
        return self


@dataclass
class Section:
    key: str
    title: str
    items: list[Item] = field(default_factory=list)


@dataclass
class ManagerDoc:
    sections: list[Section]
    dropped: int


def load_prompt(name: str) -> str:
    return (resources.files("bricksplain") / "prompts" / f"{name}.txt").read_text(
        encoding="utf-8"
    )


def numbered_listing(notebook: Notebook) -> str:
    out = []
    for c in notebook.cells:
        out.append(f"=== Cell {c.number} ({c.kind}), lines {c.start}-{c.end} ===")
        out.extend(f"{c.start + i:>5}  {line}" for i, line in enumerate(c.lines))
    return "\n".join(out)


def _norm(s: str) -> str:
    return " ".join(s.split())


def verify(citation: Citation, notebook: Notebook) -> str | None:
    """Return why the Citation fails, or None when it is a Verified Citation."""
    cell = notebook.cell(citation.cell)
    if cell is None:
        return f"cell {citation.cell} does not exist"
    if (
        citation.start > citation.end
        or citation.start < cell.start
        or citation.end > cell.end
    ):
        return f"lines {citation.start}-{citation.end} outside cell {cell.number}"
    first = citation.start - cell.start
    text = "\n".join(cell.lines[first : citation.end - cell.start + 1])
    quote = _norm(citation.quote)
    if not quote or quote not in _norm(text):
        return f"quote not found in cell {cell.number} lines {citation.start}-{citation.end}"
    return None


def build_doc(raw: str, notebook: Notebook) -> ManagerDoc:
    try:
        data = json.loads(raw)
    except ValueError as e:
        raise DocError("The LLM did not return valid JSON.") from e
    if not isinstance(data, dict):
        raise DocError("The LLM output was not a JSON object.")
    sections, dropped = [], 0
    for key, title in SECTIONS:
        section = Section(key, title)
        entries = data.get(key, [])
        for entry in entries if isinstance(entries, list) else []:
            try:
                item = Item.model_validate(entry)
            except ValidationError:
                log.warning("dropped claim in %s: malformed item", key)
                dropped += 1
                continue
            failures = [r for c in item.citations if (r := verify(c, notebook))]
            if failures:
                log.warning("dropped claim in %s: %s", key, "; ".join(failures))
                dropped += 1
            else:
                section.items.append(item)
        sections.append(section)
    if dropped:
        log.warning("citation verification dropped %d claim(s)", dropped)
    return ManagerDoc(sections, dropped)
