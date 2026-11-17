import re


def view(client, path, **params):
    return client.get("/source", params={"path": str(path), **params})


def test_input_page_prefills_default_path(client, fixtures):
    r = client.get("/")
    assert r.status_code == 200
    assert str(fixtures / "small.py") in r.text


def test_cells_are_numbered_from_one_with_header_as_cell_one(client, fixtures):
    r = view(client, fixtures / "small.py")
    assert r.status_code == 200
    for n in (1, 2, 3, 4):
        assert f"Cell {n}" in r.text
    assert "Cell 5" not in r.text
    assert 'data-kind="markdown"' in r.text
    assert 'data-kind="code"' in r.text
    assert 'data-kind="sql"' in r.text
    assert 'data-kind="run"' in r.text


def test_line_range_is_highlighted_with_absolute_line_numbers(client, fixtures):
    r = view(client, fixtures / "small.py", cell=2, start=8, end=9)
    assert r.status_code == 200
    hl = re.findall(r'<tr[^>]*class="[^"]*hl[^"]*"[^>]*data-line="(\d+)"', r.text)
    assert hl == ["8", "9"]


def test_missing_cell_shows_message(client, fixtures):
    r = view(client, fixtures / "small.py", cell=99, start=1, end=1)
    assert r.status_code == 200
    assert "Cell 99 does not exist" in r.text


def test_line_range_outside_cell_shows_message(client, fixtures):
    r = view(client, fixtures / "small.py", cell=2, start=1, end=3)
    assert r.status_code == 200
    assert "outside Cell 2" in r.text
    assert 'class="hl' not in r.text


def test_no_separators_is_one_cell_with_warning(client, tmp_path):
    p = tmp_path / "flat.py"
    p.write_text("a = 1\nb = 2\n")
    r = view(client, p)
    assert "Cell 1" in r.text and "Cell 2" not in r.text
    assert "no Cell separators" in r.text


def test_path_validation(client, tmp_path):
    big = tmp_path / "big.py"
    big.write_text("x = 1\n" * 100_000)
    txt = tmp_path / "a.txt"
    txt.write_text("hi")
    assert "does not exist" in view(client, tmp_path / "nope.py").text
    assert "must be a .py file" in view(client, txt).text
    assert "too large" in view(client, big).text
    assert "not a file" in view(client, tmp_path).text


def test_relative_path_resolves_against_cwd(client, fixtures, monkeypatch):
    monkeypatch.chdir(fixtures)
    r = view(client, "small.py")
    assert "Cell 1" in r.text


def test_non_numeric_line_parameters_show_message(client, fixtures):
    r = view(client, fixtures / "small.py", cell=2, start="abc", end=9)
    assert "not a number" in r.text
    assert 'class="hl' not in r.text


def test_lines_without_cell_show_message(client, fixtures):
    r = view(client, fixtures / "small.py", start=8, end=9)
    assert "Choose a Cell" in r.text


def test_cell_without_lines_highlights_whole_cell(client, fixtures):
    r = view(client, fixtures / "small.py", cell=2)
    hl = re.findall(r'<tr[^>]*class="[^"]*hl[^"]*"[^>]*data-line="(\d+)"', r.text)
    assert hl == ["7", "8", "9", "10"]


def test_uppercase_py_extension_accepted(client, tmp_path):
    p = tmp_path / "NB.PY"
    p.write_text("a = 1\n")
    assert "Cell 1" in view(client, p).text


def test_resolved_provider_and_model_shown_but_not_key(client, fixtures):
    for r in (client.get("/"), view(client, fixtures / "small.py")):
        assert "groq / llama-3.3-70b" in r.text
        assert "test-key" not in r.text
