import os
import re
from pathlib import Path
from typing import Optional, List, Dict, Any


class ExecutionGuard:
    """
    Guarantees execution safety, sandbox path restrictions, command blocking,
    and credential leak prevention.
    """

    FORBIDDEN_COMMAND_PATTERNS = [
        re.compile(r'\b(rm\s+-[rRfF]+|rmdir\s+/s|format\s+[c-z]:|mkfs|dd\s+if=)\b', re.I),
        re.compile(r':\(\)\s*\{\s*:\s*\|\s*:\s*&\s*\}\s*;\s*:', re.I),  # fork bomb
        re.compile(r'\b(cat|type|more|less)\s+.*\.env\b', re.I),        # secret dumping
        re.compile(r'\b(shutdown|reboot|init\s+0)\b', re.I),
    ]

    SECRET_MASKS = [
        (re.compile(r'(?i)(password|secret|token|api_key|private_key)\s*[:=]\s*[\'"][^\'"]+[\'"]'), r'\1: "[REDACTED_SECRET]"'),
        (re.compile(r'Bearer\s+[A-Za-z0-9\-._~+/]+=*'), '[REDACTED_BEARER_TOKEN]'),
    ]

    @classmethod
    def is_path_safe(cls, target_path: str, workspace_root: Optional[str] = None) -> bool:
        """
        Validates that target_path is within the permitted workspace directory.
        """
        try:
            root = Path(workspace_root or ".").resolve()
            resolved = Path(target_path).resolve()
            # Must be equal to or a subpath of root
            return resolved == root or root in resolved.parents
        except Exception:
            return False

    @classmethod
    def validate_command(cls, command: str) -> Dict[str, Any]:
        """
        Validates whether a shell command is safe to execute.
        """
        cmd_strip = command.strip()
        for pat in cls.FORBIDDEN_COMMAND_PATTERNS:
            if pat.search(cmd_strip):
                return {
                    "safe": False,
                    "reason": f"Command contains potentially dangerous or destructive patterns: {pat.pattern}"
                }
        return {"safe": True, "reason": "Command passed safety validation."}

    @classmethod
    def mask_secrets(cls, text: str) -> str:
        """Redacts sensitive credentials and tokens."""
        if not text:
            return ""
        masked = text
        for pat, repl in cls.SECRET_MASKS:
            masked = pat.sub(repl, masked)
        return masked
