# FRIDAY System Architecture

## Overview

FRIDAY is a modular personal AI assistant and Job Application Automation Platform built with FastAPI, SQLite/SQLAlchemy, and a resilient multi-provider AI gateway.

---

## Core Subsystems

### 1. AI Provider Gateway (`app/core/providers/`, `app/core/brain/manager.py`)
- **Abstract Base**: `BaseAIProvider` (`generate`, `is_available`, `provider_name`).
- **Implementations**:
  - `OllamaProvider`: Local high-performance inference (`llama3.2:3b`, etc.).
  - `GeminiProvider`: Cloud multimodal LLMs with Google GenAI SDK & REST API fallback.
  - `OpenRouterProvider`: Unified router across open & proprietary models.
- **Failover**: Automatic primary-to-secondary fallbacks for mission-critical tasks (`task="job_analysis"`, `task="asset_generation"`).

### 2. Candidate Master Profile (`app/profile/`)
- Single source of verified candidate ground truth (skills, projects, work experience, education, target roles).
- Strict truthfulness invariants: Prevents LLM generation from inventing non-existent skills, degrees, or employers.

### 3. Job Ingestion & Extraction Engine (`app/ingestion/`)
- **SSRF Hardening**: DNS pre-resolution blocks private, loopback, link-local, and cloud metadata hostnames (`169.254.169.254`, etc.) with manual redirect re-validation.
- **Extractors**:
  - `GreenhouseExtractor`: Public Boards API + JSON-LD + Semantic HTML.
  - `LeverExtractor`: Public Postings API + JSON-LD + Semantic HTML.
  - `WorkdayExtractor`: Server-rendered JSON-LD with structured client-side rendering notices.
  - `LinkedInExtractor` & `IndeedExtractor`: Ethical, structured access-restricted notices.
  - `GenericExtractor`: Schema.org `JobPosting` JSON-LD + OpenGraph + semantic HTML parser.

### 4. Tailored Application Asset Generation (`app/application_assets/`)
- **Isolation & Anti-Injection**: Untrusted external job postings are strictly encapsulated inside `<UNTRUSTED_JOB_DATA>` blocks with system instructions forbidding directive execution.
- **Conservative Grounding**: All generated claims are verified against the candidate profile and categorized into `VERIFIED_CANDIDATE_FACT`, `REWRITE_OF_CANDIDATE_FACT`, or `SUGGESTED_POSITIONING`.
- **Assets Synthesized**:
  1. *Tailored Resume Content* (summary, prioritized skills, tailored projects, keywords).
  2. *Custom Cover Letter* (aligned with tone and specific company/role highlights).
  3. *Recruiter Outreach Message* (LinkedIn, Email, or DM with character count limits).
  4. *Skill Gap Analysis* (priority gaps, required vs candidate skills, learning actions).
  5. *Application Fit Summary* (selling points, potential concerns, apply recommendation).
- **Graceful Fallback**: If LLM output fails schema validation, the system falls back to a deterministic profile-grounded asset bundle without breaking the user request.

### 5. Browser-Assisted Application Form Automation (`app/application_automation/`)
- **Two-Stage Human-in-the-Loop Model**:
  - **Stage A (Inspect & Preview)**: Detects ATS platform (Greenhouse, Lever, Oracle CX, Generic), parses DOM controls, maps candidate profile facts deterministically, and classifies page lifecycle state (`PREVIEW_READY`, `JOB_DETAILS_PAGE`, `ACCOUNT_CREATION_REQUIRED`, `AUTH_REQUIRED`, `EMAIL_VERIFICATION_REQUIRED`, `CAPTCHA_DETECTED`, `ACCESS_RESTRICTED`, `FORM_NOT_READY`).
  - **Stage B (Fill Approved Fields)**: Revalidates session and fills ONLY the explicitly approved fields, leaving the browser open on the completed page. Blocked on non-fillable checkpoints with `STAGE_TRANSITION_INVALID`.
