#!/usr/bin/env python3
"""Test o4-mini code generation capabilities."""

import os
import sys
from pathlib import Path


def test_o4_mini_available():
    """Test that o4-mini API access works."""
    try:
        from openai import OpenAI

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not set")
            return False

        client = OpenAI(api_key=api_key)

        response = client.responses.create(
            model="o4-mini-2025-04-16",
            instructions="You are a test assistant.",
            input="Say 'o4-mini is working' if you can process this."
        )

        if hasattr(response, 'output_text'):
            output = response.output_text
        else:
            output = ""
            for item in getattr(response, 'output', []):
                for content in item.get('content', []):
                    if content.get('type') == 'output_text':
                        output += content.get('text', '')

        if "o4-mini is working" in output.lower():
            print("✅ o4-mini API access confirmed")
            return True
        else:
            print(f"❌ o4-mini response unexpected: {output[:100]}")
            return False

    except Exception as e:
        print(f"❌ o4-mini API test failed: {e}")
        return False


def test_code_generation_skill():
    """Test the enhanced CodeGenerationSkill with o4-mini."""
    try:
        from orchestrator_core.skills.core import CodeGenerationSkill

        skill = CodeGenerationSkill()

        print("🧪 Testing function generation with o4-mini...")
        code = skill.generate_function(
            description="Calculate the factorial of a number",
            function_name="calculate_factorial",
            parameters={"n": "int"}
        )

        if "def calculate_factorial" in code and len(code) > 100:
            print("✅ Function generation successful")
            print(f"📝 Generated code preview:\n{code[:200]}...")
            return True
        else:
            print(f"❌ Function generation failed or too simple: {code[:100]}")
            return False

    except Exception as e:
        print(f"❌ Code generation test failed: {e}")
        return False


def test_utility_generation():
    """Test complete utility generation with o4-mini."""
    try:
        from orchestrator_core.skills.core import CodeGenerationSkill

        skill = CodeGenerationSkill()

        contract = {
            "name": "test_calculator",
            "entrypoints": [
                {
                    "name": "add",
                    "description": "Add two numbers",
                    "parameters_schema": {"type": "object", "properties": {"a": {"type": "number"}, "b": {"type": "number"}}},
                    "return_schema": {"type": "number"}
                },
                {
                    "name": "multiply",
                    "description": "Multiply two numbers",
                    "parameters_schema": {"type": "object", "properties": {"x": {"type": "number"}, "y": {"type": "number"}}},
                    "return_schema": {"type": "number"}
                }
            ]
        }

        print("🧪 Testing complete utility generation with o4-mini...")
        code = skill.generate_complete_utility_implementation(
            name="test_calculator",
            description="A calculator utility with basic math operations",
            contract=contract
        )

        if ("def add" in code and "def multiply" in code and
                len(code) > 200 and "TODO" not in code):
            print("✅ Utility generation successful")
            print(f"📝 Generated utility preview:\n{code[:300]}...")
            try:
                compile(code, "test_calculator.py", "exec")
                print("✅ Generated code compiles successfully")
                return True
            except SyntaxError as e:
                print(f"❌ Generated code has syntax errors: {e}")
                return False
        else:
            print(f"❌ Utility generation failed or incomplete: {code[:150]}")
            return False

    except Exception as e:
        print(f"❌ Utility generation test failed: {e}")
        return False


def main():
    """Run all o4-mini tests."""
    print("🧪 Testing o4-mini Integration\n")

    tests = [
        ("o4-mini API Access", test_o4_mini_available),
        ("Code Generation Skill", test_code_generation_skill),
        ("Complete Utility Generation", test_utility_generation),
    ]

    passed = 0
    for name, test_func in tests:
        print(f"Running {name}...")
        if test_func():
            passed += 1
        print()

    print(f"Tests passed: {passed}/{len(tests)}")

    if passed == len(tests):
        print("🎉 All o4-mini tests passed! Ready for real code generation.")
        print("\n🚀 Try this enhanced test:")
        print("python -m orchestrator_core.cli improve 'create a JSON validator that can validate complex schemas and pretty-print JSON'")
    else:
        print("❌ Some tests failed. Check o4-mini integration.")
        sys.exit(1)


if __name__ == "__main__":
    main()
