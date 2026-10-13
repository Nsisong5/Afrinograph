# Afrinograph — V1 Greenfield Foundation Specification

**Version:** 1.0
**Status:** Proposed — pending confirmation on the item in §9 before Gemini builds against it
**Produced by:** Claude, Technical Specification Engineer
**Scope:** Deliverables 2 and 3 of the Corrective Chief Engineer Instruction — the initial repository scaffold and the confirmed implementation sequence, from an empty repository through the first working source adapter.

---

## 0. Context confirmation (Deliverable 1)

- The project is named **Afrinograph** (Africa Knowledge Graph). PDE is retired — do not use that name in new artifacts.
- Afrinograph is a **greenfield** project. No repository inspection was performed because no prior codebase exists. The earlier repository-audit instruction is withdrawn.
- The approved V1 scope is unchanged: the **Africa Signal Collector**. It acquires, normalizes, and preserves evidence with provenance. It does **not** decide whether evidence represents a problem or an opportunity — that belongs to future modules.
- The central principle carried forward: **different sources, one consistent downstream evidence contract**, with raw evidence, source-specific context, provenance, deduplication, and idempotency handled deliberately.

Nothing below claims any file has been created or any test has been run. This is the specification Gemini CLI will execute against, in the chunks defined here and in the module specification that follows this document.

---

## 1. Repository scaffold

```
afrinograph/
├── pyproject.toml
├── uv.lock
├── README.md
├── .env.example
├── .gitignore
├── .python-version
├── alembic.ini
├── src/
│   └── afrinograph/
│       ├── __init__.py
│       ├── main.py                     # FastAPI app factory — no business logic
│       ├── config.py                   # Settings (pydantic-settings)
│       ├── logging.py                  # structured logging setup
│       ├── shared/                     # narrow cross-cutting kernel — see §1.1
│       │   ├── __init__.py
│       │   ├── domain/
│       │   │   ├── __init__.py
│       │   │   ├── errors.py           # base domain/application exception types
│       │   │   └── value_objects.py    # e.g. UtcDateTime wrapper
│       │   ├── application/
│       │   │   ├── __init__.py
│       │   │   └── ports.py            # Clock port, IdGenerator port
│       │   └── infrastructure/
│       │       ├── __init__.py
│       │       ├── clock.py            # SystemClock implementation
│       │       └── db.py               # shared SQLAlchemy engine/session factory
│       └── modules/
│           ├── __init__.py
│           └── source_contract/        # first module — see MODULE_01 spec
│               ├── __init__.py
│               ├── domain/
│               ├── application/
│               └── infrastructure/
├── migrations/
│   ├── env.py
│   ├── script.py.mako
│   └── versions/
├── tests/
│   ├── conftest.py
│   ├── unit/
│   ├── contract/
│   ├── integration/
│   ├── api/
│   └── architecture/
│       └── test_module_boundaries.py
├── AI_instructions/
│   ├── 00_START_HERE.md
│   ├── 01_PROJECT_CONSTITUTION.md
│   ├── 02_ARCHITECTURE_RULES.md
│   ├── 03_MODULE_RULES.md
│   ├── 04_CODING_RULES.md
│   ├── 05_TESTING_RULES.md
│   ├── 06_SECURITY_RULES.md
│   ├── 07_DATABASE_RULES.md
│   ├── 08_API_RULES.md
│   ├── 09_DOCUMENTATION_RULES.md
│   ├── 10_SESSION_PROTOCOL.md
│   └── 11_DEFINITION_OF_DONE.md
├── AI_state/
│   ├── CURRENT_STATE.md
│   ├── CURRENT_TASK.md
│   ├── PROGRESS.md
│   ├── COMPLETED_WORK.md
│   ├── IN_PROGRESS.md
│   ├── KNOWN_ISSUES.md
│   ├── ARCHITECTURE_STATE.md
│   ├── DATABASE_STATE.md
│   ├── API_STATE.md
│   ├── TEST_STATE.md
│   ├── DECISIONS.md
│   └── SESSION_HANDOFF.md
└── docs/
    └── modules/                        # one .md per module, copied from its approved spec
```

