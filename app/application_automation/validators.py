from typing import List, Dict, Set
from app.application_automation.schemas import FieldInspectionItem, FieldStatus
from app.application_automation.errors import AutomationErrorCode, AutomationException


class AutomationSafetyValidator:
    """
    Guards and validates field approvals and session state prior to browser interactions.
    """

    SUBMIT_KEYWORDS: Set[str] = {
        "submit",
        "apply",
        "submit_application",
        "submit_app",
        "send_application",
        "finish_application",
    }

    @classmethod
    def assert_no_submit_action(cls, field_id: str, label: str = ""):
        """
        Hard safety invariant: Ensure no submit trigger is executed.
        """
        combined = f"{field_id} {label}".lower()
        if any(kw in combined for kw in cls.SUBMIT_KEYWORDS):
            raise AutomationException(
                code=AutomationErrorCode.SUBMISSION_BLOCKED,
                message="Automated submission is strictly forbidden. The final application must be submitted manually."
            )

    @classmethod
    def validate_approved_fields(
        cls,
        approved_ids: List[str],
        inspected_fields: List[FieldInspectionItem],
        custom_answers: Dict[str, str] = None
    ) -> List[FieldInspectionItem]:
        """
        Filter and return only valid, inspected fields that the user explicitly approved.
        """
        custom_answers = custom_answers or {}
        field_map = {item.field_id: item for item in inspected_fields}
        validated_items: List[FieldInspectionItem] = []

        for fid in approved_ids:
            if fid not in field_map:
                raise AutomationException(
                    code=AutomationErrorCode.FIELD_NOT_FOUND,
                    message=f"Approved field ID '{fid}' was not found in the inspected form session."
                )

            item = field_map[fid]
            cls.assert_no_submit_action(item.field_id, item.label)

            # If user provided a custom answer, override suggested value
            if fid in custom_answers:
                item.suggested_value = custom_answers[fid]
                item.status = FieldStatus.AUTO_FILL_READY

            # Check if there is a non-empty value to fill
            if not item.suggested_value or not str(item.suggested_value).strip():
                raise AutomationException(
                    code=AutomationErrorCode.MANUAL_INPUT_REQUIRED,
                    message=f"Field '{item.label}' ({item.field_id}) has no candidate value to fill."
                )

            validated_items.append(item)

        return validated_items

