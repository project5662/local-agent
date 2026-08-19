from . import config

def should_index_file(path, project_root):
    #1
    relative = path.relative_to(project_root)

    if any(part in config.DEFAULT_IGNORE_DIRS for part in relative.parts):
        return False

    #2
    if path.suffix in config.DEFAULT_IGNORE_EXTENSIONS:
        return False

    #3
    gitignore_part = project_root / ".gitignore"
    if gitignore_part.exists():
        ignored_names = gitignore_part.read_text().splitlines()
        if path.name in ignored_names:
            return False

    #4
    return True
    