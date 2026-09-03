import re
import time
import subprocess
from typing import Optional, List, Dict, Any

from app.core.code_intelligence.schemas import TestRunReport, TestCaseResult
from app.core.code_intelligence.safety_guard import ExecutionGuard


class SafeTestRunner:
    """
    Runs Python test suites safely and parses unstructured test output
    into structured, actionable reports for self-healing and developer review.
    """

    @classmethod
    def run_tests(
        cls,
        test_target: str = "tests.run_all_phase_tests",
        timeout: int = 60,
    ) -> TestRunReport:
        cmd = f"python -m {test_target}" if not test_target.startswith("python") else test_target

        # Safety validation
        val = ExecutionGuard.validate_command(cmd)
        if not val.get("safe"):
            return TestRunReport(
                total_run=0,
                passed=0,
                failed=0,
                errors=1,
                duration_sec=0.0,
                success=False,
                raw_output=val.get("reason", "Unsafe command rejected."),
            )

        start_time = time.time()
        try:
            res = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            duration = round(time.time() - start_time, 3)
            raw = (res.stdout or "") + "\n" + (res.stderr or "")

            # Parse results
            total_run = 0
            failures = 0
            errors = 0

            # Match "TOTAL TESTS RUN: X" or "Ran X tests in Ys"
            total_match = re.search(r'TOTAL TESTS RUN:\s*(\d+)', raw) or re.search(r'Ran\s+(\d+)\s+test', raw, re.I)
            if total_match:
                total_run = int(total_match.group(1))

            fail_match = re.search(r'FAILURES:\s*(\d+)', raw) or re.search(r'failures=(\d+)', raw, re.I) or re.search(r'FAILED\s*\((?:failures=(\d+))?', raw, re.I)
            if fail_match:
                failures = int(fail_match.group(1) or 0)

            err_match = re.search(r'ERRORS:\s*(\d+)', raw) or re.search(r'errors=(\d+)', raw, re.I)
            if err_match:
                errors = int(err_match.group(1) or 0)

            if total_run == 0 and ("OK" in raw or res.returncode == 0):
                # Count dots if unittest output has dots like "......."
                dots = raw.split("\n")[0].count(".")
                if dots > 0:
                    total_run = dots

            passed = max(0, total_run - (failures + errors))
            success = (res.returncode == 0) and (failures == 0) and (errors == 0)

            # Parse individual failing test cases
            test_cases: List[TestCaseResult] = []
            failing_blocks = re.findall(r'(?:FAIL|ERROR):\s+(test_\w+)\s+\(([^)]+)\)\n-+([\s\S]*?)(?=\n={3,}|\n-{3,}|$)', raw)
            for test_name, module_info, traceback_text in failing_blocks:
                test_cases.append(
                    TestCaseResult(
                        name=test_name,
                        status="FAILED" if "FAIL:" in raw else "ERROR",
                        error_message=traceback_text.strip().splitlines()[-1] if traceback_text.strip() else None,
                        stack_trace=traceback_text.strip(),
                    )
                )

            return TestRunReport(
                total_run=total_run,
                passed=passed,
                failed=failures,
                errors=errors,
                duration_sec=duration,
                success=success,
                test_cases=test_cases,
                raw_output=ExecutionGuard.mask_secrets(raw[-4000:]),
            )
        except subprocess.TimeoutExpired:
            return TestRunReport(
                total_run=0,
                passed=0,
                failed=0,
                errors=1,
                duration_sec=float(timeout),
                success=False,
                raw_output=f"Test run timed out after {timeout} seconds.",
            )
        except Exception as e:
            return TestRunReport(
                total_run=0,
                passed=0,
                failed=0,
                errors=1,
                duration_sec=0.0,
                success=False,
                raw_output=str(e),
            )
