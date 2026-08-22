# FRIDAY System Architecture

## Overview

FRIDAY is a modular personal AI assistant and Job Application Automation System built with FastAPI, SQLite/SQLAlchemy, and a resilient multi-provider AI gateway.

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
  - **Stage A (Inspect & Preview)**: Detects ATS platform (Greenhouse, Lever, Generic), parses DOM controls, maps candidate profile facts deterministically, and classifies fields into `AUTO_FILL_READY`, `APPROVAL_REQUIRED`, `MANUAL_REQUIRED`, and `UNSUPPORTED`.
  - **Stage B (Fill Approved Fields)**: Revalidates session and fills ONLY the explicitly approved fields, leaving the browser open on the completed page.
- **Obstacle Detection**: Automatically halts on CAPTCHA (`CAPTCHA_DETECTED`) or login walls (`AUTHENTICATION_REQUIRED`) without attempting bypasses.
- **Sensitive Question Policy**: Demographic, salary, veteran, disability, and criminal history questions are strictly marked `MANUAL_REQUIRED`.
- **Absolute Submission Safety Guarantee**:
  - `submission_allowed: False` and `submission_performed: False` are hard invariant guarantees.
  - No automated final submission button clicks or form submit triggers are permitted. Final application submission is ALWAYS manual.
