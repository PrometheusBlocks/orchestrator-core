# ScaffoldingSprint.md

**Date Created:** May 8, 2025 (Revised May 8, 2025 - V2)

## 1. Project Overview & Current Status

**Project:** `orchestrator-core`

**Purpose:** Orchestrates "PrometheusBlocks" utilities, allowing discovery, planning, and (soon) scaffolding.

**Current Key Capabilities (as of May 8, 2025):**
* **Utility Contract Definition:** (`contracts/utility_contract.py`) A Pydantic model defines the schema for utilities. **This model MUST NOT be changed to maintain backward compatibility.**
* **Utility Registry & Discovery:**
    * Local registry CLI (`registry_cli/cli.py`).
    * Catalog system (`orchestrator_core/catalog/`) loads local specs and fetches `utility_contract.json` files from the `PrometheusBlocks` GitHub organization using `orchestrator_core/catalog/github_client.py`. The `github_client.py` can identify the source repository during discovery.
* **Planning Engine:**
    * Parses prompts to identify "resolved" (available) and "missing" (unavailable) capabilities, outputting a `plan.json`.
* **Interfaces:** CLI (`list`, `show`, `plan`) and API (`/plan`).

**`plan.json` structure example:**
```json
{
  "prompt": "upload pdf bank statement and see retirement simulation",
  "resolved": [
    "document_upload"
  ],
  "missing": [
    "statement_parser",
    "financial_engine"
  ]
}
External Generic Block Template (for NEW/MISSING utilities):
https://github.com/PrometheusBlocks/block-template

2. Goals for this "Scaffolding Sprint" (Revised V2)
Extend orchestrator-core to set up a local project directory based on a plan.json:

Resolved Utilities: Clone their actual source code from their respective GitHub repositories. The repository URL will be determined at the time the utility's contract is discovered by the catalog system.
Missing Utilities: Scaffold a new utility structure using the generic block template.
NO CHANGES TO orchestrator-core/contracts/utility_contract.py ARE PERMITTED.

3. Detailed Implementation Steps for AI Agent (Revised V2)
Step 3.1: Modify Catalog System to Capture Source Repository URLs
Files to Modify:

orchestrator-core/orchestrator_core/catalog/github_client.py
orchestrator-core/orchestrator_core/catalog/index.py
Task: When a utility_contract.json is fetched from GitHub, the catalog system must capture and store the HTML URL of the repository where this contract was found. This URL will be associated with the utility's specification data but will NOT be part of the UtilityContract Pydantic model itself.

In orchestrator_core/catalog/github_client.py (Workspace_github_specs function):

When processing items from the GitHub Search API (or when fetching from repo roots), each item (search result) or repo object contains information about the repository (e.g., item['repository']['html_url'] or similar for repo objects).
When a spec_json (the content of utility_contract.json) is successfully parsed and validated:
Extract the repository's HTML URL (e.g., https://github.com/PrometheusBlocks/some-utility-repo).
When adding the spec to the specs dictionary (e.g., specs[spec.name] = spec.model_dump() if hasattr(spec, "model_dump") else spec.dict()), also add this captured repository URL as an additional key-value pair to this dictionary.
Use a distinct key name that won't clash with UtilityContract fields, for example: _source_repository_url_discovered.
So, the dictionary for a spec fetched from GitHub might look like:
Python

{
    "name": "utility_x",
    "version": "1.0.0",
    # ... other fields from UtilityContract ...
    "_source_repository_url_discovered": "[https://github.com/PrometheusBlocks/utility_x_repo](https://github.com/PrometheusBlocks/utility_x_repo)" # New associated data
}
In orchestrator_core/orchestrator_core/catalog/index.py (load_specs function):

When merging remote_specs (from Workspace_github_specs) with local specs:
Ensure this new _source_repository_url_discovered field is preserved if the remote spec is chosen (e.g., it's a newer version).
Local specs (from ~/.pb_registry) will likely not have this field. This is acceptable; they might not be GitHub-sourced or this functionality might be primarily for GitHub-discovered utilities. The scaffolding logic will need to handle cases where this field might be missing for a resolved utility (and perhaps cannot clone it then, or skip).
Decision for AI Agent: If a local spec for a "resolved" utility does not have _source_repository_url_discovered, the scaffolder should log a warning and skip cloning for that specific utility, as its source is unknown.
Step 3.2: Create/Update executor Module
Directory: orchestrator-core/orchestrator_core/executor/
File: orchestrator-core/orchestrator_core/executor/scaffolder.py

In scaffolder.py:

Function 1: clone_repository(repo_url: str, target_dir: Path, branch: Optional[str] = None) -> bool

(Same as previous V1 instructions: clone, handle errors, remove .git dir).
Function 2: customize_new_utility_from_template(template_dir: Path, new_utility_name: str)

Purpose: Customizes the generic block template for a new/missing utility.
Parameters: template_dir: Path, new_utility_name: str.
Implementation:
Placeholder Replacement: Iterate files. Replace basic placeholders like {{UTILITY_NAME}} with new_utility_name.
Generate Placeholder utility_contract.json:
Create a Python dictionary representing a minimal, valid UtilityContract.
Python

placeholder_contract = {
    "name": new_utility_name,
    "version": "0.1.0-dev",
    "language": "python", # Default
    "description": f"Scaffolded utility: {new_utility_name}",
    "entrypoints": [{"name": "run", "description": "Default entry point", "parameters_schema": {}, "return_schema": {}}],
    "deps": [],
    "tests": []
    # DO NOT add _source_repository_url_discovered here
}
Save this dictionary as utility_contract.json inside template_dir using json.dump().
Log actions.
Function 3: scaffold_project(plan: dict, project_base_dir: Path, project_name: str, generic_block_template_url: str) -> Path (Revised Logic)

Parameters: (Same)
Implementation:
Create main_project_path.
Load all specs: all_specs_data: Dict[str, dict] = load_specs(). This dictionary now contains specs, some of which (from GitHub) will have the _source_repository_url_discovered key.
Handle "Resolved" Utilities:
For each utility_id in plan['resolved']: a. utility_dir = main_project_path / utility_id. Create dir. b. spec_data = all_specs_data.get(utility_id) c. If not spec_data: Log error and skip. d. repo_url_to_clone = spec_data.get("_source_repository_url_discovered") e. repo_branch_to_clone = spec_data.get("_source_repository_branch_discovered") (If you also decide to capture branch info in catalog). Assume default branch for now if this isn't captured. f. If not repo_url_to_clone: * Log warning: f"Source repository URL not found for resolved utility {utility_id}. Cannot clone. Skipping." * Continue. g. If clone_repository(repo_url_to_clone, utility_dir, branch=repo_branch_to_clone) fails: Log error and skip. h. Log success for utility_id.
Handle "Missing" Utilities:
For each utility_id_to_build in plan['missing']: a. utility_dir = main_project_path / utility_id_to_build. Create dir. b. If clone_repository(generic_block_template_url, utility_dir) fails: Log error and skip. c. Call customize_new_utility_from_template(utility_dir, utility_id_to_build). d. Log success for utility_id_to_build.
Return main_project_path.
Step 3.3: Update CLI
File to Modify: orchestrator_core/orchestrator_core/cli.py

(Largely the same as V1 instructions for scaffold subcommand. Ensure user messages are clear about cloning existing vs. scaffolding new.)
Step 3.4: Update API (Optional)
(Same as V1)
Step 3.5: Update requirements.txt
No changes expected.
Step 3.6: Update README.md
Update scaffold command description, clarifying behavior and mentioning that resolved utilities are cloned from source if discovered via GitHub.
Step 3.7: Add Tests
New Test File: orchestrator-core/tests/test_executor.py

(Test functions in scaffolder.py as described in V1, but adapt test_scaffold_project):
When testing scaffold_project, the mock load_specs should return data that includes _source_repository_url_discovered for some "resolved" utilities and omits it for others (to test the skipping logic).
Verify clone_repository is called with the correct repo URL from the spec for resolved utilities, and with the generic template URL for missing ones.
Update orchestrator-core/tests/test_catalog.py:

Modify tests for load_specs (and indirectly Workspace_github_specs by mocking its underlying GitHub API calls) to assert that _source_repository_url_discovered is correctly populated in the returned spec dictionaries when a utility is sourced from GitHub.
4. Definition of Done for this Sprint (Revised V2)
NO CHANGES to orchestrator-core/contracts/utility_contract.py Pydantic model.
Catalog system (github_client.py, index.py) is updated to capture and associate _source_repository_url_discovered with specs fetched from GitHub.
executor.scaffolder module handles:
Cloning Git repos.
Customizing generic template for new/missing utilities, including generating a placeholder utility_contract.json.
Scaffolding projects: cloning resolved utilities from their discovered source URL, and scaffolding missing utilities from the generic template.
CLI scaffold command is implemented.
README.md is updated.
Unit tests cover the new logic in catalog and executor, including the capture of source URLs.
This approach keeps your UtilityContract stable while enabling the desired scaffolding behavior for existing utilities.