`AI_instructions/` and `AI_state/` are workspace-only, per Part 19 of the original handoff — not pushed to GitHub unless you explicitly say otherwise.

### 1.1 Why `shared/` exists, and why it is this small

A shared kernel is a common way to reintroduce coupling by accident, so it is scoped to exactly three things that every module genuinely needs and that Part 4.7 already names as legitimate outbound ports:

- **Clock port** (`Clock.now()` / `SystemClock`) — every module needs current time (`observed_at`, `collected_at`, run timestamps) and every module needs to fake it in tests for deterministic idempotency checks.
- **A base domain error type** — so the error taxonomy in Part 13.1 is consistent across modules instead of each module inventing its own exception root.
- **One SQLAlchemy `Engine`/session factory** — one physical database connection pool for V1. This is connection *plumbing* only. It does not carry any table, any ORM base with business columns, or any query logic — each module defines its own models and repositories on top of it. Sharing the engine is not the same as sharing ownership (Part 4.9).

Nothing else goes in `shared/` without a demonstrated cross-module need — this is the Part 4.10 discipline applied to the kernel itself.

---

## 2. Project configuration

| Decision | Choice | Note |
|---|---|---|
| Python version | 3.12, pinned via `.python-version` | |
| Dependency/env management | `uv` (pyproject.toml + uv.lock) | Single fast tool instead of separate venv/pip/poetry steps. Swapping to Poetry later is a low-cost change if you prefer it — flagging as a tooling choice made within my engineering authority, not an architectural one. |
| Config loading | `pydantic-settings`, typed `Settings` class in `config.py` | Reads from `.env` locally (git-ignored) and real env vars in deployment |
| Example config | `.env.example`, committed, placeholder values only, comments explaining each var | No real secrets ever committed — Part 12.2 |
| Lint/format | `ruff` | One fast tool, not three |
| Type checking | `mypy`, warn-only for V1 | Enforced-as-blocking is a reasonable later upgrade once module count grows |

`config.py` holds only foundation-level settings in this phase: `DATABASE_URL`, `APP_ENV` (`local`/`test`/`ci`/`prod`), `LOG_LEVEL`. Per-adapter secrets (Reddit API keys, etc.) are added by each adapter module when it lands, never here — see Part 12.1.

---

## 3. Initial application entry point

- `src/afrinograph/main.py` exposes `create_app() -> FastAPI`, an app factory. It does exactly three things: load `Settings`, configure structured logging, and register a exception-handler translation layer that maps domain/application errors to HTTP responses without leaking internals (Part 13.1). It registers **zero** business routes in the foundation phase.
- Each module adds its own router only when that module's inbound-adapter chunk is implemented (Module H, per Part 8) — routing is not pre-declared for modules that don't exist yet.
- No CLI entry point is created in the foundation phase. One is introduced by Module G (Scheduling/Execution) when it needs a way to trigger collection manually — creating it earlier would be scaffolding for a module that doesn't exist yet, which Part 4.10 rules out.

---

## 4. Database foundation

- **Single PostgreSQL 16 instance** for V1, consistent with Part 4.9 ("modules may share one database").
- **Recommendation flagged for confirmation in §9:** each module gets its **own Postgres schema** (`source_registry`, `raw_evidence`, `evidence`, `collection_runs`, etc.), not just a table-naming convention within one shared `public` schema. Each module's SQLAlchemy models declare `schema="<module_schema>"`. This is what makes "a module must not query another module's tables directly" (Part 4.9) enforceable at the database level later — a module's DB role can eventually be restricted to `USAGE` on only its own schema — rather than remaining a code-review-only convention.
- SQLAlchemy 2.0, async engine, `asyncpg` driver. One `Engine` / `async_sessionmaker` built in `shared/infrastructure/db.py`, injected into each module's repository constructors.
- Alembic: **one shared migration history** under `migrations/` — simpler to operate in V1 than per-module histories. Ownership discipline is enforced by convention: each migration file touches exactly one module's schema and is named `<module>_<description>.py`. This is checked in review, not by an automated test, in V1 — an automated "one migration, one schema" check is a documented non-goal for now (§7).
- Test database strategy: a **locally installed PostgreSQL service** — no Docker, no testcontainers. This environment is proot-distro Ubuntu, which doesn't run a Docker daemon, so the original testcontainers recommendation is withdrawn and replaced below. Postgres is installed and started once as part of environment setup (§4.1); a `conftest.py` fixture connects to it via `TEST_DATABASE_URL` and creates/drops a dedicated `afrinograph_test` database (or truncates its schemas) around each integration test session. Unit, contract, and architecture tests never touch a real database.

