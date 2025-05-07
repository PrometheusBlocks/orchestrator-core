import json
import pytest
import openai
import orchestrator_core.planner.parser as parser


class DummyResponse:
    def __init__(self, content, error=False):
        if error:
            raise Exception("api error")
        # Simulate new Responses API: aggregated text
        self.output_text = content
        # Legacy fallback array (unused when output_text exists)
        self.output = []


class DummyClient:
    def __init__(self, content, error=False):
        self._content = content
        self._error = error
        # Responses namespace
        self.responses = self

    def create(self, *args, **kwargs):
        return DummyResponse(self._content, error=self._error)


def test_prompt_to_plan_happy(monkeypatch):
    # Setup dummy response with valid JSON plan
    plan_data = [
        {"step_id": 1, "action": "foo", "inputs": {"a": 1}, "description": "desc"}
    ]
    content = json.dumps(plan_data)
    # Patch OpenAI client to return our DummyClient
    monkeypatch.setattr(openai, "OpenAI", lambda api_key=None: DummyClient(content))

    plan = parser.prompt_to_plan("do foo")
    assert plan == plan_data


def test_prompt_to_plan_invalid_json(monkeypatch):
    # Simulate OpenAI returning invalid JSON
    # Simulate invalid JSON from LLM
    monkeypatch.setattr(openai, "OpenAI", lambda api_key=None: DummyClient("not a json"))
    # Monkey-patch fallback capabilities
    monkeypatch.setattr(parser, "prompt_to_capabilities", lambda prompt: ['cap1'])

    plan = parser.prompt_to_plan("test prompt")
    # Fallback generates one step per capability
    assert plan == [{"step_id": 1, "action": "cap1", "inputs": {}, "description": ""}]


def test_prompt_to_plan_api_error(monkeypatch):
    # Simulate API error
    # Simulate API error
    monkeypatch.setattr(openai, "OpenAI", lambda api_key=None: DummyClient("irrelevant", error=True))
    monkeypatch.setattr(parser, "prompt_to_capabilities", lambda prompt: ['A', 'B'])

    plan = parser.prompt_to_plan("another prompt")
    # Expect fallback plan with two steps
    assert plan == [
        {"step_id": 1, "action": "A", "inputs": {}, "description": ""},
        {"step_id": 2, "action": "B", "inputs": {}, "description": ""},
    ]