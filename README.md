# FRIDAY – AI-Powered Autonomous Career Platform

FRIDAY is an AI-powered career intelligence platform designed to help users discover relevant job opportunities, analyze job descriptions, evaluate candidate-job alignment, tailor application assets, track applications, and manage the complete job-search workflow.

The platform combines AI-driven job analysis with structured automation while maintaining strict human control over sensitive actions and final application submission.

---

## 🚀 Project Overview

FRIDAY brings multiple career workflows into a unified pipeline:

```text
Phase 5: Discovery
        ↓
Phase 1: AI Matching
        ↓
Phase 6: Application Tracking
        ↓
Phase 3: Tailored Assets
        ↓
Phase 4: Application Inspection & Autofill
        ↓
Human Checkpoint
        ↓
Manual Submission
        ↓
Phase 6: Referrals & Interviews
```

The platform also includes a proactive Career Intelligence Engine that continuously analyzes application pipeline health, prioritizes important actions, and generates career briefings.

---

# 🧠 Core Capabilities

## 1. AI Job Analysis & Matching

- Analyze job descriptions
- Extract technical and professional skills
- Identify job requirements
- Calculate candidate-job match scores
- Identify missing skills
- Generate structured job insights

---

## 2. Application Asset Generation

Generate and manage application assets including:

- Tailored resumes
- Cover letters
- Structured candidate information
- Job-specific application content

---

## 3. Application Inspection & Safe Autofill

FRIDAY can inspect application workflows and assist with approved fields.

Supported safety controls include:

- Safe non-sensitive profile field autofill
- Explicit user approval
- Authentication detection
- CAPTCHA detection
- Account creation detection
- Email verification checkpoints

Sensitive credentials are never stored or processed.

---

## 4. Intelligent Job Discovery

The discovery system:

- Scans job opportunities
- Filters opportunities based on match thresholds
- Prioritizes relevant jobs
- Queues actionable opportunities
- Connects discovery with the autonomous workflow system

---

## 5. Application Tracking

Track the complete application lifecycle, including:

- Applications created
- Applications submitted
- Application status
- Follow-ups
- Referrals
- Interviews
- Workflow state
- Next actions

---

# ⚙️ Phase 7: Autonomous Workflow & Career Intelligence

Phase 7 transforms FRIDAY into a proactive autonomous career platform by connecting the previous phases into a unified workflow.

## Autonomous Workflow Pipeline

```text
Discovery
    ↓
Job Matching
    ↓
Application Planning
    ↓
Resume / Asset Generation
    ↓
Application Inspection
    ↓
Safe Autofill
    ↓
Human Checkpoint
    ↓
Manual Submission
    ↓
Application Tracking
    ↓
Referral & Interview Management
```

---

# 🔄 Autonomous Workflow Subsystem

Location:

```text
app/autonomous_workflow/
```

## Core Components

### `models.py`

Defines the core workflow entities:

- `AutonomousWorkflow`
- `WorkflowStep`
- `WorkflowApproval`
- `WorkflowActionLog`
- `WorkflowRetry`

The workflow tracks:

- Priority
- Match score
- Checkpoints
- Pause state
- Retry attempts
- Metadata
- Lifecycle state

---

### `workflow_state.py`

Provides the `WorkflowStateMachine`.

Features:

- Controlled workflow transitions
- Protection against invalid state jumps
- Terminal state rules
- Support for `CANCELLED` and `CLOSED` states

---

### `job_ranker.py`

Provides `JobRankerEngine`.

Evaluates:

- Match score
- Missing skills
- Referral advantage
- Remote flexibility

Assigns deterministic priorities:

```text
URGENT
HIGH
MEDIUM
LOW
```

Also generates:

- Recommendations
- Risk flags
- Priority reasoning

---

### `application_planner.py`

Provides `ApplicationPlanner`.

Creates role-specific execution plans containing:

- Workflow steps
- Dependencies
- Required approvals
- Application preparation actions

---

### `referral_manager.py`

Provides `WorkflowReferralManager`.

