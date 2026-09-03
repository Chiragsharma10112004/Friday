import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from app.core.self_healing.schemas import DiagnosticReport, FailureCategory, RiskLevel
from app.core.self_healing.classifier import FailureClassifier


class DiagnosticCollector:
    """
    Collects diagnostics from exceptions, tracebacks, and test failures.
    Extracts relevant file locations, code contexts, and failing test cases without exposing secrets.
    """

    SECRET_PATTERNS = [
        (re.compile(r'(?i)(password|secret|key|token|api_key)\s*[:=]\s*[\'"][^\'"]+[\'"]'), r'\1: "[REDACTED_SECRET]"'),
        (re.compile(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*'), '[REDACTED_BEARER_TOKEN]'),
    ]

    @classmethod
    def sanitize(cls, text: str) -> str:
        """Redacts sensitive values and API tokens from diagnostic messages."""
        if not text:
            return ""
        sanitized = text
        for pat, repl in cls.SECRET_PATTERNS:
            sanitized = pat.sub(repl, sanitized)
        return sanitized

    @classmethod
    def extract_file_and_line(cls, traceback_text: str) -> Tuple[Optional[str], Optional[int], Optional[str]]:
        """Extracts the innermost project file, line number, and function from a traceback."""
        if not traceback_text:
            return None, None, None

        # Look for File "path", line X, in Y
        matches = re.findall(r'File "([^"]+)", line (\d+)(?:, in (\w+))?', traceback_text)
        if not matches:
            return None, None, None

        target_file = None
        target_line = None
        target_symbol = None

        for path_str, line_str, func_str in reversed(matches):
            if "site-packages" not in path_str and "<frozen" not in path_str:
                target_file = path_str
                target_line = int(line_str)
                target_symbol = func_str if func_str and func_str != "<module>" else None
                break

        if not target_file and matches:
            path_str, line_str, func_str = matches[-1]
            target_file = path_str
            target_line = int(line_str)
            target_symbol = func_str if func_str and func_str != "<module>" else None

        return target_file, target_line, target_symbol

    @classmethod
    def get_context_code(cls, file_path: str, line_no: int, window: int = 5) -> Optional[str]:
        """Reads lines surrounding the error location for context."""
        try:
            p = Path(file_path)
            if not p.exists() or not p.is_file():
                return None
            lines = p.read_text(encoding="utf-8", errors="ignore").splitlines()
            start = max(0, line_no - window - 1)
            end = min(len(lines), line_no + window)
            snippet_lines = []
            for i in range(start, end):
                prefix = ">>" if (i + 1) == line_no else "  "
                snippet_lines.append(f"{prefix} {i+1:4d}: {lines[i]}")
            return "\n".join(snippet_lines)
        except Exception:
            return None

    @classmethod
    def collect_from_traceback(
        cls,
        error_message: str,
        traceback_text: str,
        error_type: Optional[str] = None
    ) -> DiagnosticReport:
        clean_msg = cls.sanitize(error_message)
        clean_tb = cls.sanitize(traceback_text)

        category, _ = FailureClassifier.classify(clean_msg, clean_tb, error_type)
        target_file, target_line, target_symbol = cls.extract_file_and_line(clean_tb)

        context_code = None
        if target_file and target_line:
            context_code = cls.get_context_code(target_file, target_line)

        # Extract failing test names if present
        failing_tests = re.findall(r'(?:FAIL|ERROR):\s+(test_\w+)', clean_tb)

        return DiagnosticReport(
            category=category,
            error_type=error_type or "Exception",
            error_message=clean_msg,
            target_file=target_file,
            target_line=target_line,
            target_symbol=target_symbol,
            stack_trace_snippet=clean_tb[-1000:] if clean_tb else None,
            context_code=context_code,
            failing_tests=failing_tests,
        )
