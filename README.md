# PrometheusBlocks — Orchestrator Core

This repository provides the *contract definition* and a minimal *registry CLI* for PrometheusBlocks utilities.

* **contracts/utility_contract.py** — Pydantic data model that every utility must import.
* **registry_cli/** — a tiny CLI (`pb-registry`) to publish/fetch utility specs.
* **scripts/token_check.py** — fails CI if total token count for code+tests > 200 000.
* **tests/** — smoke tests for the contract schema.
