# FRIDAY Development Roadmap

## Completed Milestones

### Phase 1: AI Provider Foundation & Core Job Intelligence (Complete)
- [x] Multi-provider AI abstraction (`BaseAIProvider`, `OllamaProvider`, `GeminiProvider`, `OpenRouterProvider`).
- [x] Automatic fallback chains in `app/core/brain/manager.py`.
- [x] Tool registry stabilization (`find_symbol`, `find_text`).
- [x] Pinned `requirements.txt` runtime dependencies.
- [x] Master Candidate Profile (`/profile`).
- [x] Deterministic Job Analysis & Scoring (`/jobs/analyze`, `/job-applications/analyze-and-save`).
- [x] Application tracking dashboard (`/applications`).

### Phase 2: Automated Job Scraping & Ingestion (Complete)
- [x] Hardened SSRF protection with DNS pre-resolution and redirect re-validation.
- [x] Source platform detection (Greenhouse, Lever, Workday, LinkedIn, Indeed, Generic).
- [x] High-precision platform extractors (Greenhouse API, Lever API, Schema.org JSON-LD).
- [x] Normalized schema (`NormalizedJobPosting`).
- [x] Ingestion endpoint `POST /jobs/ingest`.

### Phase 3: Tailored Application Asset Generation (Complete)
- [x] Grounded Application Asset Generation subsystem (`app/application_assets/`).
- [x] Tailored Resume, Cover Letter, Recruiter Message, Skill Gap, Application Summary models.
- [x] Multi-modal inputs: Raw text, `NormalizedJobPosting`, or saved `application_id`.
- [x] Strict candidate fact grounding & anti-hallucination validation.
- [x] Prompt injection isolation (`<UNTRUSTED_JOB_DATA>`).
- [x] FastAPI endpoint `POST /application-assets/generate`.
- [x] 100% offline deterministic test suite (`tests/test_phase3_assets.py`).

### Phase 4: Browser-Assisted Application Form Automation (Complete)
- [x] Dedicated application automation subsystem (`app/application_automation/`).
- [x] Two-stage human-in-the-loop workflow:
  - Stage A: `POST /application-automation/inspect` (parse form controls, classify into `AUTO_FILL_READY`, `APPROVAL_REQUIRED`, `MANUAL_REQUIRED`, `UNSUPPORTED`).
  - Stage B: `POST /application-automation/fill` (fill ONLY approved fields; leave browser open on completed form).
- [x] Platform adapters (`GreenhouseFormAdapter`, `LeverFormAdapter`, `GenericFormAdapter`, Oracle CX detection).
- [x] Multi-signal Page State Classifier (`PREVIEW_READY`, `JOB_DETAILS_PAGE`, `ACCOUNT_CREATION_REQUIRED`, `AUTH_REQUIRED`, `EMAIL_VERIFICATION_REQUIRED`, `CAPTCHA_DETECTED`, `ACCESS_RESTRICTED`, `FORM_NOT_READY`).
- [x] Fixed Texas Instruments `/apply/email` and 0-field false `PREVIEW_READY` bug.
- [x] Session refresh endpoint `POST /application-automation/inspect/{session_id}/refresh`.
- [x] Deterministic field mapping engine (`FieldMapper`) with strict password & OTP protection.
- [x] Absolute submission safety invariant: `submission_allowed=False`, `submission_performed=False`, `SUBMISSION_BLOCKED` guard.
- [x] 100% offline deterministic unit & integration tests (`tests/test_phase4_automation.py`).

### Phase 5: Automated Job Discovery & Opportunity Pipeline (Complete)
- [x] Provider-based discovery architecture (`BaseJobProvider`, `GreenhouseDiscoveryProvider`, `LeverDiscoveryProvider`, `ManualUrlProvider`).
- [x] Batch search query with role, keyword, company, location, and remote filtering (`POST /job-discovery/search`).
- [x] Manual URL batch discovery delegating to Phase 2 ingestion (`POST /job-discovery/manual`).
- [x] Deterministic 4-tier deduplication (`JobDeduplicator`).
- [x] Candidate profile matching and ranking engine (`JobRanker`).
- [x] Opportunity lifecycle state machine and repository (`DiscoveredOpportunity`, `OpportunityRepository`).
- [x] Opportunity management endpoints (`GET /opportunities`, `GET /opportunities/{id}`, `PATCH /opportunities/{id}/status`).
- [x] Seamless pipeline integration with Phase 1 (`/analyze`), Phase 3 (`/generate-assets`), and Phase 4 (`/prepare-application`).
- [x] 100% offline deterministic unit & integration tests (`tests/test_phase5_discovery.py`).

