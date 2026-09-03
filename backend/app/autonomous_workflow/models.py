import json
from datetime import datetime, timezone
from typing import Dict, Any, Optional, List

from sqlalchemy import Column, Integer, String, Text, Boolean, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.memory.database import Base
from app.autonomous_workflow.schemas import (
    WorkflowStatus,
    WorkflowPriority,
    WorkflowStepStatus,
    ApprovalType,
    ApprovalStatus,
    WorkflowActionType,
    WorkflowResponse,
    WorkflowStepResponse,
    WorkflowApprovalResponse,
    WorkflowActionLogResponse,
)


class AutonomousWorkflow(Base):
    __tablename__ = "autonomous_workflows"

    id = Column(Integer, primary_key=True, index=True)
    profile_id = Column(Integer, nullable=True, index=True)
    application_id = Column(Integer, nullable=True, index=True)
    opportunity_id = Column(Integer, nullable=True, index=True)

    company = Column(String(255), nullable=False, index=True)
    role = Column(String(255), nullable=False, index=True)
    source_url = Column(String(1024), nullable=True)
    source_platform = Column(String(100), nullable=True)

    workflow_status = Column(String(50), nullable=False, default=WorkflowStatus.CREATED.value, index=True)
    workflow_priority = Column(String(20), nullable=False, default=WorkflowPriority.MEDIUM.value, index=True)

    match_score = Column(Integer, nullable=True)
    recommendation_score = Column(Integer, nullable=True)

    current_step = Column(String(100), nullable=True)
    next_action = Column(String(255), nullable=True)

    approval_required = Column(Boolean, default=False, nullable=False)
    user_action_required = Column(Boolean, default=False, nullable=False)

    paused = Column(Boolean, default=False, nullable=False)
    pause_reason = Column(String(100), nullable=True)

    retry_count = Column(Integer, default=0, nullable=False)
    last_error = Column(Text, nullable=True)

    metadata_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    paused_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    steps = relationship("WorkflowStep", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowStep.step_order")
    approvals = relationship("WorkflowApproval", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowApproval.created_at.desc()")
    action_logs = relationship("WorkflowActionLog", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowActionLog.timestamp.desc()")
    retries = relationship("WorkflowRetry", back_populates="workflow", cascade="all, delete-orphan", order_by="WorkflowRetry.created_at.desc()")

    def to_schema(self) -> WorkflowResponse:
        meta = json.loads(self.metadata_json) if self.metadata_json else {}

        try:
            w_status = WorkflowStatus(self.workflow_status)
        except ValueError:
            w_status = WorkflowStatus.CREATED

        try:
            w_priority = WorkflowPriority(self.workflow_priority)
        except ValueError:
            w_priority = WorkflowPriority.MEDIUM

        return WorkflowResponse(
            id=self.id,
            profile_id=self.profile_id,
            application_id=self.application_id,
            opportunity_id=self.opportunity_id,
            company=self.company,
            role=self.role,
            source_url=self.source_url,
            source_platform=self.source_platform,
            workflow_status=w_status,
            workflow_priority=w_priority,
            match_score=self.match_score,
            recommendation_score=self.recommendation_score,
            current_step=self.current_step,
            next_action=self.next_action,
            approval_required=self.approval_required,
            user_action_required=self.user_action_required,
            paused=self.paused,
            pause_reason=self.pause_reason,
            retry_count=self.retry_count,
            last_error=self.last_error,
            created_at=self.created_at,
            updated_at=self.updated_at,
            started_at=self.started_at,
            completed_at=self.completed_at,
            paused_at=self.paused_at,
            metadata=meta,
        )


class WorkflowStep(Base):
    __tablename__ = "workflow_steps"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("autonomous_workflows.id", ondelete="CASCADE"), nullable=False, index=True)

    step_name = Column(String(100), nullable=False)
    step_order = Column(Integer, nullable=False, default=1)

    status = Column(String(50), nullable=False, default=WorkflowStepStatus.PENDING.value)

    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    retry_count = Column(Integer, default=0, nullable=False)
    error_message = Column(Text, nullable=True)

    metadata_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    workflow = relationship("AutonomousWorkflow", back_populates="steps")

    def to_schema(self) -> WorkflowStepResponse:
        meta = json.loads(self.metadata_json) if self.metadata_json else {}

        try:
            s_status = WorkflowStepStatus(self.status)
        except ValueError:
            s_status = WorkflowStepStatus.PENDING

        return WorkflowStepResponse(
            id=self.id,
            workflow_id=self.workflow_id,
            step_name=self.step_name,
            step_order=self.step_order,
            status=s_status,
            started_at=self.started_at,
            completed_at=self.completed_at,
            retry_count=self.retry_count,
            error_message=self.error_message,
            metadata=meta,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class WorkflowApproval(Base):
    __tablename__ = "workflow_approvals"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("autonomous_workflows.id", ondelete="CASCADE"), nullable=False, index=True)

    approval_type = Column(String(100), nullable=False, index=True)
    status = Column(String(50), nullable=False, default=ApprovalStatus.PENDING.value, index=True)

    requested_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)
    rejected_at = Column(DateTime(timezone=True), nullable=True)

    approved_by = Column(String(100), nullable=True)
    reason = Column(Text, nullable=True)
    metadata_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    workflow = relationship("AutonomousWorkflow", back_populates="approvals")

    def to_schema(self) -> WorkflowApprovalResponse:
        meta = json.loads(self.metadata_json) if self.metadata_json else {}

        try:
            app_type = ApprovalType(self.approval_type)
        except ValueError:
            app_type = ApprovalType.APPLICATION_APPROVAL

        try:
            app_status = ApprovalStatus(self.status)
        except ValueError:
            app_status = ApprovalStatus.PENDING

        return WorkflowApprovalResponse(
            id=self.id,
            workflow_id=self.workflow_id,
            approval_type=app_type,
            status=app_status,
            requested_at=self.requested_at,
            approved_at=self.approved_at,
            rejected_at=self.rejected_at,
            approved_by=self.approved_by,
            reason=self.reason,
            metadata=meta,
            created_at=self.created_at,
            updated_at=self.updated_at,
        )


class WorkflowActionLog(Base):
    __tablename__ = "workflow_action_logs"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("autonomous_workflows.id", ondelete="CASCADE"), nullable=False, index=True)

    action_type = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=False)
    status = Column(String(50), nullable=False, default="SUCCESS")

    timestamp = Column(DateTime(timezone=True), server_default=func.now())
    metadata_json = Column(Text, nullable=True)

    workflow = relationship("AutonomousWorkflow", back_populates="action_logs")

    def to_schema(self) -> WorkflowActionLogResponse:
        meta = json.loads(self.metadata_json) if self.metadata_json else {}

        try:
            act_type = WorkflowActionType(self.action_type)
        except ValueError:
            act_type = WorkflowActionType.WORKFLOW_CREATED

        return WorkflowActionLogResponse(
            id=self.id,
            workflow_id=self.workflow_id,
            action_type=act_type,
            description=self.description,
            status=self.status,
            timestamp=self.timestamp,
            metadata=meta,
        )


class WorkflowRetry(Base):
    __tablename__ = "workflow_retries"

    id = Column(Integer, primary_key=True, index=True)
    workflow_id = Column(Integer, ForeignKey("autonomous_workflows.id", ondelete="CASCADE"), nullable=False, index=True)
    step_id = Column(Integer, nullable=True)

    retry_type = Column(String(100), nullable=False)
    attempt_number = Column(Integer, nullable=False, default=1)
    error_message = Column(Text, nullable=True)

    retry_at = Column(DateTime(timezone=True), server_default=func.now())
    status = Column(String(50), nullable=False, default="PENDING")

    created_at = Column(DateTime(timezone=True), server_default=func.now())

    workflow = relationship("AutonomousWorkflow", back_populates="retries")