### 4.1 Local PostgreSQL setup (proot-distro Ubuntu)

No Docker daemon is available inside proot, so Postgres runs as a native service in the same Ubuntu environment as the code:

```bash
apt update && apt install -y postgresql
# proot environments typically lack a working init system, so start the
# cluster directly rather than via `service postgresql start`:
pg_ctlcluster <version> main start
# one-time setup: a role matching your user, plus dev and test databases
su postgres -c "createuser -s $(whoami)"
createdb afrinograph_dev
createdb afrinograph_test
```

If `pg_ctlcluster` isn't present, `/etc/init.d/postgresql start` is the usual fallback. Set `DATABASE_URL` and `TEST_DATABASE_URL` in `.env` to point at these two databases — both get a placeholder entry in `.env.example`.

**If the cluster fails to start with a shared-memory error:** proot can restrict the POSIX shared-memory segments Postgres defaults to. `dynamic_shared_memory_type` is a documented, standard Postgres setting for exactly this situation — its own docs describe `mmap` as the fallback "when other shared memory facilities are not available." Set `dynamic_shared_memory_type = mmap` in `postgresql.conf` (found via `pg_lsclusters` or under `/etc/postgresql/<version>/main/`) and restart the cluster. This is a legitimate local-dev setting, not a hack — just not the default outside this kind of constrained environment.

---

## 5. Testing foundation

- Stack: `pytest`, `pytest-asyncio`, `pytest-cov`, `httpx` (API tests via `ASGITransport` against the FastAPI app, no real socket).
- Markers registered in `pyproject.toml`: `unit`, `contract`, `integration`, `api`, `architecture`.
- Plain `pytest` (no `-m` filter) runs `unit` + `contract` + `architecture` + `api` — none of these touch Postgres. `integration` is opt-in via `pytest -m integration` and is the only suite Gemini must call out as "requires the local Postgres service to be running" (§4.1) in its completion report.
- **Architecture tests** (`tests/architecture/test_module_boundaries.py`): a small, dependency-free `ast`-based scanner — no new library — that fails the suite if any file under a module's `domain/` imports `sqlalchemy`, `fastapi`, `httpx`, another module's package path, or its own module's `infrastructure/` package. This operationalizes Part 4.4 and Part 16.5. Kept intentionally simple for V1; `import-linter` is a documented future upgrade if the ruleset outgrows a ~50-line script.
- **Gemini test-reporting format** (mirrored into `AI_instructions/05_TESTING_RULES.md`): for every chunk — exact commands run, pass/fail counts, any test not run and why, outstanding manual verification. A test is never reported as passing unless it was actually executed in that session (Part 16.8).

---

## 6. Documentation foundation

Three tiers, kept distinct on purpose:

1. **`docs/modules/<module>.md`** — durable, developer-facing documentation. Populated by copying the approved module specification once a module is implemented and verified. This is what a future developer or a different coding model reads to understand the system.
2. **`AI_instructions/`** — governs *how* a coding model must behave. Written once at foundation time, changes rarely.
3. **`AI_state/`** — reflects *actual, verified* current state. Updated every session. Never a forward-looking or aspirational summary — only what has been implemented and tested (Part 19.2).

### 6.1 `AI_instructions/` — initial contents

**00_START_HERE.md**
- Read order: this file → 01 → 02 → `AI_state/CURRENT_STATE.md` → `AI_state/CURRENT_TASK.md` → the relevant module spec in `docs/modules/`.
- Inspect the actual repository before writing anything — never trust a doc's claim about what exists over the filesystem.
- Confirm the authorized chunk before coding. Do not proceed past it.

