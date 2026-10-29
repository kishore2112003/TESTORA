# Project Brief: Test Case Management System (TESTORA)

## Product Overview
A multi-page web application designed for a single QA engineer (multi-user ready) to create and execute test cases per ticket, view saved sessions, and export reports.
The application operates standalone without requiring integration with Jira or external ticket tracking systems. A "ticket" consists of a user-specified ticket number and title.

---

## Core Flows & Modules

The application follows the flow: **Login &rarr; Dashboard (Sidebar Layout) &rarr; Functional Modules**:

1. **New Ticket Session**:
   - Enter session header details (ticket number, title, environment, test date, testing types, status).
   - Create test cases and execute them within the same unified screen.
   - Autosave changes directly to the database.
2. **View Sessions**:
   - List all sessions with filtering and sorting.
   - Session actions: View (read-only), Edit, Duplicate, and Soft-delete.
3. **Export**:
   - Multi-session selection.
   - Export formats: Excel (`.xlsx`) or Word (`.docx` from template).
   - In-app preview before download.

---

## Tech Stack

### Frontend
- **Framework & Tooling**: React, Vite, TypeScript
- **Styling & UI**: Tailwind CSS, shadcn/ui
- **State & Data Fetching**: TanStack Query (React Query)
- **Routing**: React Router
- **Form Handling**: React Hook Form with Zod validation

### Backend
- **Framework**: Python FastAPI
- **ORM & Migrations**: SQLAlchemy 2.x, Alembic
- **Validation & Serialization**: Pydantic v2
- **Authentication**: JWT stored in `httpOnly` cookies, password hashing with Argon2
- **Document Exporting**: `openpyxl` (Excel), `docxtpl` (Word from `.docx` templates)
- **AI Integration (Later Phase)**: Anthropic API (API key loaded strictly from backend `.env`)

### Database & Deployment
- **Database**: PostgreSQL (SQLite supported for local development via `DATABASE_URL`)
- **Deployment**: Docker Compose

---

## Excel Export Specification

Columns must be exported in the exact following order:
1. `TCID`
2. `Scenario`
3. `Precondition`
4. `Test Data`
5. `Actual Result`
6. `Expected Result`
7. `Status`

---

## Data Model

```mermaid
erDiagram
    users ||--o{ sessions : "creates"
    users ||--o{ export_logs : "exports"
    users ||--o| user_settings : "configures"
    sessions ||--o{ test_cases : "contains"
    test_cases ||--o{ test_steps : "has"
    test_cases ||--o{ attachments : "includes"

    users {
        uuid id PK
        string name
        string email UK
        string password_hash
        string role
        timestamp created_at
    }

    sessions {
        uuid id PK
        uuid user_id FK
        string ticket_no
        string ticket_title
        string environment
        date test_date
        json testing_types
        string status "draft | in_progress | completed"
        timestamp deleted_at
        timestamp created_at
        timestamp updated_at
    }

    test_cases {
        uuid id PK
        uuid session_id FK
        string tc_id
        int position
        text scenario
        text precondition
        text test_data
        text expected_result
        text actual_result
        string status "not_run | pass | fail | blocked | skipped"
        timestamp executed_at
        timestamp created_at
        timestamp updated_at
    }

    test_steps {
        uuid id PK
        uuid test_case_id FK
        int step_no
        text description
    }

    attachments {
        uuid id PK
        uuid test_case_id FK
        string file_path
        string caption
        int figure_no
        timestamp created_at
    }

    export_logs {
        uuid id PK
        uuid user_id FK
        json session_ids
        string format
        timestamp created_at
    }

    user_settings {
        uuid user_id PK_FK
        text ai_style_prompt
        string default_environment
    }
```

### Table Definitions
- **`users`**: `id`, `name`, `email` (unique), `password_hash`, `role`, `created_at`
- **`sessions`**: `id`, `user_id`, `ticket_no`, `ticket_title`, `environment`, `test_date`, `testing_types` (json), `status` (`draft` | `in_progress` | `completed`), `deleted_at`, `created_at`, `updated_at`
- **`test_cases`**: `id`, `session_id`, `tc_id`, `position`, `scenario`, `precondition`, `test_data`, `expected_result`, `actual_result`, `status` (`not_run` | `pass` | `fail` | `blocked` | `skipped`), `executed_at`, `created_at`, `updated_at`
- **`test_steps`**: `id`, `test_case_id`, `step_no`, `description`
- **`attachments`**: `id`, `test_case_id`, `file_path`, `caption`, `figure_no`, `created_at`
- **`export_logs`**: `id`, `user_id`, `session_ids` (json), `format`, `created_at`
- **`user_settings`**: `user_id`, `ai_style_prompt`, `default_environment`

---

## Architectural Guidelines & Rules

1. **Directory Boundaries**:
   - Backend logic resides in `/backend`.
   - Frontend web application resides in `/frontend`.
   - Reference templates, documentation, and exports reside in `/reference`.
2. **Environment & Secrets**:
   - All configuration managed via `.env` files.
   - Maintain `.env.example` templates; never commit `.env` or sensitive secrets to version control.
3. **Code Quality & Testing**:
   - Strongly typed, clean, well-commented code across both stacks.
   - Automated tests for all backend routes and critical workflows.
4. **User Experience & UI**:
   - Modern, responsive sidebar layout.
   - Native support for light and dark modes.
   - Consistent typography, spacing, and micro-interactions.
5. **Soft Deletions**:
   - Sessions must never be hard deleted; set and query `deleted_at`.
6. **Progress Tracking**:
   - Update the `Progress` section in this file at the conclusion of each project phase.

---

## Progress

### Phase 0: Project Inception & Setup
- [x] Initialized Git repository.
- [x] Created `PROJECT_BRIEF.md` containing product specs, database model, and constraints.
- [x] Established directory structure (`/backend`, `/frontend`, `/reference`).
- [x] Created project `README.md`, `.gitignore`, and `.env.example` stubs.

### Phase 1: Backend Foundation & Authentication
- [x] Initialized FastAPI application structure in `/backend` (`app/core`, `app/models`, `app/schemas`, `app/routers`, `app/services`).
- [x] Created all SQLAlchemy models matching the project data model (`User`, `Session`, `TestCase`, `TestStep`, `Attachment`, `ExportLog`, `UserSetting`).
- [x] Configured Alembic with async migration support for both SQLite and PostgreSQL. Generated and applied the initial schema migration.
- [x] Implemented Argon2 password hashing and JWT authentication via `httpOnly`, `SameSite=Lax` session cookies.
- [x] Implemented `/api/v1/auth/register` (first user becomes admin, subsequent registrations require admin credentials), `/api/v1/auth/login`, `/api/v1/auth/logout`, and `/api/v1/auth/me`.
- [x] Built the `get_current_user` dependency enforcing authentication and role verification.
- [x] Implemented the admin seed script (`app.seed` / `seed.py`) driven by environment variables.
- [x] Configured CORS middleware with credentials enabled for Vite dev server origin (`http://localhost:5173`).
- [x] Added automated pytest test suite covering all authentication flows, permissions, cookies, and fresh database migrations.