### Phase 6: Application Pipeline & Job Tracking (Complete)
- [x] Dedicated application pipeline subsystem (`app/application_pipeline/`).
- [x] SQLAlchemy models: `TrackedApplication`, `ApplicationTimelineEvent`, `ApplicationInterview`, `ApplicationStatusHistory`.
- [x] Validated lifecycle state machine (`StatusTransitionEngine`) with terminal `CLOSED` state protection.
- [x] Multi-tier duplicate detection: `profile_id + company + job_id` and normalized `profile_id + company + role + source_url`.
- [x] Chronological timeline event logger (`TimelineService`) tracking all mutations and status transitions.
- [x] Timezone-aware follow-up engine (`FollowUpManager`) calculating `SCHEDULED`, `DUE`, and `OVERDUE` states.
- [x] Referral tracking system (`NOT_REQUESTED`, `REQUESTED`, `REFERRAL_PENDING`, `REFERRED`, `DECLINED`, `NOT_AVAILABLE`).
- [x] Multiple interview rounds manager (`SCREENING`, `ONLINE_ASSESSMENT`, `TECHNICAL_ROUND`, `SYSTEM_DESIGN`, `HR_ROUND`, `HIRING_MANAGER`, `FINAL_ROUND`, `OTHER`).
- [x] REST API endpoints (`/applications`, `/applications/from-opportunity/{id}`, `/applications/summary`, `/applications/follow-ups`, `/applications/dashboard`, `/applications/{id}/timeline`, `/applications/{id}/status`, `/applications/{id}/mark-applied`, `/applications/{id}/notes`, `/applications/{id}/referral`, `/applications/{id}/follow-up`, `/applications/{id}/interviews`).
- [x] Seamless integration converting Phase 5 opportunities to tracked applications.
- [x] Complete backward compatibility with existing Phase 1–5 endpoints and models.
- [x] 100% offline deterministic test suite (`tests/test_phase6_application_pipeline.py`).

### Phase 7: Proactive Career Intelligence & Next-Action System (Complete)
- [x] Dedicated career intelligence subsystem (`app/career_intelligence/`).
- [x] SQLAlchemy models: `CareerRecommendation` (`career_recommendations` table).
- [x] Explainable priority scoring engine (`ApplicationPriorityEngine`) computing 0–100 score across 7 multi-factor weights.
- [x] Diagnostic application health engine (`ApplicationHealthEngine`) evaluating `EXCELLENT`, `HEALTHY`, `ATTENTION_NEEDED`, `STALE`, and `CRITICAL` states.
- [x] Proactive recommendation engine (`RecommendationEngine`) generating deduplicated, actionable recommendations.
- [x] Daily & weekly briefing synthesis (`CareerBriefingEngine`).
- [x] Recommendation lifecycle state management (`ACTIVE`, `DISMISSED`, `COMPLETED`, `EXPIRED`) with 7-day cooldown.
- [x] REST API endpoints (`/career-intelligence/today`, `/career-intelligence/next-actions`, `/career-intelligence/dashboard`, `/career-intelligence/application-health`, `/career-intelligence/application-health/{id}`, `/career-intelligence/daily-briefing`, `/career-intelligence/weekly-briefing`, `/career-intelligence/recommendations/{id}/dismiss`, `/career-intelligence/recommendations/{id}/complete`, `/career-intelligence/recommendations/refresh`).
- [x] Strict safety invariants: No automated submissions, no external messages/emails dispatched.
- [x] 100% offline deterministic test suite (`tests/test_phase7_career_intelligence.py`).

---

## Upcoming Milestones

### Phase 8: Multi-Channel Alerts & AI Mock Interview Simulation
- [ ] Scheduled recurring discovery cron jobs with configurable match score thresholds.
- [ ] Multi-channel notifications (Email digest, Telegram/Discord webhooks) for urgent action items.
- [ ] AI-assisted Mock Interview simulator with custom technical and behavioral question generation based on target job requirements and candidate profile gaps.
- [ ] Unified frontend UI integration connecting the complete discovery-to-submission pipeline.