**01_PROJECT_CONSTITUTION.md**
- Project: Afrinograph — Africa Signal Collector (V1). Long-term vision: Africa-focused knowledge system; V1 builds only the collector.
- Central principle: different sources, one common evidence contract; raw evidence and provenance preserved; interpretation is out of scope.
- Decision authority: Chief Engineer (architecture) → Claude (specification) → Gemini (implementation) → project owner (product/final decisions). Gemini does not redesign module boundaries or public contracts.

**02_ARCHITECTURE_RULES.md**
- Modular monolith, Hexagonal/Ports-and-Adapters, Clean Architecture dependency direction: infrastructure → application → domain, never reversed.
- Domain layer: zero imports of FastAPI, SQLAlchemy, provider SDKs, HTTP clients, or scheduler libraries.
- Each module owns its persistence model; see `07_DATABASE_RULES.md` for the schema-per-module convention.
- Cross-module communication only through a module's declared public interface (its `application`-layer ports), never direct imports of another module's `domain`/`infrastructure`.

**03_MODULE_RULES.md**
- One module = one directory under `src/afrinograph/modules/`, with its own `domain/`, `application/`, `infrastructure/`.
- A module's public surface is whatever its `application/ports.py` (or equivalent) exposes — nothing else is safe for another module to import.
- New modules require an approved specification in `docs/modules/` before implementation begins.

**04_CODING_RULES.md**
- Follow the module specification's exact file paths. Do not invent alternate locations.
- No new dependency without a stated justification in the chunk's completion report.
- Docstrings on every public class/function in `application` and `domain` layers explaining the contract, not just the implementation.

**05_TESTING_RULES.md**
- Test types and markers as defined in §5 above.
- Report format: commands run, pass/fail counts, skipped tests + reason, manual verification still required. Never claim a test passed without having run it this session.

**06_SECURITY_RULES.md**
- No secrets in source, git-tracked config, logs, or example files (Part 12.2).
- Treat all external content (adapter responses) as untrusted input — validate before using.
- No credential ever lives in a domain entity.

**07_DATABASE_RULES.md**
- One module, one Postgres schema (pending confirmation — §9). One shared Alembic history, one migration file per schema per change, named `<module>_<description>.py`.
- No cross-schema queries from application code. No ORM model imported outside its owning module.

**08_API_RULES.md**
- HTTP routes live only in a module's inbound-adapter layer and call application use cases — no business logic in route handlers.
- Every endpoint documents method, path, auth requirement, request/response schema, and error responses before merge.

**09_DOCUMENTATION_RULES.md**
- Every module ships a `docs/modules/<module>.md` before it is marked done.
- `AI_state/` is updated in the same session as the code change it describes — never batched "later."

**10_SESSION_PROTOCOL.md**
- Start of session: read per `00_START_HERE.md`.
- End of session: update `AI_state/SESSION_HANDOFF.md` with what was completed, files touched, tests run and results, manual verification outstanding, and the exact next step.

**11_DEFINITION_OF_DONE.md**
- Mirrors Part 23 of the original handoff, applied per-module. A module is not done until every checklist item is either satisfied or explicitly recorded as outstanding — never silently skipped.

### 6.2 `AI_state/` — initial contents (foundation phase: nothing built yet)

**CURRENT_STATE.md** — "Foundation phase: scaffold specified, not yet implemented. No code exists."
**CURRENT_TASK.md** — "Awaiting confirmation on §9 (schema-per-module), then: implement foundation chunk 1 (repo scaffold + tooling)."
**PROGRESS.md** — empty table, columns: Module | Phase | Status | Last updated.
**COMPLETED_WORK.md** — empty.
**IN_PROGRESS.md** — empty.
**KNOWN_ISSUES.md** — empty.
**ARCHITECTURE_STATE.md** — "Modular monolith, hexagonal, dependency direction inward. No modules implemented yet."
**DATABASE_STATE.md** — "No database created. No migrations exist yet."
**API_STATE.md** — "No HTTP endpoints exist yet."
**TEST_STATE.md** — "No tests exist yet."
**DECISIONS.md** — populated now, since real decisions were already made:
- Renamed PDE → Afrinograph; greenfield confirmed; no legacy code.
- Dependency/env tool: `uv`.
- Integration DB strategy: locally-installed PostgreSQL service, no Docker (dev environment is proot-distro Ubuntu) — see foundation doc §4.1.
- Architecture-boundary check: custom `ast` scanner, not `import-linter`, for V1.
- Adapter `collect()` is `async` (see Module 01 spec, §Open Decisions).
- **Pending:** schema-per-module for Postgres — see foundation doc §9.

