from pathlib import Path
from agent.tools import read_file, grep, list_dir, is_within_project, resolve_within_project, find_max_stock, find_min_stock, list_stock_by_location, list_locations

def _make_row(art, namn, stock, kategori, plats):
    return art.ljust(10) + namn.ljust(35) + str(stock).rjust(6, "0") + kategori.ljust(15) + plats.ljust(15)

def test_read_file_returns_content(tmp_path):
    p = tmp_path / "a.py"
    p.write_text("line1\nline2\n")
    assert read_file(str(p)) == "line1\nline2\n"

def test_read_file_missing_file_returns_error_string(tmp_path):
    result = read_file(str(tmp_path / "missing.py"))
    assert "not found" in result.lower() or "error" in result.lower()

def test_read_file_rejects_file_larger_than_limit(tmp_path, monkeypatch):
    import agent.tools as tools_module
    monkeypatch.setattr(tools_module.config, "MAX_READ_FILE_CHARS", 10)
    p = tmp_path / "big.py"
    p.write_text("x" * 11)
    result = read_file(str(p))
    assert "too large" in result.lower()

def test_read_file_allows_file_within_limit(tmp_path, monkeypatch):
    import agent.tools as tools_module
    monkeypatch.setattr(tools_module.config, "MAX_READ_FILE_CHARS", 10)
    p = tmp_path / "small.py"
    p.write_text("x" * 10)
    result = read_file(str(p))
    assert result == "x" * 10

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

def test_find_max_stock_sums_across_locations_and_picks_highest(tmp_path):
    content = (
        _make_row("ART-00001", "Test1", 100, "Kategori", "Plats1") + "\n"
        + _make_row("ART-00001", "Test1", 100, "Kategori", "Plats2") + "\n"  # totalt 200
        + _make_row("ART-00002", "Test2", 150, "Kategori", "Plats1") + "\n"  # totalt 150
    )
    p = tmp_path / "lager.dat"
    p.write_text(content)
    result = find_max_stock(str(p))
    assert "ART-00001" in result
    assert "200" in result

def test_find_max_stock_missing_file_returns_error_string(tmp_path):
    result = find_max_stock(str(tmp_path / "missing.dat"))
    assert "error" in result.lower()

def test_find_max_stock_filters_by_location(tmp_path):
    content = (
        _make_row("ART-00001", "Test1", 100, "Kategori", "Plats1") + "\n"
        + _make_row("ART-00001", "Test1", 100, "Kategori", "Plats2") + "\n"  # totalt 200 över alla platser
        + _make_row("ART-00002", "Test2", 150, "Kategori", "Plats1") + "\n"  # men mest i Plats1
    )
    p = tmp_path / "lager.dat"
    p.write_text(content)
    result = find_max_stock(str(p), location="Plats1")
    assert "ART-00002" in result
    assert "150" in result

def test_find_max_stock_location_is_case_insensitive_and_ignores_padding(tmp_path):
    content = _make_row("ART-00001", "Test1", 100, "Kategori", "Plats1") + "\n"
    p = tmp_path / "lager.dat"
    p.write_text(content)
    result = find_max_stock(str(p), location="plats1")
    assert "ART-00001" in result

def test_find_max_stock_unknown_location_returns_error_string(tmp_path):
    content = _make_row("ART-00001", "Test1", 100, "Kategori", "Plats1") + "\n"
    p = tmp_path / "lager.dat"
    p.write_text(content)
    result = find_max_stock(str(p), location="Okänd Ort")
    assert "error" in result.lower()

def test_find_min_stock_sums_across_locations_and_picks_lowest(tmp_path):
    content = (
        _make_row("ART-00001", "Test1", 100, "Kategori", "Plats1") + "\n"
        + _make_row("ART-00001", "Test1", 100, "Kategori", "Plats2") + "\n"  # totalt 200
        + _make_row("ART-00002", "Test2", 50, "Kategori", "Plats1") + "\n"   # totalt 50, lägst
    )
    p = tmp_path / "lager.dat"
    p.write_text(content)
    result = find_min_stock(str(p))
    assert "ART-00002" in result
    assert "50" in result

def test_find_min_stock_filters_by_location(tmp_path):
    content = (
        _make_row("ART-00001", "Test1", 200, "Kategori", "Plats1") + "\n"
        + _make_row("ART-00002", "Test2", 50, "Kategori", "Plats1") + "\n"
        + _make_row("ART-00002", "Test2", 10, "Kategori", "Plats2") + "\n"  # lägst, men bara i Plats2
    )
    p = tmp_path / "lager.dat"
    p.write_text(content)
    result = find_min_stock(str(p), location="Plats2")
    assert "ART-00002" in result
    assert "10" in result

def test_find_min_stock_missing_file_returns_error_string(tmp_path):
    result = find_min_stock(str(tmp_path / "missing.dat"))
    assert "error" in result.lower()

def test_list_stock_by_location_returns_one_line_per_location(tmp_path):
    content = (
        _make_row("ART-00001", "Test1", 100, "Kategori", "Plats1") + "\n"
        + _make_row("ART-00001", "Test1", 50, "Kategori", "Plats2") + "\n"
        + _make_row("ART-00002", "Test2", 999, "Kategori", "Plats1") + "\n"
    )
    p = tmp_path / "lager.dat"
    p.write_text(content)
    result = list_stock_by_location(str(p), "ART-00001")
    assert "Plats1: 100 st" in result
    assert "Plats2: 50 st" in result
    assert "ART-00002" not in result

def test_list_stock_by_location_is_case_insensitive(tmp_path):
    content = _make_row("ART-00001", "Test1", 100, "Kategori", "Plats1") + "\n"
    p = tmp_path / "lager.dat"
    p.write_text(content)
    result = list_stock_by_location(str(p), "art-00001")
    assert "Plats1: 100 st" in result

def test_list_stock_by_location_unknown_article_returns_error_string(tmp_path):
    content = _make_row("ART-00001", "Test1", 100, "Kategori", "Plats1") + "\n"
    p = tmp_path / "lager.dat"
    p.write_text(content)
    result = list_stock_by_location(str(p), "ART-99999")
    assert "error" in result.lower()

def test_list_locations_returns_sorted_unique_locations(tmp_path):
    content = (
        _make_row("ART-00001", "Test1", 100, "Kategori", "Plats2") + "\n"
        + _make_row("ART-00001", "Test1", 50, "Kategori", "Plats1") + "\n"
        + _make_row("ART-00002", "Test2", 10, "Kategori", "Plats1") + "\n"  # dubblett, ska bara synas en gång
    )
    p = tmp_path / "lager.dat"
    p.write_text(content)
    result = list_locations(str(p))
    assert result == "- Plats1\n- Plats2"

def test_list_locations_missing_file_returns_error_string(tmp_path):
    result = list_locations(str(tmp_path / "missing.dat"))
    assert "error" in result.lower()
