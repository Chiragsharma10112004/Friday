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

### `GET /applications`
- **Description**: List tracked job applications with filtering by status and metrics summary.

### `GET /applications/{app_id}`
- **Description**: Get single application details.

### `PATCH /applications/{app_id}`
- **Description**: Update application status (e.g. `APPLIED`, `INTERVIEWING`, `OFFER`, `REJECTED`).

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
- **Response** (`ApplicationAssetResponse`):
```json
{
  "success": true,
  "company": "Anthropic",
  "role": "Senior AI Backend Engineer",
  "match_score": 88,
  "recommendation": "APPLY",
  "assets": {
    "resume": {
      "professional_summary": "...",
      "relevant_skills": ["Python", "FastAPI", "SQLAlchemy", "PostgreSQL"],
      "relevant_projects": [
        {
          "name": "FRIDAY AI Assistant",
          "description": "...",
          "bullet_points": ["..."],
          "matched_skills": ["Python", "FastAPI"]
        }
      ],
      "experience_bullets": ["..."],
      "achievement_bullets": ["..."],
      "keywords_matched": ["Python", "FastAPI"],
      "keywords_missing": ["Kubernetes"],
      "sections_to_prioritize": ["Backend Skills", "AI Projects"]
    },
    "cover_letter": {
      "letter_text": "...",
      "style": "standard",
      "key_highlights": ["..."],
      "evidence_used": ["..."]
    },
    "recruiter_message": {
      "message_text": "...",
      "channel": "linkedin",
      "tone": "professional",
      "character_count": 184
    },
    "skill_gap": {
      "matched_skills": ["Python", "FastAPI"],
      "partially_matched_skills": ["Docker"],
      "missing_skills": ["Kubernetes"],
      "transferable_skills": ["Container orchestration concepts"],
      "priority_gaps": [
        {
          "skill": "Kubernetes",
          "priority": "HIGH",
          "reason": "Core infrastructure requirement in job description.",
          "evidence_from_jd": "...",
          "suggested_action": "Complete hands-on deployment tutorial."
        }
      ],
      "recommended_learning_actions": ["..."]
    },
    "application_summary": {
      "overall_fit": "STRONG_MATCH",
      "strongest_selling_points": ["..."],
      "biggest_concerns": ["..."],
      "missing_requirements": ["Kubernetes"],
      "recommended_assets": ["Tailored Resume", "Cover Letter"],
      "apply_recommendation": "APPLY"
    }
  },
  "evidence_metadata": [
    {
      "claim": "FastAPI microservices and LLM gateway development",
      "claim_type": "VERIFIED_CANDIDATE_FACT",
      "source_field": "projects",
      "confidence": "high"
    }
  ],
  "warnings": [],
  "errors": []
}
```

---

## 6. Browser-Assisted Application Form Automation (Phase 4)

### `POST /application-automation/inspect`
- **Description**: Stage A: Inspect target job application form, detect ATS platform, parse visible controls, map verified candidate profile facts, and produce a human-in-the-loop preview.
- **Safety Invariant**: Does NOT modify the form and NEVER submits the application (`submission_allowed: false`).
- **Request Body** (`InspectApplicationRequest`):
```json
{
  "application_url": "https://boards.greenhouse.io/anthropic/jobs/12345",
  "application_id": null,
  "normalized_job": null
}
```
- **Response** (`InspectApplicationResponse`):
```json
{
  "success": true,
  "session_id": "3f82a17b-4029-4d64-a63e-bb36a87ce71b",
  "platform": "greenhouse",
  "status": "PREVIEW_READY",
  "page_url": "https://boards.greenhouse.io/anthropic/jobs/12345",
  "page_title": "Senior AI Backend Engineer at Anthropic",
  "fields": [
    {
      "field_id": "#first_name",
      "label": "First Name",
      "html_name": "first_name",
      "control_type": "text",
      "normalized_field": "first_name",
      "suggested_value": "Chirag",
      "source": "profile.first_name",
      "confidence": "HIGH",
      "status": "AUTO_FILL_READY",
      "requires_approval": false,
      "options": [],
      "is_sensitive": false,
      "validation_notice": null
    },
    {
      "field_id": "#gender",
      "label": "Gender (Voluntary EEO)",
      "html_name": "job_application[gender]",
      "control_type": "select",
      "normalized_field": null,
      "suggested_value": null,
      "source": null,
      "confidence": "UNSUPPORTED",
      "status": "MANUAL_REQUIRED",
      "requires_approval": true,
      "options": ["Decline to self-identify", "Female", "Male", "Non-binary"],
      "is_sensitive": true,
      "validation_notice": "Demographic, compensation, and compliance questions require manual review."
    }
  ],
  "auto_fill_ready_count": 5,
  "approval_required_count": 2,
  "manual_required_count": 3,
  "unsupported_count": 0,
  "warnings": [
    "3 field(s) require manual review (e.g. demographic, compensation, or unmapped questions)."
  ],
  "errors": [],
  "submission_allowed": false
}
```

### `POST /application-automation/fill`
- **Description**: Stage B: Fill ONLY user-approved fields into the active browser session. Leaves the browser on the completed form for final human inspection.
- **Safety Invariant**: NEVER submits the application (`submission_performed: false`, `manual_submission_required: true`).
- **Request Body** (`FillApprovedFieldsRequest`):
```json
{
  "session_id": "3f82a17b-4029-4d64-a63e-bb36a87ce71b",
  "approved_field_ids": [
    "#first_name",
    "#last_name",
    "#email",
    "#phone",
    "#urls_linkedin"
  ],
  "custom_answers": {
    "#expected_salary": "$160,000"
  }
}
```
- **Response** (`FillApprovedFieldsResponse`):
```json
{
  "success": true,
  "session_id": "3f82a17b-4029-4d64-a63e-bb36a87ce71b",
  "platform": "greenhouse",
  "fields_filled": [
    {
      "field_id": "#first_name",
      "label": "First Name",
      "normalized_field": "first_name",
      "value_filled": "Chirag",
      "success": true,
      "notice": "Populated from profile.first_name"
    }
  ],
  "fields_skipped": ["#gender"],
  "manual_fields_remaining": ["Gender (Voluntary EEO)"],
  "submission_performed": false,
  "manual_submission_required": true,
  "warnings": [
    "Form fields have been filled in the browser session. Please review all fields thoroughly and submit the application manually."
  ],
  "errors": []
}
```
