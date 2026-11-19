"""Audience Docs: schema, verification of Citations, and prompt loading."""

import json
import logging
from dataclasses import dataclass, field
from importlib import resources
from typing import Literal
from urllib.parse import quote

from pydantic import BaseModel, StrictInt, ValidationError, model_validator

from .llm import LLMClient, LLMError
from .notebook import Notebook

log = logging.getLogger("bricksplain")


@dataclass(frozen=True)
class Audience:
    key: str
    title: str
    prompt: str
    sections: tuple[tuple[str, str], ...]


AUDIENCES = (
    Audience(
        "manager",
        "Manager",
        "manager",
        (
            ("summary", "Summary"),
            ("how_it_works", "How it works in business terms"),
            ("outcomes", "Outcomes and impact"),
            ("potential_issues", "Potential issues"),
        ),
    ),
    Audience(
        "developer",
        "Developer",
        "developer",
        (
            ("notebook_map", "Notebook map by Cell"),
            ("data_flow", "Data flow"),
            ("business_rules", "Business rules"),
            ("inferred_glossary", "Inferred Glossary"),
            ("gotchas", "Gotchas and how to run"),
        ),
    ),
    Audience(
        "agent",
        "AI coding agent",
        "agent",
        (
            ("purpose", "Purpose"),
            ("invariants", "Invariants"),
            ("risky_areas", "Risky areas"),
            ("verify", "How to verify changes"),
        ),
    ),
)
AUDIENCE_BY_KEY = {a.key: a for a in AUDIENCES}


class DocError(Exception):
    """The LLM output could not be turned into a document."""


class Citation(BaseModel):
    cell: StrictInt
    start: StrictInt
    end: StrictInt
    quote: str


class Item(BaseModel):
    type: Literal["fact", "concern", "context", "no_findings"]
    text: str
    severity: Literal["low", "medium", "high"] | None = None
    # True when the Claim describes a whole Cell, so it must cite the Cell's full range.
    describes_cell: bool = False
    citations: list[Citation] = []

    @model_validator(mode="after")
    def _shape(self):
        if self.type in ("context", "no_findings"):
            self.citations = []
            self.severity = None
            self.describes_cell = False
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
class AudienceDoc:
    sections: list[Section]
    dropped: int
    failures: list[str] = field(default_factory=list)


def _read_prompt(name: str) -> str:
    return (resources.files("bricksplain") / "prompts" / f"{name}.txt").read_text(
        encoding="utf-8"
    )


CHECKLIST_PROMPT = "checklist"


def load_prompt(name: str) -> str:
    """Read a prompt file, inlining the shared risk checklist at `{{checklist}}`."""
    text = _read_prompt(name)
    if "{{checklist}}" in text:
        text = text.replace("{{checklist}}", _read_prompt(CHECKLIST_PROMPT).strip())
    return text


def numbered_listing(notebook: Notebook) -> str:
    out = []
    for c in notebook.cells:
        out.append(f"=== Cell {c.number} ({c.kind}), lines {c.start}-{c.end} ===")
        out.extend(f"{c.start + i:>5}  {line}" for i, line in enumerate(c.lines))
    return "\n".join(out)


def _norm(s: str) -> str:
    """Collapse whitespace and ignore the `# MAGIC` prefix Databricks puts on
    every line of a markdown/SQL Cell, which the LLM naturally leaves out."""
    lines = (
        line.strip().removeprefix("# MAGIC").strip() if "# MAGIC" in line else line
        for line in s.splitlines()
    )
    return " ".join(" ".join(lines).split())


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


def check_coverage(item: Item, notebook: Notebook) -> list[str]:
    """Why the cited ranges are too narrow for what the Claim asserts, if they are."""
    if not item.describes_cell:
        return []
    reasons = []
    for c in item.citations:
        cell = notebook.cell(c.cell)
        if cell and (c.start, c.end) != (cell.start, cell.end):
            reasons.append(
                f"cell {cell.number} is described as a whole but the citation covers "
                f"only lines {c.start}-{c.end}; cite its full range "
                f"{cell.start}-{cell.end}"
            )
    return reasons


def build_doc(raw: str, notebook: Notebook, audience: Audience) -> AudienceDoc:
    try:
        data = json.loads(raw)
    except ValueError as e:
        raise DocError("The LLM did not return valid JSON.") from e
    if not isinstance(data, dict):
        raise DocError("The LLM output was not a JSON object.")
    sections, dropped, failures = [], 0, []
    for key, title in audience.sections:
        section = Section(key, title)
        entries = data.get(key, [])
        for entry in entries if isinstance(entries, list) else []:
            try:
                item = Item.model_validate(entry)
            except ValidationError:
                log.warning("failing claim in %s/%s: malformed item", audience.key, key)
                log.warning(
                    "failing claim content in %s/%s: %r",
                    audience.key,
                    key,
                    entry,
                    extra={"llm_response": True},
                )
                failures.append(f"{key}: an item was malformed")
                dropped += 1
                continue
            failed = [r for c in item.citations if (r := verify(c, notebook))]
            if not failed:
                failed = check_coverage(item, notebook)
            if failed:
                reason = "; ".join(failed)
                log.warning("failing claim in %s/%s: %s", audience.key, key, reason)
                # Claim text and quotes are LLM output: only logged on opt-in.
                log.warning(
                    "failing claim content in %s/%s: text=%r citations=%r",
                    audience.key,
                    key,
                    item.text,
                    [c.model_dump() for c in item.citations],
                    extra={"llm_response": True},
                )
                failures.append(f"{key}: {reason}")
                dropped += 1
            else:
                section.items.append(item)
        sections.append(section)
    if dropped:
        log.warning("%s: citation checks dropped %d claim(s)", audience.key, dropped)
    return AudienceDoc(sections, dropped, failures)


