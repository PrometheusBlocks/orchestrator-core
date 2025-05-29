#!/usr/bin/env python3
"""Test script for self-improvement functionality."""

import sys
import subprocess
from pathlib import Path


def test_basic_import() -> bool:
    """Test that new modules can be imported."""
    try:
        from orchestrator_core.skills.core import CodeGenerationSkill, SelfInspectionSkill, PlanningSkill
        print("✅ Core skills import successfully")
        return True
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False


def test_self_inspection() -> bool:
    """Test self-inspection capabilities."""
    try:
        from orchestrator_core.skills.core import SelfInspectionSkill

        inspector = SelfInspectionSkill()

        cli_source = inspector.read_own_source("cli.py")
        if "def main(" in cli_source:
            print("✅ Can read own source code")
        else:
            print("❌ Cannot read own source code properly")
            return False

        skills = inspector.list_available_skills()
        print(f"✅ Found {len(skills)} existing skills")

        files = inspector.list_source_files()
        if "cli.py" in files:
            print("✅ Can list source files")
        else:
            print("❌ Cannot list source files properly")
            return False

        return True
    except Exception as e:
        print(f"❌ Self-inspection test failed: {e}")
        return False


def test_cli_command() -> bool:
    """Test the new CLI command."""
    try:
        result = subprocess.run(
            [sys.executable, "-m", "orchestrator_core.cli", "improve", "--help"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if result.returncode == 0 and "improve" in result.stdout:
            print("✅ CLI improve command available")
            return True
        print(f"❌ CLI command failed: {result.stderr}")
        return False
    except Exception as e:
        print(f"❌ CLI test failed: {e}")
        return False


def main() -> None:
    """Run all tests."""
    print("Testing self-improvement functionality...\n")
    tests = [
        ("Basic Import", test_basic_import),
        ("Self Inspection", test_self_inspection),
        ("CLI Command", test_cli_command),
    ]
    passed = 0
    for name, func in tests:
        print(f"Running {name}...")
        if func():
            passed += 1
        print()

    print(f"Tests passed: {passed}/{len(tests)}")
    if passed == len(tests):
        print("\n🎉 All tests passed! Self-improvement functionality is ready.")
        print("\nTry: python -m orchestrator_core.cli improve 'add file search capability'")
    else:
        print("\n❌ Some tests failed. Check the implementation.")
        sys.exit(1)


if __name__ == "__main__":
    main()
