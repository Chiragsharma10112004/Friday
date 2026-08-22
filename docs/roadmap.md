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
- [x] Platform adapters (`GreenhouseFormAdapter`, `LeverFormAdapter`, `GenericFormAdapter`).
- [x] Obstacle handling (`CAPTCHA_DETECTED`, `AUTHENTICATION_REQUIRED`, `SOURCE_ACCESS_RESTRICTED`).
- [x] Deterministic field mapping engine (`FieldMapper`).
- [x] Absolute submission safety invariant: `submission_allowed=False`, `submission_performed=False`, `SUBMISSION_BLOCKED` guard.
- [x] 100% offline deterministic unit & integration tests (`tests/test_phase4_automation.py`).

---

## Upcoming Milestones

### Phase 5: Automated Job Discovery Feeds & Application Pipeline Dashboard
- [ ] Automated discovery feed aggregation based on profile target roles and locations.
- [ ] Batch job scoring and ranked opportunity queues.
- [ ] Email/Notification alerts for high-match opportunities (Match Score $\ge 85\%$).
- [ ] Real-time application lifecycle sync and analytics dashboard.
