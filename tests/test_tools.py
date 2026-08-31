from pathlib import Path
from agent.tools import read_file, grep, list_dir, is_within_project, resolve_within_project

def test_read_file_returns_content(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("line1\nline2\n")
    assert read_file(str(p)) == "line1\nline2\n"

def test_read_file_missing_file_returns_error_string(tmp_path):
    result = read_file(str(tmp_path / "missing.py"))
    assert "not found" in result.lower() or "error" in result.lower()

def test_grep_finds_matching_lines(tmp_path):
    (tmp_path / "a.py").write_text("def add(): pass\ndef sub(): pass\n")
    (tmp_path / "b.py").write_text("class Widget: pass\n")
    results = grep("def ", str(tmp_path))
    assert any("a.py" in r and "def add" in r for r in results)
    assert not any("b.py" in r for r in results)

def test_list_dir_lists_entries(tmp_path):
    (tmp_path / "a.py").write_text("x")
    (tmp_path / "sub").mkdir()
    entries = list_dir(str(tmp_path))
    assert "a.py" in entries
    assert "sub" in entries

def test_is_within_project_accepts_paths_inside(tmp_path):
    (tmp_path / "sub").mkdir()
    assert is_within_project(str(tmp_path), tmp_path) is True
    assert is_within_project(str(tmp_path / "sub"), tmp_path) is True

def test_is_within_project_rejects_paths_outside(tmp_path):
    outside = tmp_path.parent / "not-the-project"
    assert is_within_project(str(outside), tmp_path) is False

def test_is_within_project_rejects_traversal(tmp_path):
    assert is_within_project(str(tmp_path / ".." / ".."), tmp_path) is False

def test_resolve_within_project_joins_relative_paths(tmp_path):
    assert resolve_within_project("lager.dat", tmp_path) == tmp_path / "lager.dat"

def test_resolve_within_project_leaves_absolute_paths_unchanged(tmp_path):
    absolute = tmp_path / "sub" / "lager.dat"
    assert resolve_within_project(str(absolute), tmp_path) == absolute

def test_is_within_project_accepts_relative_path_regardless_of_cwd(tmp_path, monkeypatch):
    (tmp_path / "lager.dat").write_text("data")
    monkeypatch.chdir(tmp_path.parent)
    assert is_within_project("lager.dat", tmp_path) is True
