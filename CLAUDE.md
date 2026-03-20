# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**ZimPrep** is a ZIMSEC (Zimbabwe Schools Examination Council) exam preparation platform. Students practice past papers, submit answers that are AI-graded, and track their progress. Parents can monitor student performance. Admins ingest PDFs and manage the question catalog.

## Development Commands

### Frontend (Next.js 16 + React 19 + TypeScript)
```bash
cd frontend
npm install
npm run dev       # http://localhost:3000
npm run build
npm run lint      # ESLint
```

### Backend (FastAPI + Python)
```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # then fill in secrets
uvicorn main:app --reload   # http://localhost:8000
```

### Supabase (local)
```bash
supabase start    # spins up local Postgres + Auth + Storage
supabase stop
supabase reset    # re-runs all migrations
# Studio at http://127.0.0.1:54323, API at http://127.0.0.1:54321
```

There are no automated tests in this project.

## Architecture

### Data stores
| Store | Purpose |
|-------|---------|
| **MongoDB** | Questions, exam attempts, vector embeddings for RAG-based marking |
| **Supabase (PostgreSQL)** | Auth, subject/paper catalog, subscriptions, payments, RLS policies |
| **Supabase Storage** | PDF buckets: `past-papers`, `question-images`, `syllabus` |

### API routing
Next.js rewrites `/api/*` → `http://localhost:8000/*` (configured in `frontend/next.config.ts`). Frontend code calls `/api/...` paths; the rewrite transparently proxies to FastAPI.

### Backend layout (`backend/`)
- `main.py` — registers all routers and CORS middleware
- `core/config.py` — Pydantic `Settings` loaded from `.env`
- `routes/` — one file per domain: `admin`, `attempts`, `catalog`, `marking`, `ocr`, `questions`, `students`, `subscription`
- `services/` — business logic: `question_service`, `marking_service`, `batch_marking_service`, `retrieval_service`, `embedding_service`, `ocr_service`, `pdf_extraction_service`, `flutterwave_service`

### Frontend layout (`frontend/`)
- `app/` — Next.js App Router pages grouped by feature: `(dashboard)`, `(marketing)`, `auth`, `exam`, `results`, `subjects`, `history`, `parent`, `register`, `subscription`, `practice`
- `components/` — reusable UI built on Radix UI primitives + Tailwind CSS + shadcn/ui
- `lib/contracts/` — shared TypeScript interfaces (the canonical types layer)
- `lib/exam/store.ts` — Zustand store for in-progress exam state
- `lib/auth.ts` — Supabase Auth wrapper; `getUser()` reads from localStorage cache
- `lib/supabase.ts` — Supabase client singleton
- `lib/api-client.ts` — typed HTTP client for backend calls

### Key data flows

**Exam attempt:**
1. Student picks subject/paper → frontend calls `/api/questions`
2. Student submits answer → POST `/api/attempts`
3. Backend runs vector search (MongoDB) for relevant evidence, then calls Claude/OpenAI to grade
4. Result written to MongoDB; frontend polls `/api/results/{attempt_id}`

**PDF ingestion (admin):**
1. Admin uploads PDF → POST `/api/admin/papers`
2. Backend extracts text with PyMuPDF + Google Cloud Vision OCR
3. Text chunked, embedded, stored in MongoDB with vectors
4. Questions parsed and inserted into Supabase `papers_q`
5. Admin reviews and approves questions via PATCH `/api/admin/questions`

**Subscriptions:**
- Payment via Flutterwave; webhook hits POST `/api/subscription/webhook`
- Subscription records live in Supabase; RLS policies gate content access

### User roles
`admin` | `student` | `parent` — enforced via Supabase RLS and frontend role guards in `lib/identity/roleGuards.ts`

## Environment variables

**Backend** (see `backend/.env.example`): `MONGO_URI`, `MONGO_DB`, `SUPABASE_URL`, `SUPABASE_ANON_KEY`, `SUPABASE_SERVICE_ROLE_KEY`, `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, `GOOGLE_APPLICATION_CREDENTIALS`, `FLUTTERWAVE_SECRET_KEY`, `BILLING_WEBHOOK_SECRET`, `JWT_SECRET`

**Frontend** (see `frontend/.env.example`): `NEXT_PUBLIC_API_URL`, `NEXT_PUBLIC_SUPABASE_URL`, `NEXT_PUBLIC_SUPABASE_ANON_KEY`
