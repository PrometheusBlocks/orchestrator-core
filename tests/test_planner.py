def test_plan_stub():
    from orchestrator_core.planner.maker import make_plan
    plan = make_plan("demo prompt")
    assert "prompt" in plan