- **Session Refresh Flow**: `POST /application-automation/inspect/{session_id}/refresh` allows re-inspecting active sessions after the user completes manual authentication or registration in their browser.
- **Sensitive Question Policy**: Passwords, OTP codes, demographic, salary, veteran, disability, and criminal history questions are strictly marked `MANUAL_REQUIRED`. Never stores or logs passwords or OTPs.
- **Absolute Submission Safety Guarantee**: `submission_allowed: False` and `submission_performed: False` are hard invariant guarantees across all endpoints. Final application submission is ALWAYS manual.

### 6. Automated Job Discovery & Opportunity Pipeline (`app/job_discovery/`)
- **Provider Architecture**: `GreenhouseDiscoveryProvider`, `LeverDiscoveryProvider`, `ManualUrlProvider`.
- **Deterministic Deduplication**: 4-Tier deduplication (`JobDeduplicator`).
- **Candidate Matching & Ranking**: Evaluates match fit scores, match categories, matched/missing skills, and key concerns.
- **Lifecycle Management**: `DISCOVERED` $\to$ `SAVED` $\to$ `ANALYZED` $\to$ `ASSETS_GENERATED` $\to$ `READY_TO_APPLY` $\to$ `APPLIED` $\to$ `REJECTED` / `ARCHIVED`.

### 7. Application Pipeline & Job Tracking (`app/application_pipeline/`)
- **Core Entities & ORM Models**:
  - `TrackedApplication`: Central application tracking record holding status, priority, match scores, dates, referral, and follow-up states.
  - `ApplicationTimelineEvent`: Chronological audit log for all mutations (`APPLICATION_CREATED`, `STATUS_CHANGED`, `APPLICATION_MARKED_APPLIED`, `REFERRAL_ADDED`, `REFERRAL_STATUS_UPDATED`, `FOLLOW_UP_SCHEDULED`, `FOLLOW_UP_COMPLETED`, `INTERVIEW_SCHEDULED`, `INTERVIEW_UPDATED`, `OFFER_RECORDED`, `APPLICATION_REJECTED`, `APPLICATION_WITHDRAWN`, `NOTE_ADDED`).
  - `ApplicationInterview`: Multi-round interview tracking (`stage`, `scheduled_at`, `duration_minutes`, `mode`, `meeting_url`, `status`, `notes`).
  - `ApplicationStatusHistory`: Audit log for lifecycle status transitions (`from_status`, `to_status`, `timestamp`, `note`).
- **Validated Lifecycle State Machine (`app/application_pipeline/transitions.py`)**:
  - States: `DISCOVERED`, `SAVED`, `ASSETS_READY`, `READY_TO_APPLY`, `APPLIED`, `INTERVIEWING`, `OFFER`, `REJECTED`, `WITHDRAWN`, `CLOSED` (terminal).
  - Enforces valid transition paths and automatically records timestamps (`date_saved`, `date_assets_generated`, `date_applied`, `offer_date`, `rejection_date`, `withdrawal_date`, `last_status_update`).
- **Multi-Tier Duplicate Prevention (`app/application_pipeline/repository.py`)**:
  - Priority 1: `profile_id + company + job_id`
  - Priority 2 (job_id absent): `profile_id + normalized company + normalized role + normalized source_url` (case-insensitive, whitespace-normalized).
- **Timezone-Aware Follow-Up Engine (`app/application_pipeline/reminders.py`)**:
  - Calculates dynamic states: `NONE`, `SCHEDULED`, `DUE` (today), `OVERDUE` (past), `COMPLETED`.
- **Referral Tracking**:
  - Manages status (`NOT_REQUESTED`, `REQUESTED`, `REFERRAL_PENDING`, `REFERRED`, `DECLINED`, `NOT_AVAILABLE`), contact metadata, and request/referred dates.
- **Phase 5 Opportunity Conversion**:
  - Endpoint `POST /applications/from-opportunity/{opportunity_id}` converts discovered opportunities into tracked applications.
