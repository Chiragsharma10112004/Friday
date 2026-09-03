import logging
from pathlib import Path
from typing import Optional, Dict, Any

from app.core.self_healing.schemas import (
    RemediationProposal,
    RemediationResult,
    RecoveryStatus,
    RemediationStrategy,
)
from app.core.self_healing.errors import SelfHealingException, SelfHealingErrorCode
from app.core.editor.editor import replace_function
from app.core.editor.validator import validate_ast
from app.core.editor.retry import repair_code
from app.core.execution.terminal import run_command

logger = logging.getLogger("friday.self_healing.executor")


class RemediationExecutor:
    """
    Safely applies remediation proposals with automated pre-edit backups,
    isolated AST verification, validation test runs, rollback on regression, and escalation handling.
    """

    MAX_RETRIES = 2

    @classmethod
    def execute(
        cls,
        proposal: RemediationProposal,
        approved: bool = True,
        max_retries: int = MAX_RETRIES,
    ) -> RemediationResult:
        if proposal.requires_approval and not approved:
            return RemediationResult(
                proposal_id=proposal.proposal_id,
                status=RecoveryStatus.PENDING_APPROVAL,
                strategy_applied=proposal.strategy,
                target_file=proposal.target_file,
                validation_passed=False,
                error="Remediation requires explicit approval before execution.",
            )

        target_path = Path(proposal.target_file)
        if not target_path.exists() or not target_path.is_file():
            return RemediationResult(
                proposal_id=proposal.proposal_id,
                status=RecoveryStatus.ESCALATED,
                strategy_applied=proposal.strategy,
                target_file=proposal.target_file,
                validation_passed=False,
                error=f"Target file '{proposal.target_file}' does not exist.",
            )

        # 1. Take snapshot backup of original content for safe rollback
        backup_content = target_path.read_text(encoding="utf-8", errors="ignore")
        current_code = proposal.proposed_code
        attempts = 0
        diff_applied = proposal.diff_preview

        while attempts <= max_retries:
            attempts += 1
            logger.info(f"Applying remediation attempt {attempts}/{max_retries+1} on {target_path.name}")

            # 2. AST Validation prior to file write
            if current_code and proposal.strategy == RemediationStrategy.AST_FUNCTION_REPLACE:
                val = validate_ast(current_code)
                if not val.get("valid"):
                    logger.warning(f"AST validation failed on attempt {attempts}: {val.get('error')}")
                    # Try syntax repair
                    repaired = repair_code(
                        original_prompt=proposal.description,
                        generated_code=current_code
                    )
                    if repaired.get("success"):
                        current_code = repaired.get("code")
                    else:
                        continue

            # 3. Apply modification
            apply_success = False
            if proposal.strategy == RemediationStrategy.AST_FUNCTION_REPLACE and proposal.target_symbol:
                res = replace_function(
                    function_name=proposal.target_symbol,
                    new_source=current_code,
                    root=str(target_path.parent),
                    preview=False,
                )
                apply_success = res.get("success", False)
                diff_applied = res.get("diff")
            elif current_code:
                try:
                    target_path.write_text(current_code, encoding="utf-8")
                    apply_success = True
                except Exception as e:
                    logger.error(f"Failed to write file {target_path}: {e}")
                    apply_success = False

            if not apply_success:
                logger.warning(f"Failed to apply modification on attempt {attempts}")
                continue

            # 4. Run validation command
            validation_passed = True
            validation_output = "No validation command specified."
            if proposal.validation_command:
                val_res = run_command(proposal.validation_command, timeout=20)
                validation_passed = val_res.get("success", False)
                validation_output = val_res.get("stdout", "") or val_res.get("stderr", "") or val_res.get("error", "")

            # 5. Check if successful
            if validation_passed:
                logger.info(f"Self-healing successfully remediated {target_path.name} on attempt {attempts}")
                return RemediationResult(
                    proposal_id=proposal.proposal_id,
                    status=RecoveryStatus.RECOVERED,
                    strategy_applied=proposal.strategy,
                    target_file=proposal.target_file,
                    diff_applied=diff_applied,
                    validation_passed=True,
                    validation_output=validation_output,
                    attempts=attempts,
                )
            else:
                logger.warning(f"Validation failed on attempt {attempts}: {validation_output}")

        # 6. If all attempts failed, rollback to pristine original state
        logger.error(f"All remediation attempts failed for {target_path.name}. Performing automated rollback.")
        try:
            target_path.write_text(backup_content, encoding="utf-8")
            status = RecoveryStatus.ROLLED_BACK
        except Exception as e:
            logger.critical(f"Rollback failed: {e}")
            status = RecoveryStatus.ESCALATED

        return RemediationResult(
            proposal_id=proposal.proposal_id,
            status=status,
            strategy_applied=proposal.strategy,
            target_file=proposal.target_file,
            diff_applied=diff_applied,
            validation_passed=False,
            validation_output=validation_output,
            attempts=attempts,
            error=f"Remediation could not be validated after {attempts} attempts. File was rolled back.",
        )