**SESSION_HANDOFF.md** — "No sessions have run yet. First session should begin at foundation chunk 1."

---

## 7. What the foundation phase explicitly does NOT include

- No source adapters, registry, evidence, or collection-run tables — those migrations belong to their respective modules, not to the foundation.
- No automated check that a migration touches only one schema — review discipline only, for now.
- No CI pipeline definition — not requested yet; flagged as a real gap but not a blocker for module work to begin.
- No authentication/authorization on the API — there are no endpoints yet; Module H must define this before any real endpoint ships.

---

## 8. Confirmed module sequence

The Chief Engineer's proposed 16-item sequence is preserved with one adjustment: "core architecture rules and contracts" is folded into this foundation document and into `AI_instructions/02_ARCHITECTURE_RULES.md` rather than issued as its own module artifact, because it establishes rules rather than building a testable unit — Part 20 reserves the one-Markdown-per-module format for things that produce code and tests. Everything downstream of it is unchanged and renumbered accordingly.

1. **Foundation** (this document) — repo scaffold, tooling, DB/testing/doc foundation. *Proof: `uv sync`, `alembic upgrade head` (no-op), app boots, empty test suite exits 0.*
2. **Source Contract & Adapter Interface** *(next deliverable — see `AFRINOGRAPH_MODULE_01_SOURCE_CONTRACT.md`)* — adapter interface, collection request/response DTOs, raw item DTO, capability enum, error taxonomy. No persistence. *Proof: a fake adapter satisfies the contract with no real provider involved.*
3. **Source Registry** — depends on (2) for the types it stores references to. Source identity, non-secret config, enable/disable, adapter association. *Proof: a source can be registered and retrieved through its public interface.*
4. **Raw Evidence & Provenance** — depends on (2) for `RawSourceItem`. Preserves original evidence, source-item identity, observation history. *Proof: a raw item is preserved and traceable to its source.*
5. **Collection Orchestration** — depends on (2), (3), (4). Coordinates the collection use case, run lifecycle, failure isolation, checkpoints. *Proof: a fake source adapter is collected end-to-end through the application layer.*
6. **Normalization & Identity** — depends on (4). Canonical evidence DTO, deterministic normalization, dedup rules, normalization versioning. *Proof: differently-shaped fake inputs map to the same common contract without losing required provenance.*
7. **Persistence Integration** — depends on (3)–(6) each owning their schema. Repository implementations, migrations, uniqueness/transaction guarantees. *Proof: repeated ingestion of the same fixture produces no duplicate canonical evidence.*
8. **Scheduling & Execution** — depends on (5). Minimal trigger/dispatch abstraction; CLI entry point introduced here. *Proof: collection can be triggered without coupling the core to a specific scheduler.*
9. **RSS/Atom Adapter** — depends on (2), (5), (6), (7). First real external source. *Proof: a real feed flows through the full pipeline.*
10. **Reddit Adapter** — depends on same as (9). *Proof: Reddit uses the identical pipeline without Reddit-specific branching in the core.*
11. **Third-Source Adapter** — selected after (9)/(10) prove the abstraction; candidate research happens then, not now.
12. **Collection Management Interface** — depends on (3), (5). FastAPI/CLI entry points calling existing use cases only.
13. **Architecture Enforcement** — hardens the checks sketched in §5; can start as soon as (2)–(3) exist and grows with each module.
14. **End-to-End Verification** — full suite, repeat-collection idempotency, provenance, failure recovery.
15. **Documentation & Final Handoff** — `docs/modules/` finalized for every module, `AI_state/` reconciled, session handoff written.

No item here authorizes Gemini to implement beyond the currently approved chunk — sequencing shows dependency order, not a blanket license to proceed.

---

## 9. Item flagged for confirmation before implementation

