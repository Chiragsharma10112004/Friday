import uuid
from pathlib import Path
from typing import Optional, Dict, Any

from app.core.self_healing.schemas import (
    DiagnosticReport,
    RemediationProposal,
    RemediationStrategy,
    FailureCategory,
    RiskLevel,
)
from app.core.editor.diff import generate_diff
from app.core.editor.editor import extract_function
from app.core.brain.manager import process_message


class RemediationPlanner:
    """
    Formulates structured remediation proposals with diff previews,
    risk assessments, and validation criteria based on diagnostic reports.
    """

    @classmethod
    def plan_remediation(
        cls,
        report: DiagnosticReport,
        proposed_code_override: Optional[str] = None,
        custom_validation_cmd: Optional[str] = None,
    ) -> RemediationProposal:
        proposal_id = f"rem_{uuid.uuid4().hex[:8]}"
        target_file = report.target_file or "unknown_file.py"
        target_symbol = report.target_symbol
        strategy = RemediationStrategy.MANUAL_ESCALATION
        risk = RiskLevel.MEDIUM
        requires_approval = True
        proposed_code = proposed_code_override
        diff_preview = None
        description = f"Remediation for {report.category.value}: {report.error_message}"

        # 1. Handle Syntax and Runtime errors with a target function
        if report.target_symbol and Path(target_file).exists():
            fn_info = extract_function(report.target_symbol, root=str(Path(target_file).parent))
            if fn_info.get("success"):
                orig_source = fn_info.get("source", "")
                strategy = RemediationStrategy.AST_FUNCTION_REPLACE
                risk = RiskLevel.LOW if report.category == FailureCategory.SYNTAX_ERROR else RiskLevel.MEDIUM

                if not proposed_code:
                    # Formulate repair via AI Brain or template
                    prompt = (
                        f"Fix the following Python function '{report.target_symbol}' to resolve this error: {report.error_message}\n"
                        f"Context traceback: {report.stack_trace_snippet or ''}\n\n"
                        f"Original function:\n```python\n{orig_source}\n```\n"
                        f"Return ONLY the updated complete function code."
                    )
                    try:
                        ai_response = process_message(
                            messages=[{"role": "user", "content": prompt}],
                            task="code_repair"
                        )
                        # Extract python code block if present
                        if "```python" in ai_response:
                            proposed_code = ai_response.split("```python")[1].split("```")[0].strip()
                        elif "```" in ai_response:
                            proposed_code = ai_response.split("```")[1].split("```")[0].strip()
                        else:
                            proposed_code = ai_response.strip()
                    except Exception:
                        proposed_code = orig_source

                if proposed_code:
                    diff_preview = generate_diff(orig_source, proposed_code)
                    description = f"Patch function '{report.target_symbol}' in {Path(target_file).name} to resolve {report.category.value}"

        # 2. Handle Import Errors
        elif report.category == FailureCategory.IMPORT_ERROR:
            strategy = RemediationStrategy.IMPORT_INSERTION
            risk = RiskLevel.LOW
            description = f"Fix import resolution error: {report.error_message}"

        # 3. Handle Test Failures
        elif report.category == FailureCategory.TEST_FAILURE:
            strategy = RemediationStrategy.AST_FUNCTION_REPLACE
            risk = RiskLevel.MEDIUM
            description = f"Remediate failing test assertion in {target_file}"

        # Build validation command
        validation_cmd = custom_validation_cmd
        if not validation_cmd and report.failing_tests:
            validation_cmd = f"python -m unittest {report.failing_tests[0]}"
        elif not validation_cmd and target_file:
            validation_cmd = f"python -c \"import py_compile; py_compile.compile(r'{target_file}', doraise=True)\""

        return RemediationProposal(
            proposal_id=proposal_id,
            category=report.category,
            strategy=strategy,
            risk_level=risk,
            description=description,
            target_file=target_file,
            target_symbol=target_symbol,
            proposed_code=proposed_code,
            diff_preview=diff_preview,
            requires_approval=requires_approval,
            validation_command=validation_cmd,
        )