Synchronizes referral tracking with application tracking while enforcing:

```text
No automated outreach
```

---

### `discovery_scheduler.py`

Provides `DiscoveryScheduler`.

Responsible for:

- Running discovery cycles
- Scanning opportunities
- Applying match thresholds
- Queueing high-priority job opportunities

---

### `orchestrator.py`

Provides:

```text
AutonomousWorkflowOrchestrator
```

Coordinates cross-phase operations and handles checkpoints such as:

- `AUTH_REQUIRED`
- `ACCOUNT_CREATION_REQUIRED`
- `CAPTCHA_DETECTED`
- `EMAIL_VERIFICATION_REQUIRED`
- `JOB_DETAILS_PAGE`

The orchestrator also:

- Manages workflow lifecycle
- Performs safe approved autofill
- Coordinates asset generation
- Coordinates application inspection
- Pauses before final submission

---

### `service.py`

Provides `WorkflowService`.

Acts as a unified service facade for:

- Workflow creation
- Workflow lifecycle management
- Approvals
- Application inspection
- Safe autofill
- Dashboard aggregation

---

# 📊 Career Intelligence Engine

Location:

```text
app/career_intelligence/
```

The Career Intelligence Engine continuously analyzes the application pipeline and generates actionable insights.

---

## `priority_engine.py`

Computes a 0–100 priority score using multiple factors:

- Match score
- User priority
- Referral advantage
- Application lifecycle state
- Follow-up urgency
- Interview urgency
- Application staleness

---

## `health_engine.py`

Diagnoses application health using categories:

```text
EXCELLENT
HEALTHY
ATTENTION_NEEDED
STALE
CRITICAL
```

---

## `recommendation_engine.py`

Generates actionable recommendations with:

- Deduplication
- Automatic expiration
- Dismissal tracking
- 7-day cooldown for dismissed recommendations

---

## `briefing_engine.py`

Generates:

- Daily executive action queues
- Daily career briefings
- Weekly pipeline performance digests

---

# 🌐 REST API

## Autonomous Workflow API

Mounted at:

```text
/workflow
```

### Workflow Management

```text
POST /workflow
POST /workflow/from-opportunity/{opportunity_id}

GET /workflow
GET /workflow/{workflow_id}
GET /workflow/queue
GET /workflow/dashboard
```

### Lifecycle Actions

```text
POST /workflow/{workflow_id}/start
POST /workflow/{workflow_id}/pause
POST /workflow/{workflow_id}/resume
POST /workflow/{workflow_id}/retry
POST /workflow/{workflow_id}/cancel
```

### Approvals

```text
POST /workflow/{workflow_id}/approve
POST /workflow/{workflow_id}/reject
```

### Workflow Inspection

```text
GET /workflow/{workflow_id}/plan
GET /workflow/{workflow_id}/steps
GET /workflow/{workflow_id}/actions
GET /workflow/{workflow_id}/approvals
GET /workflow/{workflow_id}/next-action
```

### Application Operations

```text
POST /workflow/{workflow_id}/assets/generate
POST /workflow/{workflow_id}/application/inspect
POST /workflow/{workflow_id}/application/autofill
POST /workflow/{workflow_id}/confirm-manual-submission
```

### Referrals & Discovery

```text
POST /workflow/{workflow_id}/referral
POST /workflow/discovery/run
```

---

## Career Intelligence API

Mounted at:

```text
/career-intelligence
```

### Daily Intelligence

```text
GET /career-intelligence/today
GET /career-intelligence/next-actions
GET /career-intelligence/dashboard
```

### Application Health

```text
GET /career-intelligence/application-health
GET /career-intelligence/application-health/{id}
```

### Career Briefings

```text
GET /career-intelligence/daily-briefing
GET /career-intelligence/weekly-briefing
```

### Recommendation Management

```text
POST /career-intelligence/recommendations/{id}/dismiss
POST /career-intelligence/recommendations/{id}/complete
POST /career-intelligence/recommendations/refresh
```

---

# 🔐 Safety Principles

