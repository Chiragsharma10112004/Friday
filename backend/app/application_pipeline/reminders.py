from datetime import datetime, timezone, date
from typing import Optional

from app.application_pipeline.schemas import FollowUpStatus


class FollowUpManager:
    """
    Computes dynamic follow-up status based on scheduled follow-up dates and current time.
    """

    @classmethod
    def calculate_follow_up_status(
        cls,
        next_follow_up_date: Optional[datetime],
        current_status: Optional[FollowUpStatus] = None,
        now: Optional[datetime] = None
    ) -> FollowUpStatus:
        if current_status == FollowUpStatus.COMPLETED:
            return FollowUpStatus.COMPLETED

        if not next_follow_up_date:
            return FollowUpStatus.NONE

        now = now or datetime.now(timezone.utc)

        # Normalize to UTC dates for calendar comparison
        if next_follow_up_date.tzinfo is None:
            follow_up_utc = next_follow_up_date.replace(tzinfo=timezone.utc)
        else:
            follow_up_utc = next_follow_up_date.astimezone(timezone.utc)

        now_utc = now.astimezone(timezone.utc) if now.tzinfo else now.replace(tzinfo=timezone.utc)

        follow_up_day = follow_up_utc.date()
        today = now_utc.date()

        if follow_up_day > today:
            return FollowUpStatus.SCHEDULED
        elif follow_up_day == today:
            return FollowUpStatus.DUE
        else:
            return FollowUpStatus.OVERDUE

