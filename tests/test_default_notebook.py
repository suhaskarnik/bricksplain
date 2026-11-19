import re
import subprocess
from pathlib import Path

from fastapi.testclient import TestClient

from bricksplain import app as app_module
from bricksplain import notebook as nb
from bricksplain.app import create_app
from bricksplain.config import Config

ROOT = Path(__file__).parent.parent


def test_default_notebook_is_committed_and_parses_into_cells():
    path = ROOT / app_module.DEFAULT_PATH
    assert path.is_file()
    assert app_module.DEFAULT_PATH.startswith("examples/")
    notebook = nb.load(str(path))
    assert len(notebook.cells) > 1


def test_source_viewer_opens_default_notebook_cell_and_line_range():
    client = TestClient(create_app(Config("groq", "llama-3.3-70b", "test-key")))
    path = ROOT / app_module.DEFAULT_PATH
    cell = nb.load(str(path)).cell(1)
    r = client.get(
        "/source",
        params={"path": str(path), "cell": 1, "start": cell.start, "end": cell.start},
    )
    assert r.status_code == 200
    hl = re.findall(r'<tr[^>]*class="[^"]*hl[^"]*"[^>]*data-line="(\d+)"', r.text)
    assert hl == [str(cell.start)]


def test_sample_notebook_and_data_are_not_git_ignored():
    files = [
        app_module.DEFAULT_PATH,
        *(
            str(p.relative_to(ROOT))
            for p in (ROOT / "examples/sample_data").glob("*.csv")
        ),
    ]
    assert len(files) > 1
    r = subprocess.run(
        ["git", "check-ignore", *files],
        cwd=ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    assert r.returncode == 1, f"ignored by git: {r.stdout}"