SUPPORT_PROMPT = "support"


def support_check(llm: LLMClient, doc: AudienceDoc, audience: Audience) -> AudienceDoc:
    """Drop Claims whose quotes do not back them, using one batched LLM call.

    Raises LLMError/DocError when the call or its answer is unusable: the doc
    cannot be trusted without the check."""
    claims = [
        (s, i)
        for s in doc.sections
        for i, item in enumerate(s.items)
        if item.type in ("fact", "concern")
    ]
    if not claims:
        return doc
    payload = {
        "claims": [
            {
                "id": n,
                "text": s.items[i].text,
                "quotes": [c.quote for c in s.items[i].citations],
            }
            for n, (s, i) in enumerate(claims)
        ]
    }
    raw = llm.complete(load_prompt(SUPPORT_PROMPT), json.dumps(payload))
    try:
        verdicts = {str(v["id"]): v for v in json.loads(raw)["verdicts"]}
    except (ValueError, KeyError, TypeError) as e:
        raise DocError("The support check did not return usable verdicts.") from e
    unsupported: dict[tuple[str, int], str] = {}
    for n, (s, i) in enumerate(claims):
        v = verdicts.get(str(n))
        if isinstance(v, dict) and v.get("supported") is True:
            continue
        reason = (v.get("reason") if isinstance(v, dict) else None) or "no verdict"
        unsupported[(s.key, i)] = str(reason)
    if not unsupported:
        return doc
    sections, failures = [], list(doc.failures)
    for s in doc.sections:
        kept = []
        for i, item in enumerate(s.items):
            reason = unsupported.get((s.key, i))
            if reason is None:
                kept.append(item)
                continue
            log.warning("unsupported claim in %s/%s", audience.key, s.key)
            # The reason and claim text are LLM output: only logged on opt-in.
            log.warning(
                "unsupported claim content in %s/%s: text=%r reason=%r",
                audience.key,
                s.key,
                item.text,
                reason,
                extra={"llm_response": True},
            )
            failures.append(f"{s.key}: not supported by its quote: {reason}")
        sections.append(Section(s.key, s.title, kept))
    log.warning("%s: support check dropped %d claim(s)", audience.key, len(unsupported))
    return AudienceDoc(sections, doc.dropped + len(unsupported), failures)


def _generate_checked(
    llm: LLMClient, system: str, user: str, notebook: Notebook, audience: Audience
) -> AudienceDoc:
    doc = build_doc(llm.complete(system, user), notebook, audience)
    return support_check(llm, doc, audience)


def generate_doc(llm: LLMClient, notebook: Notebook, audience: Audience) -> AudienceDoc:
    """Generate the doc; retry once with failures fed back if any Claim fails."""
    system, user = load_prompt(audience.prompt), numbered_listing(notebook)
    doc = _generate_checked(llm, system, user, notebook, audience)
    if not doc.dropped:
        return doc
    log.warning(
        "%s: retrying generation once after %d failing claim(s)",
        audience.key,
        doc.dropped,
    )
    coverage = any(
        "described as a whole" in f and "not supported by its quote" not in f
        for f in doc.failures
    )
    feedback = (
        f"{user}\n\nYour previous answer had claims that failed checks:\n"
        + "\n".join(f"- {f}" for f in doc.failures)
        + "\nReturn the complete corrected JSON document. Every citation must "
        "use lines inside the cited cell and a quote copied verbatim from them, "
        "and every claim must follow from its quoted text."
        + (
            ' A claim with "describes_cell": true must cite each cited cell\'s '
            "full line range."
            if coverage
            else ""
        )
    )
    try:
        retried = _generate_checked(llm, system, feedback, notebook, audience)
    except (LLMError, DocError) as e:
        log.warning(
            "%s: retry failed (%s); keeping first result",
            audience.key,
            type(e).__name__,
        )
        return doc
    if retried.dropped:
        log.warning(
            "%s: %d claim(s) still failing after retry; dropped",
            audience.key,
            retried.dropped,
        )
    return retried if retried.dropped <= doc.dropped else doc


def _cite_label(c: Citation) -> str:
    lines = f"line {c.start}" if c.start == c.end else f"lines {c.start}-{c.end}"
    return f"Cell {c.cell}, {lines}"


def to_markdown(doc: AudienceDoc, audience: Audience, path: str) -> str:
    """Render an Audience Doc as Markdown; Citations are app-relative links."""
    out = [f"# {audience.title} Audience Doc", "", f"Notebook: `{path}`", ""]
    for s in doc.sections:
        out += [f"## {s.title}", ""]
        for item in s.items:
            if item.type == "context":
                label = "Context (not from the Notebook)"
            elif item.type == "no_findings":
                label = "No findings"
            elif item.type == "concern":
                label = f"Concern ({item.severity})"
            else:
                label = "Fact"
            links = " ".join(
                f"[{_cite_label(c)}](/source?path={quote(path, safe='')}"
                f"&cell={c.cell}&start={c.start}&end={c.end})"
                for c in item.citations
            )
            out.append(f"- **{label}** {item.text} {links}".rstrip())
        out.append("")
    return "\n".join(out)
