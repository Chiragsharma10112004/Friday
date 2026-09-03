# FRIDAY — Autonomous AI Personal Operating System & Career Intelligence Platform

[![FRIDAY CI Test Suite](https://github.com/Chiragsharma10112004/Friday/actions/workflows/ci.yml/badge.svg)](https://github.com/Chiragsharma10112004/Friday/actions/workflows/ci.yml)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Next.js](https://img.shields.io/badge/Next.js-14.2+-black.svg?logo=next.js&logoColor=white)](https://nextjs.org/)
[![TypeScript](https://img.shields.io/badge/TypeScript-5.4+-3178C6.svg?logo=typescript&logoColor=white)](https://www.typescriptlang.org/)
[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Tests Passing](https://img.shields.io/badge/Tests-115%20Passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

> **FRIDAY** is a general-purpose **Autonomous AI Personal Operating System** engineered for developer intelligence, code self-healing, multi-model AI reasoning, job discovery, application workflow automation, and career trajectory optimization.

---

## 🌟 Architecture & Core Capabilities

```
                           ┌──────────────────────────────────────────────┐
                           │            FRIDAY AI COMMAND CENTER          │
                           │       (Next.js + TypeScript + Tailwind)      │
                           └──────────────────────┬───────────────────────┘
                                                  │
                                                  ▼
                           ┌──────────────────────────────────────────────┐
                           │               FRIDAY AI OS CORE              │
                           │           (FastAPI + Python Backend)         │
                           └──────────────────────┬───────────────────────┘
                                                  │
         ┌────────────────────────────────────────┼────────────────────────────────────────┐
         │                                        │                                        │
┌────────▼────────┐                     ┌─────────▼─────────┐                    ┌─────────▼────────┐
│  AI REASONING   │                     │  SELF-HEALING &   │                    │     AUTONOMOUS   │
│   & INTELLIGENCE│                     │ CODE INTELLIGENCE │                    │  CAREER PIPELINE │
└────────┬────────┘                     └─────────┬─────────┘                    └─────────┬────────┘
         │                                        │                                        │
  • Multi-Model Brain                     • Failure Classification                 • Job Discovery (ATS)
  • Contextual Memory                     • AST Code Analyzer                      • Asset Tailoring
  • Task Planning                         • Unified Diff Proposals                 • Pipeline Tracking
  • Tool Orchestration                    • Bounded Auto-Rollback                  • Outcome Analytics
```

---

## 🖥️ Phase 10: Modern AI Operating System UI

FRIDAY features a **dark, futuristic command center web application** built with **Next.js 14 App Router**, **TypeScript**, **Tailwind CSS**, and **Lucide Icons**:

| Screen | Route | Description | Backend Integrations |
| :--- | :--- | :--- | :--- |
| **1. Command Center** | `/` | AI greeting, command bar, live system telemetry, today's priorities | `GET /status`, `GET /health/readiness`, `GET /career-intelligence/today`, `GET /workflow/queue` |
| **2. AI Chat & Reasoning** | `/chat` | Multi-turn reasoning, tool execution, model provider badge | `POST /chat/`, `GET /memory/history` |
| **3. Tasks & Planning** | `/tasks` | Autonomous workflow queue, approval gates, pause/resume | `GET /workflow/queue`, `GET /workflow`, `POST /workflow/{id}/start`, `POST /workflow/{id}/approve` |
| **4. Developer Mode** | `/developer` | Repository AST tree, symbol catalog, safe test runner, AST patcher | `GET /developer/workspace`, `GET /developer/symbols`, `POST /developer/run-tests`, `POST /developer/edit` |
| **5. Self-Healing & Health** | `/health` | Diagnostic telemetry, AST failure classification, auto-heal simulator | `GET /health/readiness`, `GET /health/diagnostics`, `POST /self-healing/auto-heal`, `GET /self-healing/history` |
| **6. Projects** | `/projects` | Monitored repository workspace, lines of code, test coverage | `GET /developer/workspace`, `GET /health/detailed` |
| **7. Memory & Context** | `/memory` | Stored permanent user facts and conversational history | `GET /memory`, `POST /memory`, `DELETE /memory/{key}`, `GET /memory/history` |
| **8. Job Discovery** | `/jobs` | Greenhouse/Lever job search, match scoring, workflow launcher | `POST /job-discovery/search`, `GET /opportunities` |
| **9. Application Pipeline** | `/applications` | Kanban lifecycle board (`SAVED` &rarr; `APPLIED` &rarr; `OFFER`), notes, timeline | `GET /applications`, `POST /applications`, `POST /applications/{id}/status`, `GET /applications/{id}/timeline` |
| **10. Career Intelligence** | `/intelligence` | Application health audits, staleness detection, daily executive briefing | `GET /career-intelligence/dashboard`, `GET /career-intelligence/application-health`, `GET /career-intelligence/daily-briefing` |
| **11. Analytics & Feedback** | `/analytics` | Conversion funnel, ATS platform metrics, field issue resolution | `GET /feedback/analytics/summary`, `GET /feedback/analytics/funnel`, `GET /feedback/analytics/platforms` |
| **12. Activity Timeline** | `/activity` | Chronological audit log of operations, workflows, and self-healing | `GET /self-healing/history`, `GET /career-intelligence/next-actions` |
| **13. System Settings** | `/settings` | Candidate profile editor, runtime parameters, safety invariants | `GET /status`, `GET /profile`, `PATCH /profile` |
| **Global Command Palette** | `Ctrl/Cmd + K` | Universal keyboard shortcut for instant screen navigation & actions | Full Client Routing |

---

## 🔒 Security Invariants & Human-in-the-Loop Safeguards

1. **Zero Credential Storage**: FRIDAY never stores, logs, or transmits passwords, OTPs, auth tokens, or private secrets.
2. **Mandatory Human Submission Checkpoint**: Final job submission is strictly manual. FRIDAY prepares the application and pauses for explicit human review.
3. **Sandbox Confinement**: All code modifications and shell commands are checked against path traversal filters and dangerous command blockers.
4. **Automated Rollback Safety**: Any automated remediation that fails test suite validation is reverted to its original snapshot.

---

## 🧪 Comprehensive Test Suite

FRIDAY maintains 100% deterministic offline unit and integration test coverage across all subsystems:

### Backend Test Suite (115 Tests Passing)
```bash
cd backend
python -m tests.run_all_phase_tests
```

```
==========================================
TOTAL TESTS RUN: 115
FAILURES: 0
ERRORS: 0
==========================================
```

### Frontend Test Suite
```bash
cd web
npm test
```

---

## 🚀 Quickstart & Deployment

### Option A: Local Development

```bash
# 1. Start the FastAPI Backend
cd backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# 2. In a separate terminal, start the Next.js Frontend
cd web
npm install
npm run dev -- -p 3000
```

Open `http://localhost:3000` to access the FRIDAY Command Center.

### Option B: Docker Compose (Full Stack)

```bash
# Build and start both Backend (:8000) and Web Frontend (:3000)
docker compose up --build
```

---

## 📄 License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.
