from typing import List, Tuple
from app.profile.models import UserProfile
from app.application_automation.schemas import (
    FormPlatform,
    InspectionStatus,
    FieldInspectionItem,
    FieldConfidence,
    FieldStatus,
    InspectApplicationResponse,
)
from app.application_automation.field_mapping import FieldMapper


class FormPreviewCompiler:
    """
    Synthesizes detected DOM controls and candidate profile ground truth into a structured,
    auditable human-in-the-loop preview.
    """

    @classmethod
    def compile_preview(
        cls,
        session_id: str,
        platform: FormPlatform,
        page_url: str,
        raw_fields: List[FieldInspectionItem],
        profile: UserProfile,
        page_title: str = "",
        extra_warnings: List[str] = None
    ) -> InspectApplicationResponse:
        warnings = list(extra_warnings or [])
        compiled_fields: List[FieldInspectionItem] = []

        auto_ready = 0
        approval_req = 0
        manual_req = 0
        unsupported = 0

        for item in raw_fields:
            # 1. Resolve canonical mapping key
            canonical_key = FieldMapper.match_canonical_field(
                label=item.label,
                html_name=item.html_name or "",
                control_type=item.control_type
            )

            # 2. Resolve candidate profile fact
            (
                val,
                src,
                conf,
                status,
                is_sens,
                notice
            ) = FieldMapper.resolve_candidate_value(
                canonical_key=canonical_key,
                profile=profile,
                label=item.label,
                html_name=item.html_name or "",
                control_type=item.control_type,
            )

            item.normalized_field = canonical_key
            item.suggested_value = val
            item.source = src
            item.confidence = conf
            item.status = status
            item.is_sensitive = is_sens
            item.requires_approval = (status != FieldStatus.AUTO_FILL_READY)
            item.validation_notice = notice

            # Update count metrics
            if status == FieldStatus.AUTO_FILL_READY:
                auto_ready += 1
            elif status == FieldStatus.APPROVAL_REQUIRED:
                approval_req += 1
            elif status == FieldStatus.MANUAL_REQUIRED:
                manual_req += 1
            else:
                unsupported += 1

            compiled_fields.append(item)

        if manual_req > 0:
            warnings.append(
                f"{manual_req} field(s) require manual review (e.g. demographic, compensation, or unmapped questions)."
            )

        return InspectApplicationResponse(
            success=True,
            session_id=session_id,
            platform=platform,
            status=InspectionStatus.PREVIEW_READY,
            page_url=page_url,
            page_title=page_title,
            fields=compiled_fields,
            auto_fill_ready_count=auto_ready,
            approval_required_count=approval_req,
            manual_required_count=manual_req,
            unsupported_count=unsupported,
            warnings=warnings,
            errors=[],
            submission_allowed=False,  # Hard invariant: NEVER allow automated final submission
        )

