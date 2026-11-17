"""Notebook model: load, validate and split a Databricks .py export into Cells."""

from dataclasses import dataclass, field
from pathlib import Path

SOURCE_MARKER = "# Databricks notebook source"
SEPARATOR = "# COMMAND ----------"
MAX_BYTES = 500 * 1024


class NotebookError(Exception):
    """A user-facing problem with the requested Notebook path."""


@dataclass(frozen=True)
class Cell:
    number: int
    kind: str  # code | markdown | sql | run
    start: int  # absolute 1-based first line
    lines: tuple[str, ...]

    @property
    def end(self) -> int:
        return self.start + len(self.lines) - 1


@dataclass
class Notebook:
    path: Path
    lines: list[str]
    cells: list[Cell]
    warnings: list[str] = field(default_factory=list)

    def cell(self, number: int) -> Cell | None:
        return next((c for c in self.cells if c.number == number), None)

    def resolve_line_range(
        self, cell: str | None, start: str | None, end: str | None
    ) -> tuple[set[int], str | None]:
        """Turn raw request parameters into highlighted lines or a user message."""
        cell, start, end = (v.strip() if v else "" for v in (cell, start, end))
        if not cell:
            if start or end:
                return set(), "Choose a Cell to highlight a Line Range."
            return set(), None
        try:
            cell_no = int(cell)
            first = int(start) if start else None
            last = int(end) if end else None
        except ValueError:
            return set(), "One of Cell, start or end is not a number."
        target = self.cell(cell_no)
        if target is None:
            return set(), f"Cell {cell_no} does not exist (1 to {len(self.cells)})."
        first = target.start if first is None else first
        last = (target.end if start == "" else first) if last is None else last
        if first > last or first < target.start or last > target.end:
            return set(), (
                f"Lines {first}-{last} are outside Cell {cell_no} "
                f"(lines {target.start}-{target.end})."
            )
        return set(range(first, last + 1)), None


def detect_kind(lines: tuple[str, ...] | list[str]) -> str:
    for line in lines:
        if not line.strip():
            continue
        if line.startswith("# MAGIC"):
            magic = line.removeprefix("# MAGIC").strip()
            if magic.startswith("%md"):
                return "markdown"
            if magic.startswith("%sql"):
                return "sql"
            if magic.startswith("%run"):
                return "run"
        return "code"
    return "code"


def parse(text: str, path: Path) -> Notebook:
    lines = text.splitlines()
    first = 2 if lines and lines[0].strip() == SOURCE_MARKER else 1
    cells: list[Cell] = []
    buf: list[str] = []
    buf_start = first
    saw_separator = False

    def flush() -> None:
        cells.append(Cell(len(cells) + 1, detect_kind(buf), buf_start, tuple(buf)))

    for i in range(first, len(lines) + 1):
        line = lines[i - 1]
        if line.strip() == SEPARATOR:
            saw_separator = True
            flush()
            buf, buf_start = [], i + 1
        else:
            buf.append(line)
    flush()

    warnings = []
    if not saw_separator:
        warnings.append(
            "This file has no Cell separators, so it is treated as a single Cell."
        )
    return Notebook(path, lines, cells, warnings)


def resolve_path(raw: str) -> Path:
    return Path(raw.strip()).expanduser().resolve()


def load(raw_path: str) -> Notebook:
    if not raw_path.strip():
        raise NotebookError("Enter the path of a Notebook.")
    path = resolve_path(raw_path)
    if not path.exists():
        raise NotebookError(f"{path} does not exist.")
    if not path.is_file():
        raise NotebookError(f"{path} is not a file.")
    if path.suffix.lower() != ".py":
        raise NotebookError(
            f"{path.name} must be a .py file (Databricks source export)."
        )
    try:
        size = path.stat().st_size
        if size > MAX_BYTES:
            raise NotebookError(
                f"{path.name} is too large ({size // 1024} KB; the limit is about "
                f"{MAX_BYTES // 1024} KB)."
            )
        text = path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError) as e:
        raise NotebookError(f"{path} cannot be read: {e}") from e
    return parse(text, path)
