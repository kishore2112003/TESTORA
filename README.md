# TESTORA - Test Case Management System

A modern, standalone web application for QA engineers to create, execute, manage, and export test cases per ticket session with autosave and multi-format reporting.

---

## Architecture Overview

- **Frontend**: React, Vite, TypeScript, Tailwind CSS, shadcn/ui, TanStack Query, React Router, React Hook Form
- **Backend**: Python FastAPI, SQLAlchemy 2.x, Alembic, Pydantic v2
- **Database**: PostgreSQL (SQLite supported for local development)
- **Authentication**: JWT in `httpOnly` cookies with Argon2 password hashing
- **Exports**: Excel (`openpyxl`) and Word (`docxtpl`) templates
- **AI Integration**: Anthropic API (for future test case generation & refinement)
- **Deployment**: Docker Compose

---

## Repository Structure

```text
TESTORA/
├── backend/                  # FastAPI backend application
│   ├── alembic/              # Database migration scripts
│   ├── app/
│   │   ├── api/v1/           # API endpoints & routing
│   │   ├── core/             # Configuration, security & database setup
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic v2 validation models
│   │   ├── services/         # Business logic (auth, exports, sessions)
│   │   └── templates/        # Document generation templates
│   └── tests/                # Automated backend tests
├── frontend/                 # React + Vite frontend application
│   ├── public/               # Static assets
│   └── src/
│       ├── assets/           # UI icons & images
│       ├── components/       # UI & layout components (shadcn/ui)
│       ├── features/         # Feature modules (auth, sessions, test cases, export)
│       ├── hooks/            # Custom React hooks
│       ├── lib/              # Utility functions & API clients
│       ├── services/         # Frontend API integration
│       └── types/            # TypeScript type definitions
├── reference/                # Export templates, specifications & sample docs
│   ├── docs/
│   └── templates/
├── .env.example              # Template environment variables
├── .gitignore
├── PROJECT_BRIEF.md          # Comprehensive product requirements & data models
└── README.md                 # Project documentation stub
```

---

## Getting Started

> Application code will be implemented in subsequent phases. Refer to [PROJECT_BRIEF.md](PROJECT_BRIEF.md) for full project specifications and progress.
