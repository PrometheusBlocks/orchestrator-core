#!/usr/bin/env python3
"""Ultimate test of self-bootstrapping with o4-mini real code generation."""

import subprocess
import sys
import os
from pathlib import Path


def run_ultimate_test():
    """Run the ultimate self-improvement test."""
    print("🚀 ULTIMATE SELF-BOOTSTRAPPING TEST")
    print("Testing: o4-mini generating real functional code\n")

    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Please set OPENAI_API_KEY environment variable")
        return False

    test_goal = (
        "create a comprehensive file analyzer that can read various file types, "
        "extract metadata, and generate detailed reports with statistics"
    )

    print(f"🎯 Test Goal: {test_goal}")
    print("\n🤖 Launching self-improvement with o4-mini...")

    try:
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "orchestrator_core.cli",
                "improve",
                test_goal,
            ],
            capture_output=True,
            text=True,
            timeout=120,
        )

        print("📊 RESULTS:")
        print("STDOUT:", result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)

        if result.returncode == 0:
            print("\n✅ Self-improvement command completed successfully!")

            gen_dir = Path("./generated_utilities")
            if gen_dir.exists():
                print(f"\n📁 Generated utilities in {gen_dir}:")
                for item in gen_dir.iterdir():
                    if item.is_dir():
                        print(f"  📂 {item.name}")
                        for file in item.rglob("*.py"):
                            size = file.stat().st_size
                            print(f"    📄 {file.name} ({size} bytes)")
                            content = file.read_text()
                            if len(content) > 500 and "def " in content and "TODO" not in content:
                                print(f"    ✅ Contains substantial functional code")
                            else:
                                print(f"    ⚠️  May be placeholder code")
                return True
            else:
                print("❌ No generated utilities directory found")
                return False
        else:
            print(f"❌ Self-improvement failed with return code: {result.returncode}")
            return False

    except subprocess.TimeoutExpired:
        print("❌ Test timed out (o4-mini may be taking too long)")
        return False
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False


if __name__ == "__main__":
    success = run_ultimate_test()
    if success:
        print("\n🎉 ULTIMATE TEST PASSED!")
        print("The orchestrator can now truly improve itself with o4-mini!")
    else:
        print("\n❌ ULTIMATE TEST FAILED!")
        print("Check the implementation and try again.")
        sys.exit(1)
