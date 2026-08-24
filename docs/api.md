# FRIDAY REST API Reference

The FRIDAY backend exposes a high-performance, strongly typed REST API powered by FastAPI.

---

## 1. System & Assistant Endpoints

### `GET /`
- **Description**: Healthcheck endpoint.
- **Response**: `{"message": "Backend running successfully"}`

### `GET /system/info`
- **Description**: System runtime and configuration information.

### `POST /chat`
- **Description**: Conversational assistant interaction.
- **Request Body**: `{"message": "string"}`
- **Response**: `{"response": "string"}`

---

## 2. Candidate Master Profile

### `GET /profile`
- **Description**: Retrieve the user's master candidate profile.
- **Response**: `UserProfileResponse`

### `POST /profile`
- **Description**: Create or update the user's master candidate profile (skills, experience, projects, education, preferences).
- **Request Body**: `UserProfileCreate`
- **Response**: `UserProfileResponse`

---

## 3. Job Analysis & Tracking

### `POST /jobs/analyze`
- **Description**: Analyze a job description against the candidate master profile without persisting.
- **Request Body**: `{"job_description": "string"}`
- **Response**: Match score, recommendation, strong/partial/missing skills, resume focus, interview topics.

### `POST /job-applications/analyze-and-save`
- **Description**: Analyze a job description and optionally persist it to the SQLite application tracker.
- **Request Body**: `AnalyzeAndSaveRequest`
- **Response**: `AnalyzeAndSaveResponse`

---

## 4. Job Ingestion & Scraping (Phase 2)

### `POST /jobs/ingest`
- **Description**: Extract and normalize job details from public URLs with SSRF protection and multi-platform extractors.
- **Request Body**:
```json
{
  "job_url": "https://boards.greenhouse.io/anthropic/jobs/12345"
}
```
- **Response**:
```json
{
  "success": true,
  "source_platform": "greenhouse",
  "data": {
    "company": "Anthropic",
    "role": "AI Systems Engineer",
    "job_description": "Full cleaned job description text...",
    "source_platform": "greenhouse",
    "source_url": "https://boards.greenhouse.io/anthropic/jobs/12345",
    "location": "San Francisco, CA / Remote",
    "confidence": "high"
  },
  "warnings": [],
  "errors": []
}
```

---

## 5. Tailored Application Asset Generation (Phase 3)

### `POST /application-assets/generate`
- **Description**: Generate grounded, tailored application materials (Tailored Resume, Cover Letter, Recruiter Outreach Message, Skill Gap Analysis, Application Summary) based on candidate profile facts and target job requirements.
- **Request Body** (`ApplicationAssetRequest`):
```json
{
  "job_description": "We are seeking a Senior Python Engineer with FastAPI and GenAI experience...",
  "company": "Anthropic",
  "role": "Senior AI Backend Engineer",
  "application_id": null,
  "normalized_job": null,
  "assets": [
    "resume",
    "cover_letter",
    "recruiter_message",
    "skill_gap",
    "application_summary"
  ],
  "cover_letter_style": "standard",
  "message_style": "linkedin",
  "message_tone": "professional"
}
```

---

## 6. Browser-Assisted Application Form Automation (Phase 4)

### `POST /application-automation/inspect`
- **Description**: Stage A: Inspect target job application form, detect ATS platform (Greenhouse, Lever, Oracle CX, Generic), parse visible controls, map verified candidate profile facts, and classify page lifecycle state.
- **Safety Invariant**: Does NOT modify the form and NEVER submits the application (`submission_allowed: false`).

### `POST /application-automation/inspect/{session_id}/refresh`
- **Description**: Re-inspect the active application form session after the candidate completes manual authentication or account registration in their browser.

### `POST /application-automation/fill`
- **Description**: Stage B: Fill ONLY user-approved fields into the active browser session. Leaves the browser on the completed form for final human inspection.
- **Safety Invariant**: Blocked on `AUTH_REQUIRED`, `ACCOUNT_CREATION_REQUIRED`, `CAPTCHA_DETECTED`, `JOB_DETAILS_PAGE`, `FORM_NOT_READY` with `STAGE_TRANSITION_INVALID`. NEVER submits the application (`submission_performed: false`, `manual_submission_required: true`).

---

## 7. Automated Job Discovery & Opportunity Pipeline (Phase 5)

### `POST /job-discovery/search`
- **Description**: Query configured public job providers (Greenhouse, Lever), deduplicate results, match and rank against candidate profile, and store unique opportunities.

### `POST /job-discovery/manual`
- **Description**: Batch ingest one or more manual job URLs through Phase 2 ingestion, rank against profile, and persist opportunities.

### `GET /opportunities`
- **Description**: List discovered opportunities with server-side filtering, sorting, and pagination.

### `GET /opportunities/{opportunity_id}`
- **Description**: Retrieve detailed opportunity record.

### `PATCH /opportunities/{opportunity_id}/status`
- **Description**: Update opportunity status with strict transition validation.

### `POST /opportunities/{opportunity_id}/analyze`
- **Description**: Trigger deep Phase 1 job analysis on opportunity and advance lifecycle to `ANALYZED`.

### `POST /opportunities/{opportunity_id}/generate-assets`
- **Description**: Generate Phase 3 tailored application assets for opportunity and advance lifecycle to `ASSETS_GENERATED`.

### `POST /opportunities/{opportunity_id}/prepare-application`
- **Description**: Inspect opportunity application page via Phase 4 automation and advance lifecycle to `READY_TO_APPLY`.

---

## 8. Application Pipeline & Job Tracking (Phase 6)

### `POST /applications`
- **Description**: Create a tracked application record manually.

