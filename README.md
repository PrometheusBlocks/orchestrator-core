# PrometheusBlocks — Orchestrator Core

## Day 1 Completed (2025-05-02)

- Migrated GitHub client to use the `requests` library.
- Added unit tests for the GitHub client (tests/test_github_client.py).
- Updated `requirements.txt` with `requests` and `packaging`.
- Verified CLI list/show commands and all tests pass.

This repository provides the *contract definition* and a minimal *registry CLI* for PrometheusBlocks utilities.

* **contracts/utility_contract.py** — Pydantic data model that every utility must import.
* **registry_cli/** — a tiny CLI (`pb-registry`) to publish/fetch utility specs.
* **scripts/token_check.py** — fails CI if total token count for code+tests > 200 000.
* **tests/** — smoke tests for the contract schema.
## Catalog Index (new)

After you publish a utility spec with `pb-registry`, you can inspect everything
that’s available:

```bash
# list all registered utilities (latest version only)
python -m orchestrator_core.cli list

# view the full JSON spec for a specific utility
python -m orchestrator_core.cli show data-models
```

## GitHub Integration (new)

The catalog now also discovers utility specs directly from public GitHub repositories under the `PrometheusBlocks` organization. Any file named `utility_contract.json` in any path of those repos will be fetched, validated, and merged into the local registry view.

Prerequisites:
  * (Optional) Set a GitHub personal access token for higher rate limits:
      export GITHUB_TOKEN=<your_token>
  * Ensure your Python trusts GitHub’s TLS certificates. On macOS, run the
    `Install Certificates.command` that comes with the Python installer,
    or install the `certifi` package (`pip install certifi`).

Usage:
```bash
# List all utilities, including those fetched from GitHub
python -m orchestrator_core.cli list

# If you prefer to inspect directly via Python:
python3 - <<'EOF'
from orchestrator_core.catalog.github_client import fetch_github_specs
specs = fetch_github_specs()
import pprint; pprint.pprint(specs)
EOF
```

## Planner (new)

Generate execution plans from natural language prompts:

```bash
# via CLI
python -m orchestrator_core.cli plan "upload pdf statements"
# or if installed as pb-orchestrator:
pb-orchestrator plan "upload pdf statements"
```

This prints a JSON array of structured execution plan steps (each with `step_id`, `action`, `inputs`, and `description`), and writes `plan.json` to the current directory.

## API (new)

Run the API server:

```bash
uvicorn orchestrator_core.api.main:app --reload
```

Then POST to `/plan`:

```bash
curl -X POST "http://127.0.0.1:8000/plan" -H "Content-Type: application/json" \
     -d '{"prompt": "upload pdf statements"}'
```

Response:

```json
[
  {
    "step_id": 1,
    "action": "document_upload",
    "inputs": {},
    "description": "Upload PDF statements to storage"
  },
  {
    "step_id": 2,
    "action": "statement_parser",
    "inputs": {},
    "description": "Parse statements from uploaded PDF"
  }
]
```
  
## Scaffold (new)

Scaffold a local project directory based on a planning result (`plan.json`):

```bash
# Scaffold project 'my_project' in the current directory using plan.json
python -m orchestrator_core.cli scaffold my_project .
```

Behavior:
  * For each utility contract listed in `plan.json`, a folder is created under the project directory.
  * The `block-template` repository is cloned into each folder and its `utility_contract.json` is replaced with the contract from `plan.json`.

The command assumes `plan.json` is present in the working directory and uses `https://github.com/PrometheusBlocks/block-template` as the template source.

## Execute (new)

Run a single utility entrypoint within a scaffolded project. Dependencies from
each utility's `requirements.txt` are installed into an isolated virtual
environment under the project directory on first use.

```bash
# Execute the 'hello' entrypoint of utility 'myutil' inside ./my_project
python -m orchestrator_core.cli execute ./my_project --utility myutil --entrypoint hello --params_json '{"name": "World"}'
```

## Web UI (new)

A minimal React-based frontend is included under `webui/`.
The API server now serves this UI directly. Start the app with:

```bash
uvicorn orchestrator_core.api.main:app --reload
# Visit http://localhost:8000
```

The landing page asks *"What do you want to build?"*. After submitting a
prompt, it calls the `/plan` API and lists the utilities found. Clicking a
utility fetches its contract from the `/utility/{name}` endpoint.

## New API Endpoint

The API now exposes `GET /utility/{name}` to retrieve a utility contract by
name.

```bash
curl http://127.0.0.1:8000/utility/myutil
```
