# PrometheusBlocks — Orchestrator Core

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

This prints resolved and missing capabilities and writes `plan.json` to the current directory.

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
{
  "prompt": "upload pdf statements",
  "resolved": ["document_upload", ...],
  "missing": ["statement_parser", ...]
}
```