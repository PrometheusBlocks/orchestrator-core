import json
import subprocess
from pathlib import Path


import orchestrator_core.executor.scaffolder as scaffolder


def test_clone_repository_success(monkeypatch, tmp_path):
    target = tmp_path / "repo_clone"

    # Fake subprocess.run to simulate git clone and create .git directory
    def fake_run(args, check):
        # args: ['git', 'clone', repo_url, target_dir]
        # Create target_dir and .git inside
        dest = Path(args[-1])
        dest.mkdir(parents=True, exist_ok=True)
        (dest / ".git").mkdir()
        return

    monkeypatch.setattr(subprocess, "run", fake_run)
    # Now call clone_repository
    repo_url = "https://example.com/repo.git"
    success = scaffolder.clone_repository(repo_url, target, branch="main")
    assert success is True
    # .git should have been removed
    assert not (target / ".git").exists()
    # target directory should exist
    assert target.exists()


def test_clone_repository_failure(monkeypatch, tmp_path):
    target = tmp_path / "repo_fail"

    # Fake subprocess.run to raise CalledProcessError
    def fake_run(args, check):
        raise subprocess.CalledProcessError(returncode=1, cmd=args)

    monkeypatch.setattr(subprocess, "run", fake_run)
    success = scaffolder.clone_repository("url", target)
    assert success is False
    # target directory should not exist or empty
    # Depending on implementation, may or may not create. At least not a full clone
    assert not (target / ".git").exists()


def test_customize_new_utility_from_template(tmp_path):
    # Create template directory with a file containing placeholder
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    file_path = template_dir / "README.md"
    file_path.write_text("This is {{UTILITY_NAME}} template.")
    # Call customization
    scaffolder.customize_new_utility_from_template(template_dir, "myutil")
    # Placeholder replaced
    content = file_path.read_text()
    assert "myutil template" in content
    # utility_contract.json created
    contract_path = template_dir / "utility_contract.json"
    assert contract_path.exists()
    data = json.loads(contract_path.read_text())
    assert data["name"] == "myutil"
    assert data["version"] == "0.1.0-dev"


def test_customize_new_utility_with_contract(tmp_path):
    template_dir = tmp_path / "template2"
    template_dir.mkdir()
    f = template_dir / "README.md"
    f.write_text("Hello {{UTILITY_NAME}}")
    contract = {"name": "foo", "version": "1.0.0"}
    scaffolder.customize_new_utility_from_template(
        template_dir, "foo", contract_data=contract
    )
    data = json.loads((template_dir / "utility_contract.json").read_text())
    assert data == contract
    assert "foo" in f.read_text()


def test_scaffold_project_calls(monkeypatch, tmp_path):
    # Prepare plan with one resolved and one missing utility
    plan = {
        "resolved": ["a"],
        "missing": ["b"],
        "proposed_utilities": [{"name": "b", "version": "1.0"}],
    }
    base = tmp_path / "projects"
    project_name = "proj"
    template_url = "https://example.com/template.git"
    # Monkeypatch load_specs to return spec for 'a'
    fake_specs = {
        "a": {"_source_repository_url_discovered": "https://github.com/org/a"}
    }
    monkeypatch.setattr(scaffolder, "load_specs", lambda: fake_specs)
    # Capture calls
    calls = []

    def fake_clone(repo_url, target_dir, branch=None):
        calls.append(("clone", repo_url, str(target_dir), branch))
        return True

    monkeypatch.setattr(scaffolder, "clone_repository", fake_clone)

    def fake_customize(target_dir, name, contract_data=None):
        calls.append(("customize", str(target_dir), name, contract_data))

    monkeypatch.setattr(
        scaffolder, "customize_new_utility_from_template", fake_customize
    )

    def fake_init(repo_dir):
        calls.append(("init", str(repo_dir)))
        return True

    monkeypatch.setattr(scaffolder, "init_git_repo", fake_init)
    # Run scaffolding
    monkeypatch.setattr(scaffolder, "create_github_repository", lambda *a, **k: "https://github.com/example/repo.git")
    monkeypatch.setattr(scaffolder, "push_repo_to_remote", lambda repo, remote: calls.append(("push", str(repo), remote)))
    project_path = scaffolder.scaffold_project(
        plan,
        base,
        project_name,
        template_url,
        create_github_repos=True,
    )
    # Verify returned path
    assert project_path == base / project_name
    # Expected calls: clone for 'a', clone for 'b', customize for 'b'
    assert (
        "clone",
        "https://github.com/org/a",
        str(base / project_name / "a"),
        None,
    ) in calls
    assert ("clone", template_url, str(base / project_name / "b"), None) in calls
    assert (
        "customize",
        str(base / project_name / "b"),
        "b",
        {"name": "b", "version": "1.0"},
    ) in calls
    assert ("init", str(base / project_name / "a")) in calls
    assert ("init", str(base / project_name / "b")) in calls
    assert (
        "push",
        str(base / project_name / "b"),
        "https://github.com/example/repo.git",
    ) in calls