**Existing/default assumption:** the handoff states modules "may share one PostgreSQL database" and must not bypass each other's tables, without specifying the enforcement mechanism.

**Problem:** a shared `public` schema with table-name prefixes relies entirely on code review to catch a cross-module query or a stray foreign key — it's easy to violate by accident and hard to catch in a growing codebase.

**Consequence of leaving it as-is:** module boundaries are real in the Python code but soft at the database layer; a future migration or a rushed query could quietly couple two modules' data models.

**Proposed alternative:** one Postgres schema per module (§4), with each module's ORM models declaring that schema explicitly. Costs nothing extra in V1 (still one physical database, one Alembic history) and creates a real path to DB-role-level enforcement later.

**Migration implications:** none — this is a greenfield decision, not a migration.

Please confirm schema-per-module, or tell me to default to a single shared schema with table-name prefixes instead, before I hand Gemini the Source Registry, Raw Evidence, or Normalization module specs (all three define tables).

---

## 10. Manual verification for the foundation itself

1. Clone the scaffold, run `uv sync` — expect a clean dependency install, no errors.
2. Copy `.env.example` to `.env` and fill in `DATABASE_URL` / `TEST_DATABASE_URL` for the local Postgres service set up per §4.1.
3. Confirm the local Postgres cluster is running (`pg_lsclusters`, or `pg_isready`); run `pytest` — expect the suite to collect and exit `0` with 0 tests (this is the correct, expected result at this phase — no test files exist yet).
4. Run `alembic upgrade head` — expect a no-op success (no migrations exist yet).
5. Run `uvicorn afrinograph.main:create_app --factory --reload` — expect the app to boot and respond with a sane 404 on any path (no routes registered yet is correct).
6. Cleanup: `dropdb afrinograph_test && createdb afrinograph_test` resets the test database to empty if anything was left behind.

## 11. Definition of Done — foundation phase

- [ ] Scaffold matches §1 exactly, or deviations are recorded in `AI_state/DECISIONS.md` with reasoning.
- [ ] `uv sync`, `alembic upgrade head` (no-op), app boot, and empty `pytest` run all succeed as described in §10.
- [ ] `AI_instructions/` and `AI_state/` populated with the initial content in §6.
- [ ] §9 has been explicitly confirmed or overridden by the owner/Chief Engineer.
- [ ] No module code, tables, or routes exist yet — foundation stays foundation-only.
- [ ] `AI_state/SESSION_HANDOFF.md` updated with exact next step: begin Module 01 (Source Contract) chunk 1.

---

## 12. Gemini implementation chunks — foundation phase

None of these chunks create a database table, so all eight are unblocked regardless of how §9 is resolved. §9 only gates the Source Registry / Raw Evidence / Normalization module specs, not this document. Docker is not used anywhere in this project — Chunks 4 and 5 assume a locally installed Postgres service per §4.1.

