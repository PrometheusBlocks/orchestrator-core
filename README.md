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