### `POST /applications/from-opportunity/{opportunity_id}`
- **Description**: Convert a Phase 5 discovered opportunity into a tracked application.

### `GET /applications`
- **Description**: List tracked applications with filtering, sorting, and pagination.

### `GET /applications/summary`
- **Description**: Pipeline overview metrics, status and priority counts, company breakdown, and follow-up/referral totals.

### `GET /applications/dashboard`
- **Description**: Backward-compatible summary dashboard.

### `GET /applications/follow-ups`
- **Description**: Retrieve categorized follow-ups (`scheduled`, `due`, `overdue`) using timezone-aware calculations.

### `GET /applications/{application_id}`
- **Description**: Retrieve single application record.

### `PATCH /applications/{application_id}`
- **Description**: Update application metadata (company, role, priority, notes, etc.) with duplicate check protection.

### `POST /applications/{application_id}/status`
- **Description**: Validated lifecycle status transition. Rejects invalid state jumps with `INVALID_STATUS_TRANSITION`.

### `POST /applications/{application_id}/mark-applied`
- **Description**: Mark application as `APPLIED` idempotently, set `applied_at` timestamp, and create timeline event.

### `GET /applications/{application_id}/timeline`
- **Description**: Retrieve chronological audit log of all events for this application.

### `POST /applications/{application_id}/notes`
- **Description**: Add a timestamped audit note to the application record and timeline.

### `POST /applications/{application_id}/referral`
- **Description**: Add or update referral tracking status, contact metadata, and dates.

### `POST /applications/{application_id}/follow-up`
- **Description**: Schedule follow-up reminder date.

### `POST /applications/{application_id}/follow-up/complete`
- **Description**: Mark active follow-up reminder completed.

### `POST /applications/{application_id}/interviews`
- **Description**: Schedule an interview round for the application.

### `GET /applications/{application_id}/interviews`
- **Description**: List all scheduled and past interview rounds for the application.

### `PATCH /applications/{application_id}/interviews/{interview_id}`
- **Description**: Update interview round details, status, or notes.

---

## 9. Proactive Career Intelligence & Next-Action System (Phase 7)

### `GET /career-intelligence/today`
- **Description**: Returns today's complete, prioritized action queue sorted by priority (`URGENT`, `HIGH`, `MEDIUM`, `LOW`) and score descending.
- **Response** (`TodayActionQueueResponse`):
```json
{
  "success": true,
  "date": "2026-08-24",
  "summary": "You have 1 urgent action(s) and 2 high-priority action(s) today.",
  "action_count": 3,
  "urgent_count": 1,
  "high_priority_count": 2,
  "actions": [
    {
      "id": 1,
      "type": "FOLLOW_UP_OVERDUE",
      "priority": "URGENT",
      "title": "Follow-up Overdue: Scale AI",
      "description": "Your scheduled follow-up for Data Engine Architect at Scale AI is overdue.",
      "reason": "Follow-up date 2026-08-23 has passed without completion.",
      "recommended_action": "Contact the recruiter or recruiter contact for Scale AI today.",
      "score": 95,
      "application_id": 1,
      "opportunity_id": null,
      "status": "ACTIVE",
      "created_at": "2026-08-24T12:00:00Z",
      "updated_at": "2026-08-24T12:00:00Z",
      "metadata": {
        "company": "Scale AI",
        "role": "Data Engine Architect",
        "status": "APPLIED"
      }
    }
  ]
}
```

### `GET /career-intelligence/next-actions`
- **Description**: Query active recommendations with optional filters by priority, recommendation type, application ID, or opportunity ID.
- **Response**: `List[ActionItemResponse]`.

### `GET /career-intelligence/dashboard`
- **Description**: Returns holistic career intelligence overview including healthy, attention-needed, stale, and critical application counts, urgent action totals, overdue follow-ups, upcoming interviews, pending referrals, and average application health.
- **Response**: `DashboardIntelligenceResponse`.

### `GET /career-intelligence/application-health`
- **Description**: Evaluates and returns health diagnostics across all active job applications.
- **Response**: `ApplicationHealthListResponse`.

### `GET /career-intelligence/application-health/{application_id}`
- **Description**: Returns detailed health diagnostic evaluation (`EXCELLENT`, `HEALTHY`, `ATTENTION_NEEDED`, `STALE`, `CRITICAL`), diagnostic score (0-100), reasons, and recommended action for a single application.
- **Response**: `ApplicationHealthItem`.

### `GET /career-intelligence/daily-briefing`
- **Description**: Generates a deterministic daily executive briefing containing summary, applications requiring action, overdue follow-ups, upcoming interviews, top opportunities, and next actions.
- **Response**: `DailyBriefingResponse`.

### `GET /career-intelligence/weekly-briefing`
- **Description**: Generates a weekly pipeline performance summary containing weekly created/applied totals, interviewing counts, offers, rejections, average match score, top companies, status distributions, and recommended focus areas.
- **Response**: `WeeklyBriefingResponse`.

### `POST /career-intelligence/recommendations/{recommendation_id}/dismiss`
- **Description**: Dismiss an active recommendation. Applies a 7-day cooldown preventing repetitive recommendation spam.
- **Response**: `ActionItemResponse`.

### `POST /career-intelligence/recommendations/{recommendation_id}/complete`
- **Description**: Mark an active recommendation as completed.
- **Response**: `ActionItemResponse`.

### `POST /career-intelligence/recommendations/refresh`
- **Description**: Deterministically recalculates recommendations across all applications and opportunities. Creates new recommendations, updates existing active recommendations, and expires invalid ones. Never performs external network calls or status transitions.
- **Response**: `RefreshResponse`.
