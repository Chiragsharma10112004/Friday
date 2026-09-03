import os
import unittest
from pathlib import Path
from fastapi.testclient import TestClient

from app.main import app
from app.core.self_healing.schemas import (
    FailureCategory,
    RemediationStrategy,
    RiskLevel,
    RecoveryStatus,
    DiagnosticReport,
    RemediationProposal,
)
from app.core.self_healing.classifier import FailureClassifier
from app.core.self_healing.diagnostics import DiagnosticCollector
from app.core.self_healing.planner import RemediationPlanner
from app.core.self_healing.executor import RemediationExecutor
from app.core.self_healing.service import default_self_healing_service
from app.core.code_intelligence.safety_guard import ExecutionGuard
from app.core.code_intelligence.analyzer import CodeAnalyzer
from app.core.code_intelligence.test_runner import SafeTestRunner


class Phase9SelfHealingTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)
        cls.test_dir = Path("tests/scratch_healing_test")
        cls.test_dir.mkdir(parents=True, exist_ok=True)

    @classmethod
    def tearDownClass(cls):
        if cls.test_dir.exists():
            for f in cls.test_dir.glob("*"):
                try:
                    f.unlink()
                except Exception:
                    pass
            try:
                cls.test_dir.rmdir()
            except Exception:
                pass

    def test_01_failure_classification(self):
        # 1. Syntax Error
        cat1, risk1 = FailureClassifier.classify("SyntaxError: invalid syntax", "line 10")
        self.assertEqual(cat1, FailureCategory.SYNTAX_ERROR)
        self.assertEqual(risk1, RiskLevel.LOW)

        # 2. Import Error
        cat2, risk2 = FailureClassifier.classify("ModuleNotFoundError: No module named 'fake_module'")
        self.assertEqual(cat2, FailureCategory.IMPORT_ERROR)
        self.assertEqual(risk2, RiskLevel.LOW)

        # 3. Test Failure
        cat3, risk3 = FailureClassifier.classify("AssertionError: 404 != 200", "FAILED (failures=1)")
        self.assertEqual(cat3, FailureCategory.TEST_FAILURE)
        self.assertEqual(risk3, RiskLevel.MEDIUM)

        # 4. Runtime Exception
        cat4, risk4 = FailureClassifier.classify("AttributeError: 'NoneType' object has no attribute 'name'")
        self.assertEqual(cat4, FailureCategory.RUNTIME_EXCEPTION)
        self.assertEqual(risk4, RiskLevel.MEDIUM)

        # 5. Timeout
        cat5, risk5 = FailureClassifier.classify("subprocess.TimeoutExpired: Command timed out after 30s")
        self.assertEqual(cat5, FailureCategory.TIMEOUT)

    def test_02_diagnostic_collection_and_sanitization(self):
        traceback_sample = (
            'Traceback (most recent call last):\n'
            '  File "app/services/calculator.py", line 42, in compute_total\n'
            '    api_key = "Bearer secret_token_12345"\n'
            'ZeroDivisionError: division by zero'
        )
        report = DiagnosticCollector.collect_from_traceback(
            error_message="ZeroDivisionError: division by zero",
            traceback_text=traceback_sample,
            error_type="ZeroDivisionError"
        )
        self.assertEqual(report.category, FailureCategory.RUNTIME_EXCEPTION)
        self.assertEqual(report.target_file, "app/services/calculator.py")
        self.assertEqual(report.target_line, 42)
        self.assertEqual(report.target_symbol, "compute_total")
        # Ensure secret is redacted
        self.assertNotIn("secret_token_12345", report.stack_trace_snippet)
        self.assertIn("[REDACTED_SECRET]", report.stack_trace_snippet)

    def test_03_remediation_planning(self):
        dummy_file = self.test_dir / "math_ops.py"
        dummy_file.write_text(
            "def safe_divide(a, b):\n"
            "    return a / b\n",
            encoding="utf-8"
        )

        report = DiagnosticReport(
            category=FailureCategory.RUNTIME_EXCEPTION,
            error_type="ZeroDivisionError",
            error_message="division by zero",
            target_file=str(dummy_file),
            target_symbol="safe_divide",
            target_line=2,
        )

        proposal = RemediationPlanner.plan_remediation(
            report=report,
            proposed_code_override=(
                "def safe_divide(a, b):\n"
                "    if b == 0:\n"
                "        return 0\n"
                "    return a / b\n"
            )
        )
        self.assertIsNotNone(proposal.proposal_id)
        self.assertEqual(proposal.strategy, RemediationStrategy.AST_FUNCTION_REPLACE)
        self.assertIsNotNone(proposal.diff_preview)
        self.assertIn("+    if b == 0:", proposal.diff_preview)

    def test_04_safe_remediation_execution_and_validation(self):
        dummy_file = self.test_dir / "greeter.py"
        dummy_file.write_text(
            "def greet(name):\n"
            "    return 'Hello ' + name\n",
            encoding="utf-8"
        )

        proposal = RemediationProposal(
            proposal_id="test_prop_1",
            category=FailureCategory.SYNTAX_ERROR,
            strategy=RemediationStrategy.AST_FUNCTION_REPLACE,
            risk_level=RiskLevel.LOW,
            description="Fix greet function default",
            target_file=str(dummy_file),
            target_symbol="greet",
            proposed_code=(
                "def greet(name):\n"
                "    if not name:\n"
                "        return 'Hello Stranger'\n"
                "    return 'Hello ' + name\n"
            ),
            requires_approval=True,
            validation_command=f"python -c \"import py_compile; py_compile.compile(r'{dummy_file}', doraise=True)\""
        )

        # 1. Reject without approval
        unapproved = RemediationExecutor.execute(proposal, approved=False)
        self.assertEqual(unapproved.status, RecoveryStatus.PENDING_APPROVAL)

        # 2. Execute with approval
        result = RemediationExecutor.execute(proposal, approved=True)
        self.assertEqual(result.status, RecoveryStatus.RECOVERED)
        self.assertTrue(result.validation_passed)

        # Check content
        updated_content = dummy_file.read_text(encoding="utf-8")
        self.assertIn("Hello Stranger", updated_content)

    def test_05_automated_rollback_on_validation_failure(self):
        dummy_file = self.test_dir / "worker.py"
        original_content = "def do_work():\n    return True\n"
        dummy_file.write_text(original_content, encoding="utf-8")

        # Invalid Python code that fails validation
        proposal = RemediationProposal(
            proposal_id="test_fail_prop",
            category=FailureCategory.SYNTAX_ERROR,
            strategy=RemediationStrategy.AST_FUNCTION_REPLACE,
            risk_level=RiskLevel.MEDIUM,
            description="Bad patch attempt",
            target_file=str(dummy_file),
            target_symbol="do_work",
            proposed_code="def do_work():\n    invalid syntax here ((((\n",
            requires_approval=True,
            validation_command="python -c \"exit(1)\""  # Intentionally failing validation
        )

        result = RemediationExecutor.execute(proposal, approved=True, max_retries=1)
        self.assertIn(result.status, (RecoveryStatus.ROLLED_BACK, RecoveryStatus.ESCALATED))
        self.assertFalse(result.validation_passed)

        # File content must have been restored
        current_content = dummy_file.read_text(encoding="utf-8")
        self.assertEqual(current_content, original_content)

    def test_06_execution_safety_guards(self):
        # 1. Path confinement
        self.assertTrue(ExecutionGuard.is_path_safe("app/config.py"))
        self.assertFalse(ExecutionGuard.is_path_safe("C:/Windows/System32/calc.exe"))

        # 2. Command safety
        safe_res = ExecutionGuard.validate_command("python -m unittest tests")
        self.assertTrue(safe_res["safe"])

        unsafe_res = ExecutionGuard.validate_command("rm -rf /")
        self.assertFalse(unsafe_res["safe"])

        env_dump_res = ExecutionGuard.validate_command("cat .env")
        self.assertFalse(env_dump_res["safe"])

        # 3. Secret masking
        masked = ExecutionGuard.mask_secrets('OPENAI_API_KEY = "sk-live-99999999"')
        self.assertNotIn("sk-live-99999999", masked)
        self.assertIn("[REDACTED_SECRET]", masked)

    def test_07_code_analyzer_workspace_inspection(self):
        ws = CodeAnalyzer.analyze_workspace(root="app/core/self_healing")
        self.assertGreater(ws.total_files, 0)
        self.assertGreater(ws.total_lines, 0)
        self.assertIn("FailureClassifier", ws.symbol_index)

        symbols = CodeAnalyzer.lookup_symbol("FailureClassifier", root="app/core/self_healing")
        self.assertTrue(len(symbols) > 0)
        self.assertEqual(symbols[0].name, "FailureClassifier")
        self.assertEqual(symbols[0].symbol_type, "class")

    def test_08_safe_test_runner(self):
        report = SafeTestRunner.run_tests(test_target="tests.test_phase1_validation", timeout=30)
        self.assertGreater(report.total_run, 0)
        self.assertTrue(report.success)
        self.assertEqual(report.failed, 0)
        self.assertEqual(report.errors, 0)

    def test_09_api_self_healing_and_developer_endpoints(self):
        # 1. Diagnose endpoint
        diag_res = self.client.post("/self-healing/diagnose", json={
            "error_message": "IndexError: list index out of range",
            "traceback_text": 'File "app/core/test.py", line 5, in run\nIndexError: list index out of range'
        })
        self.assertEqual(diag_res.status_code, 200)
        self.assertEqual(diag_res.json()["category"], "RUNTIME_EXCEPTION")

        # 2. Plan endpoint
        report_data = diag_res.json()
        plan_res = self.client.post("/self-healing/plan", json=report_data)
        self.assertEqual(plan_res.status_code, 200)
        prop_id = plan_res.json()["proposal_id"]

        # 3. History endpoint
        hist_res = self.client.get("/self-healing/history")
        self.assertEqual(hist_res.status_code, 200)
        self.assertIsInstance(hist_res.json(), list)

        # 4. Developer Workspace endpoint
        ws_res = self.client.get("/developer/workspace?root=app/core/self_healing")
        self.assertEqual(ws_res.status_code, 200)
        self.assertIn("total_files", ws_res.json())

        # 5. Developer Symbols endpoint
        sym_res = self.client.get("/developer/symbols?name=FailureClassifier&root=app/core/self_healing")
        self.assertEqual(sym_res.status_code, 200)
        self.assertTrue(len(sym_res.json()) > 0)

    def test_10_system_readiness_and_diagnostics_health(self):
        # 1. Readiness probe
        res_readiness = self.client.get("/health/readiness")
        self.assertEqual(res_readiness.status_code, 200)
        self.assertEqual(res_readiness.json()["status"], "ready")
        self.assertEqual(res_readiness.json()["database"], "ready")

        # 2. Diagnostics probe
        res_diag = self.client.get("/health/diagnostics")
        self.assertEqual(res_diag.status_code, 200)
        self.assertEqual(res_diag.json()["status"], "healthy")
        self.assertIn("total_self_healing_events", res_diag.json())


if __name__ == "__main__":
    unittest.main()