FRIDAY follows strict safety boundaries.

## 1. No Automated Application Submission

Final application submission is never automated.

```text
submission_allowed = False
submission_performed = False
```

The user must manually complete the final submission.

---

## 2. No Password or OTP Storage

FRIDAY never:

- Stores passwords
- Stores OTP codes
- Logs credentials
- Automates sensitive authentication

---

## 3. No Automated CAPTCHA Solving

CAPTCHAs immediately trigger a human checkpoint:

```text
CAPTCHA_DETECTED
```

---

## 4. Safe Autofill Only

Autofill is limited to approved non-sensitive fields such as:

```text
first_name
last_name
email
phone
linkedin_url
```

Explicit approval is required.

---

## 5. Human Authentication Checkpoints

The workflow pauses for:

```text
AUTH_REQUIRED
ACCOUNT_CREATION_REQUIRED
EMAIL_VERIFICATION_REQUIRED
```

Authentication must be completed manually by the user.

---

# 🧪 Testing

FRIDAY includes a comprehensive offline regression suite covering all major phases.

```text
tests/test_phase1_validation.py
tests/test_phase2_ingestion.py
tests/test_phase3_assets.py
tests/test_phase4_automation.py
tests/test_phase5_discovery.py
tests/test_phase6_application_pipeline.py
tests/test_phase7_career_intelligence.py
tests/test_phase7_autonomous_workflow.py
```

### Test Coverage

```text
Phase 1 Validation              13 tests
Phase 2 Ingestion               10 tests
Phase 3 Assets                   9 tests
Phase 4 Automation              14 tests
Phase 5 Discovery                6 tests
Phase 6 Application Pipeline    14 tests
Phase 7 Career Intelligence     13 tests
Phase 7 Autonomous Workflow     18 tests
-----------------------------------------
TOTAL                            97 tests
```

The test suite is designed to run:

```text
100% offline
No external network dependencies
```

---

# 🛠️ Technology Stack

## Backend

- Python
- FastAPI
- Pydantic
- SQLAlchemy

## Data

- PostgreSQL
- MongoDB
- Vector databases

## AI & Machine Learning

- Generative AI
- LLM workflows
- Prompt engineering
- Agentic workflows
- Semantic processing

## Engineering

- REST APIs
- WebSockets
- Object-Oriented Programming
- Workflow orchestration
- Automated testing
- Async processing

## DevOps

- Git
- GitHub
- Docker
- CI/CD
- AWS

---

# 🎯 Project Vision

FRIDAY aims to evolve from a traditional job tracker into an intelligent career operating system.

The long-term goal is to help users:

```text
Discover
      ↓
Understand
      ↓
Match
      ↓
Prioritize
      ↓
Prepare
      ↓
Track
      ↓
Improve
```

while keeping the user in control of all sensitive actions and final application decisions.

---

# 🚧 Current Status

```text
Phase 1  AI Job Matching                 Complete
Phase 2  Job Ingestion                   Complete
Phase 3  Application Asset Generation   Complete
Phase 4  Application Inspection          Complete
Phase 5  Intelligent Job Discovery       Complete
Phase 6  Application Pipeline            Complete
Phase 7  Autonomous Workflow             Complete
Phase 7  Career Intelligence             Complete
```

**FRIDAY is now a unified, intelligent career platform combining AI, job discovery, application workflows, career intelligence, and human-controlled automation.**

---

## 👨‍💻 Author

**Chirag Sharma**

- LinkedIn: https://www.linkedin.com/in/chiragatwork18/
- GitHub: https://github.com/Chiragsharma10112004

---

## ⚠️ Important Disclaimer

FRIDAY assists with career research, application preparation, workflow management, and safe automation.

It does not:

- Automatically submit job applications
- Store passwords or OTPs
- Solve CAPTCHAs
- Send automated referral outreach
- Bypass authentication or security mechanisms

Final application submission and sensitive actions always remain under human control.
## Verification Status
- Phase 7: Complete
- Automated regression tests: 99 passed
- Main application import: Verified
