# Margin local development

This document defines the repository and command conventions for the V0 application. M1-T12
established the integrated verification baseline for the completed application foundation.

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
| Install frontend dependencies | `(cd apps/web && pnpm install --frozen-lockfile)` | M1-T07 |
| Start the web app | `(cd apps/web && pnpm dev --port 3000)` | M1-T07 |
| Run frontend tests | `(cd apps/web && pnpm test)` | M1-T07 |
| Frontend lint | `(cd apps/web && pnpm lint)` | M1-T07 |
| Frontend type check | `(cd apps/web && pnpm typecheck)` | M1-T07 |
| Apply database migrations | `uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head` | M1-T09 |
| Run end-to-end verification | `(cd apps/web && pnpm exec playwright test ../../tests/e2e)` | M5 |

The implementing ticket may correct a command only when its selected tool cannot support the
documented form. It must update this file and `AGENTS.md` in the same change so there is one
authoritative workflow.

## M1 integrated verification baseline

Run this ordered procedure from a clean checkout. It is the authoritative M1 verification
procedure; it uses no provider credential and does not run live spikes.

0. Bootstrap the toolchain. Install CPython 3.12 and Node.js 22 using the versions selected by
   `.python-version` and `.nvmrc`. Install [`uv`](https://docs.astral.sh/uv/getting-started/installation/)
   with its official instructions, then enable Corepack. From the repository root, Corepack reads
   `apps/web/package.json` and installs its pinned `pnpm` 10 release:

   ```sh
   corepack enable
   (cd apps/web && corepack install)
   uv --version
   (cd apps/web && pnpm --version)
   ```

1. Install locked dependencies:

   ```sh
   uv sync --project apps/api --all-groups
   (cd apps/web && pnpm install --frozen-lockfile)
   ```

2. Create `apps/api/.env` only if it does not already exist. This command never overwrites an
   existing local environment file. Keep `OPENROUTER_API_KEY` empty for this baseline:

   ```sh
   if [ ! -e apps/api/.env ]; then
     cp apps/api/.env.example apps/api/.env
   fi
   ```

3. Create and migrate a unique ignored verification database. Keep this shell open for the API
   process in step 5 so it uses the same database. The run ID makes each invocation a fresh
   migration without deleting an existing verification database:

   ```sh
   mkdir -p var/m1-verification
   MARGIN_VERIFICATION_RUN_ID="$(date -u +%Y%m%dT%H%M%SZ)-$$"
   export MARGIN_DATABASE_URL="sqlite:///var/m1-verification/${MARGIN_VERIFICATION_RUN_ID}.db"
   uv run --project apps/api alembic -c apps/api/alembic.ini upgrade head
   ```

4. Run all automated checks:

   ```sh
   uv run --project apps/api pytest apps/api/tests
   uv run --project apps/api ruff check apps/api
   uv run --project apps/api mypy apps/api/src
   (cd apps/web && pnpm test)
   (cd apps/web && pnpm lint)
   (cd apps/web && pnpm typecheck)
   ```

5. In the same shell that performed the migration, start exactly one API worker against that
   migrated verification database. In a separate terminal, start the web application:

   ```sh
   uv run --project apps/api uvicorn margin_api.main:app --reload --port 8000
   (cd apps/web && pnpm dev --port 3000)
   ```

6. Open `http://127.0.0.1:3000/api-health`, confirm that it says “The local API is connected,” and
   inspect the browser console for errors. The same-origin route must also return the API health
   response:

   ```sh
   curl --fail http://127.0.0.1:3000/api/health
   ```

The procedure exercises the Next.js rewrite, API health endpoint, fresh Alembic migration, domain
schema persistence tests, and deterministic fake capability tests together. It deliberately does
not treat a live OpenRouter call as a normal automated check.

## M1 accepted configuration and constraints

`apps/api/.env.example` is the authoritative non-secret configuration. The values below were
measured by the M1 spike reports and are repeated here to make the implementation constraints easy
to find:

| Area | Initial configuration | Accepted constraint |
| --- | --- | --- |
| PDF extraction | `pypdf` 6.1.1 with `pdfplumber` 0.11.7 | The selected checksum-pinned Constitution PDF is text-based and needs no OCR. Its unusable outline and one signature-page multi-column exception require deterministic layout/fallback processing; arbitrary-PDF support is unproven. |
| Recording and STT | Chromium WebM/Opus, `openai/gpt-4o-transcribe`, 120 seconds, 2,000 normalized-question characters | The verified Chromium path needs no audio conversion. Longer recordings and other browser formats require later validation. |
| Reasoning | `openai/gpt-5.6-sol`, 128,000-token profile, 4,096 reserved answer tokens, 2,048-token safety margin, `o200k_base` plus 4 framing tokens | Enforce either the selected token estimator or the 3.0-characters-per-token fallback, never whichever makes a request fit. Reject over-limit questions or session dialogue; never truncate or summarize source or dialogue. |
| TTS | `microsoft/mai-voice-2`, `en-US-Harper:MAI-Voice-2`, MP3, speed 1.0 | Generate paragraph or stored-answer audio only. Validate non-empty `audio/mpeg` bytes; one bounded retry is reserved for documented transient provider failures. |
| Audio cache | Contract version, model, voice, MP3 format, speed, and optional style/style degree form the cache version | Changing any byte-affecting synthesis input must select a new cache namespace. Browser playback speed is not a synthesis-cache input. |

The PDF, STT, TTS, and reasoning reports under `docs/spikes/` retain their reproducible commands,
measurements, live-run evidence, and unresolved risks. Provider routing, price, latency, tokenizer
compatibility, and model availability can drift, so provider checks stay explicit and opt-in.