### Chunk 1 — Repository skeleton and tooling
**Objective:** the directory tree in §1 exists exactly (package `__init__.py` files in place, no implementation code yet); `pyproject.toml` configures `uv`, `ruff`, `mypy` (warn-only), and pytest markers (`unit`, `contract`, `integration`, `api`, `architecture`); `.env.example`, `.gitignore`, `.python-version`, `README.md` stub exist.
**Files:** everything in §1's tree except file *contents* under `shared/`, `main.py`, `config.py`, `migrations/`, `AI_instructions/`, `AI_state/` — those are later chunks. This chunk is structure + tooling only.
**Instructions:** no business logic in this chunk — if you find yourself writing a function body, stop, that belongs to a later chunk.
**Tests:** none yet (nothing to test).
**Acceptance criteria:** `uv sync` succeeds; `ruff check .` runs clean; the tree matches §1 (report any deviation, don't silently resolve it).
**Completion report:** tree listing, `uv sync` output.

### Chunk 2 — Shared kernel: Clock, base errors, DB engine bootstrap
**Objective:** `shared/domain/errors.py`, `shared/domain/value_objects.py`, `shared/application/ports.py` (`Clock` Protocol), `shared/infrastructure/clock.py` (`SystemClock`), `shared/infrastructure/db.py` (async engine/session factory reading `DATABASE_URL` from `Settings`) — all implemented and unit-tested.
**Preconditions:** Chunk 1 complete.
**Business rule to test explicitly:** importing `shared.infrastructure.db` must **not** open a real database connection at import time — connection happens lazily, on first session use. This is what keeps unit tests DB-free.
**Tests:** `SystemClock.now()` returns a timezone-aware UTC `datetime`; the db module import test above.
**Acceptance criteria:** `pytest -m unit` passes with these tests included.
**Completion report:** standard format.

### Chunk 3 — App factory, config, logging
**Objective:** `config.py` (`Settings`), `logging.py`, `main.py` (`create_app()`) per §3, including the exception-handler layer that translates `shared.domain.errors` base exceptions to HTTP responses without leaking internals.
**Preconditions:** Chunk 2 complete.
**Tests (api marker):** using `httpx` + `ASGITransport` against `create_app()` — an unregistered route returns 404; the app boots without error.
**Acceptance criteria:** `pytest -m api` passes; manual boot (`uvicorn afrinograph.main:create_app --factory`) succeeds per §10 step 5.
**Completion report:** standard format.

### Chunk 4 — Alembic initialization
**Objective:** `alembic.ini`, `migrations/env.py`, `migrations/script.py.mako` configured against the engine from Chunk 2; empty `migrations/versions/`; `alembic upgrade head` succeeds as a no-op.
**Preconditions:** Chunk 2 complete; the local Postgres service from §4.1 is installed and running, with `afrinograph_test` created.
**Tests (integration marker — requires the local Postgres service, not Docker):** against `TEST_DATABASE_URL`, run `alembic upgrade head` programmatically, assert exit code 0 and zero tables created; the fixture should leave `afrinograph_test` empty afterward (truncate rather than drop, since the database itself is expected to persist across runs).
**Acceptance criteria:** `pytest -m integration -k alembic` passes with the local Postgres service running.
**Completion report:** standard format, explicitly confirm the local service (not Docker) was used and note its connection details were read from `TEST_DATABASE_URL`.

### Chunk 5 — Testing foundation: architecture checker + shared fixtures
**Objective:** `tests/architecture/test_module_boundaries.py` (the `ast`-based scanner from §5) implemented; `tests/conftest.py` with a session-scoped `test_db` fixture that connects to the already-running local Postgres service via `TEST_DATABASE_URL` and truncates all module schemas/tables before and after the session — reused by Chunk 4 and all future integration tests. This fixture assumes Postgres is already running (§4.1); it does not start or stop the service itself.
**Preconditions:** Chunks 1–2 complete; local Postgres service running per §4.1.
**Business rule to test:** the checker must be proven to actually catch a violation, not just pass trivially because no modules exist yet — write one fixture-only "bad" module snippet (not shipped in `src/`) with a forbidden import and assert the checker flags it.
**Acceptance criteria:** `pytest -m architecture` passes, including the self-test described above.
**Completion report:** standard format.

### Chunk 6 — `AI_instructions/` files
**Objective:** all 12 files listed in §6.1 created with that content.
**Preconditions:** none (can run in parallel with Chunks 2–5, but do it after Chunk 1 so the folder exists).
**Acceptance criteria:** all 12 files present; content matches §6.1 or deviation is noted in the completion report.

### Chunk 7 — `AI_state/` files
**Objective:** all 12 files listed in §6.2 created with that initial content, `DECISIONS.md` populated with the real decisions already made.
**Preconditions:** none, same note as Chunk 6.
**Acceptance criteria:** all 12 files present; `DECISIONS.md` correctly reflects whether §9 has been confirmed at time of execution — if it's still open, the file must say so explicitly, not guess an answer.

### Chunk 8 — Foundation manual verification and handoff
**Objective:** execute §10's manual verification steps in order and record the actual results; update `AI_state/SESSION_HANDOFF.md` with the exact next step (begin Module 01, Chunk 1).
**Preconditions:** Chunks 1–7 complete.
**Acceptance criteria:** every §10 step passes as described; §11's Definition of Done checklist is fully checked or exceptions are explicitly recorded — never marked done by default.
**Completion report:** full §10 results, final `AI_state/SESSION_HANDOFF.md` content.
