import pytest

from orchestrator_core.planner import make_plan


@pytest.mark.parametrize(
    "prompt,expected_resolved,expected_missing",
    [
        ("upload pdf", ["document_upload"], []),
        ("bank statement", [], ["statement_parser"]),
        ("simulate retirement", [], ["financial_engine"]),
    ],
)
def test_make_plan_classification(prompt, expected_resolved, expected_missing):
    plan = make_plan(prompt)
    # Check prompt echoed
    assert plan.get("prompt") == prompt
    # Check resolved capabilities include expected items
    for cap in expected_resolved:
        assert cap in plan.get("resolved", []), f"Expected {cap} in resolved"
    # Check missing capabilities include expected items
    for cap in expected_missing:
        assert cap in plan.get("missing", []), f"Expected {cap} in missing"
