from agent.tools import read_file, grep, list_dir

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
