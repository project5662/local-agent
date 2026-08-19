from agent.filters import should_index_file

def test_rejects_ignored_directory(tmp_path):
    p = tmp_path / ".git" / "config"
    p.parent.mkdir()
    p.write_text("x")
    assert should_index_file(p, tmp_path) is False

def test_rejects_binary_extension(tmp_path):
    p = tmp_path / "logo.png"
    p.write_bytes(b"\x89PNG")
    assert should_index_file(p, tmp_path) is False

def test_accepts_python_file(tmp_path):
    p = tmp_path / "main.py"
    p.write_text("print('hi')")
    assert should_index_file(p, tmp_path) is True

def test_rejects_gitignored_file(tmp_path):
    (tmp_path / ".gitignore").write_text("secret.txt\n")
    p = tmp_path / "secret.txt"
    p.write_text("shh")
    assert should_index_file(p, tmp_path) is False
