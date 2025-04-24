import sys
import re
import pathlib

MAX_TOKENS = int(sys.argv[1]) if len(sys.argv) > 1 else 200_000


# --- locate the current repository root --------------------------------------
def find_git_root(path: pathlib.Path) -> pathlib.Path:
    for parent in [path] + list(path.parents):
        if (parent / ".git").exists():
            return parent
    raise RuntimeError("Could not find .git directory")


root = find_git_root(pathlib.Path(__file__).resolve())
# -----------------------------------------------------------------------------


def iter_source_files(repo_root: pathlib.Path):
    """Yield every *.py file to be measured."""
    for p in repo_root.rglob("*.py"):
        if "_reference" in p.parts or ".venv" in p.parts:
            continue
        yield p


token_total = 0
for py_file in iter_source_files(root):
    try:
        token_total += len(re.findall(r"\S+", py_file.read_text()))
    except Exception:
        # Ignore unreadable files (permissions, encoding)
        continue

if token_total > MAX_TOKENS:
    print(f"Token budget exceeded: {token_total} > {MAX_TOKENS}")
    sys.exit(1)

print(f"Token count OK: {token_total}")
