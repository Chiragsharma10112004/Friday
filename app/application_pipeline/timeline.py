import json
from datetime import datetime, timezone
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session

from app.application_pipeline.models import ApplicationTimelineEvent
from app.application_pipeline.schemas import TimelineEventType, ApplicationTimelineEventResponse


class TimelineService:
    """
    Event logger and timeline aggregator for tracked applications.
    """

    @classmethod
    def log_event(
        cls,
        db: Session,
        application_id: int,
        event_type: TimelineEventType | str,
        description: str,
        metadata: Optional[Dict[str, Any]] = None,
        now: Optional[datetime] = None
    ) -> ApplicationTimelineEvent:
        now = now or datetime.now(timezone.utc)
        meta_str = json.dumps(metadata or {}, default=str)
        evt_type_val = event_type.value if hasattr(event_type, "value") else str(event_type)

        event = ApplicationTimelineEvent(
            application_id=application_id,
            event_type=evt_type_val,
            timestamp=now,
            description=description,
            event_metadata=meta_str,
            created_at=now,
        )
        db.add(event)
        db.commit()
        db.refresh(event)
        return event

    @classmethod
    def get_events(
        cls,
        db: Session,
        application_id: int,
        limit: int = 100
    ) -> List[ApplicationTimelineEventResponse]:
        events = (
            db.query(ApplicationTimelineEvent)
            .filter(ApplicationTimelineEvent.application_id == application_id)
            .order_by(ApplicationTimelineEvent.timestamp.asc(), ApplicationTimelineEvent.id.asc())
            .limit(limit)
            .all()
        )
        return [e.to_schema() for e in events]

