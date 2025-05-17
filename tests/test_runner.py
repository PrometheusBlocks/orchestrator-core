import subprocess
import sys

import orchestrator_core.executor.runner as runner


def test_prepare_environment_installs(monkeypatch, tmp_path):
    project = tmp_path / "proj"
    util = project / "util"
    util.mkdir(parents=True)
    req = util / "requirements.txt"
    req.write_text("package==1.0")

    calls = []

    def fake_run(args, check):
        calls.append(args)

    monkeypatch.setattr(subprocess, "run", fake_run)

    venv = runner.prepare_environment(project)
    assert venv == project / "venv"
    assert calls[0][0:3] == [sys.executable, "-m", "venv"] if calls else False
    pip_call = calls[1]
    assert "pip" in pip_call[0]
    assert "install" in pip_call


def test_execute_utility_runs(tmp_path):
    project = tmp_path / "proj"
    util_dir = project / "myutil"
    util_dir.mkdir(parents=True)
    init_file = util_dir / "__init__.py"
    init_file.write_text(
        "def hello(name):\n    print(f'hello {name}')\n    return name.upper()\n"
    )

    result = runner.execute_utility(project, "myutil", "hello", {"name": "bob"})

    assert result.return_value == "BOB"
    assert "hello bob" in result.stdout
    assert result.stderr == ""
