# Margin local development

This document defines the repository and command conventions for the V0 application. M1-T01
established the contract, and M1-T06 created the FastAPI application. Later M1 tickets create the
remaining application files and make their owning commands executable.

## Repository layout

All commands are run from the repository root unless a command says otherwise.

```text
Margin/
├── apps/
│   ├── api/
│   │   ├── pyproject.toml          # Python project and tool configuration
│   │   ├── uv.lock                 # locked Python dependencies
│   │   ├── .env.example            # documented backend configuration, never secrets
│   │   ├── src/margin_api/         # FastAPI application package
│   │   ├── tests/                  # backend unit and API tests
│   │   ├── alembic.ini             # added with the persistence foundation
│   │   └── alembic/                # database migrations
│   └── web/
│       ├── package.json            # frontend scripts and pinned package manager
│       ├── pnpm-lock.yaml          # locked frontend dependencies
│       ├── .env.example            # server-only local proxy configuration, if needed
│       ├── src/                     # Next.js application and colocated unit tests
│       └── tests/                   # broader frontend integration tests
├── tests/
│   └── e2e/                        # Playwright tests crossing the web/API boundary
├── docs/
│   └── spikes/                     # durable capability-spike reports and measurements
├── var/                             # ignored local database, uploads, recordings, and audio
├── DEVELOPMENT.md                   # this local workflow
└── AGENTS.md                        # engineering rules and authoritative command index
```

Application code is limited to `apps/api` and `apps/web`. Backend tests live with the API project,
frontend tests live with the web project, and only tests that operate both running applications
belong in root `tests/e2e`. Capability-spike reports are durable documentation under `docs/spikes`;
disposable spike scripts should stay within the selected spike ticket and must not become a second
application architecture.

`var/` is the only repository-local runtime-data root. It will contain the SQLite database,
uploaded PDFs, temporary recordings, and reproducible audio caches in ticket-defined subfolders.
It is ignored in full and must never contain source-controlled fixtures. Small legal test fixtures
belong under the test suite that owns them.

## Runtimes and package managers

- Python: CPython 3.12.x, selected by `.python-version`.
- Python packages and virtual environment: `uv`; the API ticket will commit `apps/api/uv.lock`.
- JavaScript runtime: Node.js 22.x LTS, selected by `.nvmrc`.
- JavaScript packages: `pnpm` 10.x through Corepack; the web ticket will pin an exact release in
  `apps/web/package.json` and commit `apps/web/pnpm-lock.yaml`.

Lockfiles are required. Dependency changes use the owning package manager and update the relevant
lockfile in the same change. Do not add a root JavaScript workspace or Python project unless a
later ticket demonstrates a shared-code need.

## Environment and local data

Backend settings live in `apps/api/.env`, created locally from `apps/api/.env.example` once M1-T06
adds it. OpenRouter credentials and all provider/context settings are backend-only. They must not
use a `NEXT_PUBLIC_` prefix, appear in frontend environment files, or be returned by an API route.

The committed API example records the measured M1 defaults for model IDs, recording duration,
context-budget inputs, and TTS settings. Local paths and database behavior also have typed settings,
although M1-T09 owns the database integration. The API validates all configured values at startup.
`OPENROUTER_API_KEY` is intentionally optional until a provider-backed operation is invoked; that
operation must fail with the stable configuration-error response when the key is absent. The audio
cache version is derived from every byte-affecting TTS setting, so changing any of those settings
selects a new cache namespace automatically.

The web app should need no browser-visible secret. If M1-T08 requires a configurable development
rewrite target, it belongs in `apps/web/.env.local` as a server-only value and its safe placeholder
belongs in `apps/web/.env.example`.

Git ignores every `.env` variant except `.env.example`, plus dependency directories, caches, test
output, and all of `var/` (the required location for local databases, recordings, uploaded
documents, and generated audio). Example environment files contain names and non-secret
development defaults only.

## Local processes and ports

Local development uses two long-running processes:

| Process | Address | Constraint |
| --- | --- | --- |
| Next.js web | `http://127.0.0.1:3000` | Browser entry point; proxies same-origin `/api` requests. |
| FastAPI API | `http://127.0.0.1:8000` | Backend-only application; exactly one worker. |

The browser opens port 3000 and calls `/api`; it does not call port 8000 or OpenRouter directly.
Port 8000 may be used for local health checks. M1-T08 will establish the Next.js rewrite and must
not add permissive development CORS.

## SQLite operation

The API uses SQLite in WAL mode with foreign-key enforcement enabled for every connection. Run
exactly one FastAPI worker and do not run background writers in another process. Keep database
transactions short: application code must finish slow network or provider calls before opening a
transaction and persist their resulting application-owned values in a separate short transaction.
The configured database URL defaults to `sqlite:///var/margin.db`; tests instead supply a unique
temporary SQLite URL.

## Command contract

The following commands are the canonical interface later tickets must implement. Their owning
ticket is shown because they are intentionally unavailable in the current planning-only tree.

| Purpose | Root command | Available after |
| --- | --- | --- |
| Install backend dependencies | `uv sync --project apps/api --all-groups` | M1-T06 |
| Start the API | `uv run --project apps/api uvicorn margin_api.main:app --reload --port 8000` | M1-T06 |
| Run backend tests | `uv run --project apps/api pytest apps/api/tests` | M1-T06 |
| Backend lint | `uv run --project apps/api ruff check apps/api` | M1-T06 |
| Backend type check | `uv run --project apps/api mypy apps/api/src` | M1-T06 |
| Install frontend dependencies | `pnpm --dir apps/web install --frozen-lockfile` | M1-T07 |
| Start the web app | `pnpm --dir apps/web dev --port 3000` | M1-T07 |
| Run frontend tests | `pnpm --dir apps/web test` | M1-T07 |
| Frontend lint | `pnpm --dir apps/web lint` | M1-T07 |
| Frontend type check | `pnpm --dir apps/web typecheck` | M1-T07 |
| Apply database migrations | `uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head` | M1-T09 |
| Run end-to-end verification | `pnpm --dir apps/web exec playwright test ../../tests/e2e` | M5 |

The implementing ticket may correct a command only when its selected tool cannot support the
documented form. It must update this file and `AGENTS.md` in the same change so there is one
authoritative workflow.

## Contributor procedure

After the owning scaffold tickets exist:

1. Install CPython 3.12 and Node.js 22, then enable Corepack and install `uv`.
2. Run the backend and frontend dependency-install commands above.
3. Copy each committed `.env.example` to its ignored local counterpart and fill only required
   backend secrets. Keep runtime files under `var/`.
4. Start FastAPI on port 8000 in one terminal with exactly one worker.
5. Start Next.js on port 3000 in a second terminal and open `http://127.0.0.1:3000`.
6. Run the relevant test, lint, and type-check commands from the command table. Apply migrations
   before persistence-dependent work once M1-T09 is complete.

M1-T12 will exercise this procedure from a clean local state and may add a single integrated
verification command without changing the two-process, same-origin, single-writer constraints.
