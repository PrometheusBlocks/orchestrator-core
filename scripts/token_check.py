import sys, pathlib, re

MAX_TOKENS = int(sys.argv[1]) if len(sys.argv) > 1 else 200000
root = pathlib.Path(__file__).resolve().parent.parent
code = "\n".join(p.read_text() for p in root.rglob("*.py") if "venv" not in p.parts)
tokens = len(re.findall(r"\S+", code))
if tokens > MAX_TOKENS:
    print(f"Token budget exceeded: {tokens} > {MAX_TOKENS}")
    sys.exit(1)
print(f"Token count OK: {tokens}")
