from orchestrator_core.planner import make_plan


def test_plan_stub():
    plan = make_plan("demo prompt")
    assert "prompt" in plan
