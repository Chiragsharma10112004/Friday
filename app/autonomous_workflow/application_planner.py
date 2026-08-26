from typing import List, Optional
from app.autonomous_workflow.schemas import WorkflowPlanStep, WorkflowPlanResponse
from app.autonomous_workflow.models import AutonomousWorkflow


class ApplicationPlanner:
    """
    Synthesizes custom application execution plans based on target job characteristics,
    candidate profile, and platform capabilities.
    """

    @classmethod
    def create_execution_plan(
        cls,
        workflow: AutonomousWorkflow,
        has_referral: bool = False,
        source_url: Optional[str] = None
    ) -> WorkflowPlanResponse:
        steps: List[WorkflowPlanStep] = []

        # 1. Resume Generation
        steps.append(
            WorkflowPlanStep(
                step="GENERATE_RESUME",
                required=True,
                approval_required=False,
                recommended=True,
                automation_allowed=True,
                description="Synthesize profile-grounded tailored resume bullet points and summary."
            )
        )

        # 2. Cover Letter Generation
        steps.append(
            WorkflowPlanStep(
                step="GENERATE_COVER_LETTER",
                required=False,
                approval_required=False,
                recommended=True,
                automation_allowed=True,
                description="Generate role-tailored cover letter highlighting candidate strengths."
            )
        )

        # 3. Referral Recommendation
        if not has_referral:
            steps.append(
                WorkflowPlanStep(
                    step="REQUEST_REFERRAL",
                    required=False,
                    approval_required=False,
                    recommended=True,
                    automation_allowed=False,
                    description="Identify company connections and draft outreach message."
                )
            )

        # 4. Form Inspection
        steps.append(
            WorkflowPlanStep(
                step="INSPECT_APPLICATION",
                required=True,
                approval_required=False,
                recommended=True,
                automation_allowed=True,
                description="Inspect form controls, verify platform adapter, and detect checkpoints."
            )
        )

        # 5. Safe Autofill
        steps.append(
            WorkflowPlanStep(
                step="AUTOFILL_SAFE_FIELDS",
                required=True,
                approval_required=True,
                recommended=True,
                automation_allowed=True,
                description="Autofill only approved non-sensitive candidate profile fields."
            )
        )

        # 6. Manual Submission Checkpoint (Hard Invariant)
        steps.append(
            WorkflowPlanStep(
                step="MANUAL_SUBMISSION",
                required=True,
                approval_required=True,
                recommended=True,
                automation_allowed=False,
                description="Final review and submission strictly performed by the candidate in browser."
            )
        )

        return WorkflowPlanResponse(
            workflow_id=workflow.id,
            company=workflow.company,
            role=workflow.role,
            plan=steps
        )
