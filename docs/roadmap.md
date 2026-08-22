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

---

## Upcoming Milestones

### Phase 6: Automated Career Alerts & Multi-Channel Interview Intelligence
- [ ] Scheduled recurring discovery cron jobs with configurable match score thresholds ($\ge 80\%$).
- [ ] Multi-channel notifications (Email digest, Telegram/Discord webhooks) for top opportunities.
- [ ] AI-assisted Mock Interview simulator with custom technical and behavioral question generation based on target job requirements and candidate profile gaps.
- [ ] Unified frontend UI integration connecting the complete discovery-to-submission pipeline.
