# Afrinograph Module Specification — Source Contract & Adapter Interface

**Module ID:** `source_contract`
**Corresponds to:** Original handoff, Module B (Part 8) + Phase 1 (Part 22, renumbered as sequence item 2 in the foundation doc). Also what the Chief Engineer's later handoffs call **Module 2: Source Contracts & DTOs** — same module, no rename of this file.
**Depends on:** Foundation phase only (`shared/domain/errors.py`, `shared/application/ports.py::Clock`)
**Depended on by:** Source Registry, Raw Evidence & Provenance, Collection Orchestration, Normalization & Identity, every future source adapter
**Precondition:** Foundation phase complete and verified per `AFRINOGRAPH_00_FOUNDATION_AND_SEQUENCE.md` §10–11.

---

## 1. Purpose

This module defines the **stable boundary** between Afrinograph's core and every external source. It is pure contract: interfaces, DTOs, an error taxonomy, and a capability vocabulary. It contains **no provider-specific code and no persistence** — that is the entire point of building it first. Its proof of correctness is that a fake, in-memory adapter can satisfy it completely, with zero knowledge of Reddit, RSS, or any real provider.

## 2. Responsibilities

**Owns:**
- The `SourceAdapter` interface every concrete adapter must implement.
- `CollectionRequest` / `CollectionResult` DTOs exchanged between the orchestrator and an adapter.
- `RawSourceItem` — the shape of one unprocessed item as an adapter hands it back.
- `SourceCapability` — the vocabulary for declaring what a given source can and can't do.
- The adapter-facing error hierarchy (`AdapterError` and subtypes).
- A reusable, parameterizable **contract test suite** any future adapter's tests can plug into.

**Does not own** (explicitly out of scope for this module):
- Registering or persisting source configuration (Source Registry).
- Storing raw or normalized evidence (Raw Evidence, Normalization).
- Deciding when or how often to collect (Orchestration, Scheduling).
- Any provider-specific logic (belongs inside each adapter's own package, added later).
- Credentials of any kind — this module's DTOs never carry a secret; the registry resolves credentials and hands an already-authenticated client concern to the adapter implementation, not to this contract.

## 3. Architecture context

Pure domain + a thin application-layer `Protocol`. No infrastructure package is needed for this module in V1 — flag this as a deliberate deviation from the default module skeleton (empty `infrastructure/` is fine; do not fill it just to match the folder template).

- `src/afrinograph/modules/source_contract/domain/` — `capabilities.py`, `errors.py`, `items.py` (the `RawSourceItem` DTO — it's a domain concept: "what a source actually gave us," independent of any transport format).
- `src/afrinograph/modules/source_contract/application/` — `contracts.py` (`CollectionRequest`, `CollectionResult`), `ports.py` (`SourceAdapter` Protocol).
- No `infrastructure/` content in this module for V1.

Dependency rule: this module imports only `shared/` and the standard library. It is never allowed to import from `modules/source_registry`, `modules/raw_evidence`, or any other module — it sits below all of them.

## 4. Public contracts

Two design decisions apply across everything below, made within engineering authority and stated explicitly here since the Module 2 handoff asks for the reasoning, not just the choice:

- **`Protocol` over an abstract base class** for `SourceAdapter` (§4.7): a `Protocol` lets `FakeSourceAdapter` (Chunk 3) and every future concrete adapter satisfy the interface structurally, without inheriting from a class defined in this module — adapters stay decoupled from this module at the class-hierarchy level, constrained only at the method-signature level. An ABC would force every adapter, including test doubles, into an explicit inheritance relationship this contract doesn't need to enforce.
- **Plain, frozen `dataclasses` over Pydantic** for every DTO here: these DTOs live in the `domain`/`application` layers, which must not depend on infrastructure or framework libraries (§3's dependency rule). FastAPI's use of Pydantic elsewhere in the project is a `shared.infrastructure`/HTTP-boundary concern with no bearing on this module — pulling Pydantic in here would be exactly the "introduce it merely because FastAPI uses it elsewhere" case the Module 2 handoff warns against. Frozen dataclasses with explicit `__post_init__` validation give these contracts everything they need — explicit types, validation, immutability — without the added dependency.

### 4.1 `SourceCapability` (domain/capabilities.py)

```python
from enum import Enum, auto

class SourceCapability(Enum):
    INCREMENTAL_COLLECTION = auto()
    HISTORICAL_BACKFILL = auto()
    CURSOR_PAGINATION = auto()
    TIME_WINDOW_COLLECTION = auto()
    STABLE_ITEM_IDENTIFIERS = auto()
    UPDATE_DETECTION = auto()
    DELETION_DETECTION = auto()
    RATE_LIMIT_METADATA = auto()
```

Rule: an adapter's `capabilities()` return value is authoritative. The orchestrator (a later module) must check it before requesting behavior a source doesn't support (e.g., must not send a `checkpoint` to a source lacking `CURSOR_PAGINATION`). This module only defines the vocabulary and enforces nothing by itself — enforcement is the orchestrator's job.

### 4.2 `CollectionMode` (application/contracts.py)

```python
from enum import Enum, auto

class CollectionMode(Enum):
    FULL = auto()
    INCREMENTAL = auto()
    BACKFILL = auto()
```

### 4.3 `CollectionRequest` (application/contracts.py)

Frozen dataclass. Fields:

| Field | Type | Required | Notes |
|---|---|---|---|
| `source_id` | `str` | yes | Opaque identifier assigned by Source Registry (later module); this module treats it as an opaque string, never validates its format |
| `mode` | `CollectionMode` | yes | |
| `window_start` | `datetime \| None` | no | UTC only; required by convention when `mode == INCREMENTAL` or `TIME_WINDOW_COLLECTION` is used, but **not enforced here** — enforcement is the orchestrator's responsibility, since this module can't see the adapter's declared capabilities at construction time |
| `window_end` | `datetime \| None` | no | UTC only |
| `checkpoint` | `str \| None` | no | Opaque continuation token; this module never parses it |
| `max_items` | `int \| None` | no | Must be `> 0` if provided — **this module does validate this**, since it's a self-contained invariant, not a cross-module one |

Validation performed in `__post_init__`: raise `ValueError` if `max_items is not None and max_items <= 0`. Raise `ValueError` if any provided datetime is not timezone-aware UTC.

### 4.4 `RawSourceItem` (domain/items.py)

Frozen dataclass. Fields:

| Field | Type | Required | Notes |
|---|---|---|---|
| `source_item_id` | `str \| None` | no | Missing means the source genuinely has no stable ID — this is not the same as an empty string, which is invalid and rejected |
| `source_item_type` | `str` | **yes** | e.g. `"post"`, `"comment"`, `"article"`, `"indicator"` — free-text but non-empty; this module does not maintain a closed enum of types, since that list is provider-driven and would force this contract to change every time a new provider is added |
| `title` | `str \| None` | no | `None` means the provider didn't supply a title (unknown/not applicable). An explicit empty string (`""`) is a distinct, valid state — the provider supplied the item with a confirmed-blank title. This DTO never collapses the two |
| `content_text` | `str \| None` | no | The item's textual content or summary, where the provider separates it from the full raw payload. Same `None`-vs-`""` distinction as `title` |
| `original_url` | `str \| None` | no | |
| `raw_payload` | `str \| bytes` | **yes** | The retained original representation, subject to Part 5.2's permission constraints (enforced by the adapter/registry, not by this DTO) |
| `provider_metadata` | `Mapping[str, Any]` | yes, may be empty | Structured, provider-specific; this module treats its contents as opaque but enforces two things about the container itself: it is converted to an immutable `types.MappingProxyType` in `__post_init__`, so mutating it after construction raises `TypeError` rather than silently changing data that already crossed the adapter boundary; and it must be JSON-serializable as a whole — `__post_init__` performs a `json.dumps()` round-trip and raises `ValueError` naming the failure if it isn't, rather than silently discarding an unsupported value |
| `source_published_at` | `datetime \| None` | no | Distinct from "unknown" (`None`) vs any real value — never defaulted to a sentinel time |
| `retrieved_at` | `datetime` | **yes** | Set by the adapter using the injected `Clock` port, never `datetime.now()` directly — this is what makes adapter tests deterministic |

Validation: `source_item_type` and `raw_payload` must be non-empty; `source_item_id`, if provided, must be non-empty (use `None`, never `""`, to mean "no ID"). `title` and `content_text` have no such restriction — an empty string is a valid, meaningful value for both, distinct from `None`. `provider_metadata` must be JSON-serializable as a whole and is stored read-only.

### 4.5 `CollectionResult` (application/contracts.py)

Frozen dataclass. Fields:

| Field | Type | Required |
|---|---|---|
| `items` | `list[RawSourceItem]` | yes, may be empty |
| `next_checkpoint` | `str \| None` | no |
| `has_more` | `bool` | yes |
| `warnings` | `list[str]` | yes, may be empty |

Rule: `has_more = True` with `next_checkpoint = None` is invalid and raises `ValueError` in `__post_init__` — the orchestrator would have no way to resume.

### 4.6 Error hierarchy (domain/errors.py)

```python
class AdapterError(Exception):
    """Base for all source-adapter errors. Carries whether a retry is safe."""
    def __init__(self, message: str, *, retryable: bool):
        super().__init__(message)
        self.retryable = retryable

class SourceUnavailableError(AdapterError): ...      # network/outage — retryable=True by default
class AuthenticationError(AdapterError): ...          # retryable=False by default
class RateLimitedError(AdapterError):                 # retryable=True; carries retry_after
    def __init__(self, message: str, *, retry_after_seconds: float | None = None):
        super().__init__(message, retryable=True)
        self.retry_after_seconds = retry_after_seconds

class InvalidConfigurationError(AdapterError): ...    # retryable=False
class MalformedResponseError(AdapterError): ...       # retryable=False by default — a bad payload usually won't fix itself on retry

class InvalidCheckpointError(AdapterError):           # retryable=False — retrying with the same bad checkpoint won't help
    def __init__(self, message: str):
        super().__init__(message, retryable=False)
```

Every subtype sets a sensible default for `retryable` but allows the adapter to override it per Part 13.1's error taxonomy. This module defines the taxonomy; it does not catch or translate exceptions — that's the orchestrator's job (Module E) when it calls an adapter.

An adapter raises `InvalidCheckpointError` when a supplied `checkpoint` can't be interpreted or resumed from — see §4.8 for the full checkpoint contract. A genuinely unanticipated failure (one matching none of the subtypes above) must still not escape `collect()` as a raw, untyped exception: the adapter catches it and re-raises as `AdapterError(str(original), retryable=False)` using `raise ... from original` to preserve the traceback, so the orchestrator only ever has to handle one exception family at this boundary (Part 13.1). "Permanent provider rejection" (e.g., a revoked API key with no recovery path) and "invalid request"/"unsupported operation" (e.g., a capability the adapter doesn't declare) deliberately get no dedicated subtype — `AuthenticationError` and `InvalidConfigurationError` with the appropriate `retryable` value already cover them, and the Module 2 handoff itself asks that "the final taxonomy must be proportionate to the MVP."

### 4.7 `SourceAdapter` (application/ports.py)

```python
from typing import Protocol

class SourceAdapter(Protocol):
    def capabilities(self) -> frozenset[SourceCapability]: ...
    async def collect(self, request: CollectionRequest) -> CollectionResult: ...
```

`collect` is `async`. **Decision made within engineering authority** (flagged, not blocking): adapters are I/O-bound by nature (HTTP calls to external providers), and the orchestrator will eventually want to collect from multiple sources concurrently — an async contract now avoids a breaking signature change later. If you'd rather start sync and add an async variant when concurrency is actually needed, say so and this is a one-file change at this stage. This is also "consistent with the project's execution model" as the Module 2 handoff asks: the app factory, the database engine, and every other foundation piece are already async.

### 4.8 Checkpoint semantics

A checkpoint is a provider-independent, opaque `str` representing collection continuation state — this module carries it but never interprets it.

- **Representation:** absence is `None` (no continuation state — collection hasn't started, or the source doesn't support resumption at all); presence is any non-empty `str`.
- **Who produces/manages it:** an adapter *produces* `next_checkpoint` in `CollectionResult`; the orchestration layer (a later module) *persists* it and *re-supplies* it as `checkpoint` on the next `CollectionRequest`. This module's DTOs are a carrier only — they never persist a checkpoint themselves.
- **Serializability:** guaranteed — it's already a plain `str`, safe to store as text in a future collection-run record.
- **Log safety:** not guaranteed. A checkpoint is adapter-defined and may, for some providers, encode more than a bare counter (e.g., a continuation URL with embedded parameters). Treat it as **not safe to log at INFO level or above**; if visibility is needed for debugging, log only a truncated form (e.g., first 8 characters plus length), never the full value, outside of explicitly-enabled DEBUG diagnostics.
- **Version/adapter ties:** a checkpoint is only meaningful paired with the exact `source_id` and adapter implementation that produced it. This module doesn't version-stamp the string itself (disproportionate for MVP); persisting one must always be paired with the source's registered adapter identity so a later module can detect an adapter swap and discard a stale checkpoint instead of passing it through. That pairing is Orchestration's responsibility, not this module's.
- **Invalid/incompatible checkpoints:** an adapter that receives a `checkpoint` it cannot interpret raises `InvalidCheckpointError` (§4.6) — it never silently ignores the checkpoint and restarts, and never raises a generic `AdapterError` for this specific, nameable case.

### 4.9 Contract versioning policy

These DTOs are internal interfaces used by every future adapter and by Normalization downstream, so changes need discipline proportional to an internal modular monolith — not a distributed-service versioning scheme.

- **Backward-compatible, no coordination needed:** adding a new optional field with a safe default; adding a new `SourceCapability` or `AdapterError` subtype.
- **Breaking, requires a deliberate, reviewed change across every consumer in the same commit:** removing or renaming a required field; changing a field's type; changing an existing error type's default `retryable` semantics; changing what `None` vs. an empty value means for any field.
- Every breaking change is recorded in `AI_state/DECISIONS.md` and a short changelog note in `docs/modules/source_contract.md` — never made silently.
- No contract version number is embedded in the DTOs themselves for V1; Python's own import system is the compatibility boundary. A structured version tag is a documented future option if this module ever needs two contract versions to coexist — it doesn't yet.

## 5. Persistence

None. No migration, no table, no repository in this module. If a chunk below appears to need one, stop and flag it — that would mean scope has drifted into Source Registry or Raw Evidence.

## 6. Configuration and security

No configuration keys, no secrets. Credentials belong to Source Registry (config resolution) and to each concrete adapter (using the resolved credential to authenticate) — never to this contract layer.

## 7. Gemini implementation chunks

### Chunk 1 — Module skeleton, capability enum, error hierarchy

**Objective:** `source_contract` module exists with the exact folder layout in §3; `SourceCapability` and the full `AdapterError` hierarchy exist and are unit-tested.

**Preconditions:** Foundation phase complete (`shared/domain/errors.py` exists and defines the base exception this module's errors may — or per §4.6, need not — inherit from; confirm by reading that file, do not assume its contents).

**Architectural context:** Pure domain layer. No imports beyond the standard library and, if applicable, `shared.domain.errors`.

**Files to create:**
- `src/afrinograph/modules/source_contract/__init__.py`
- `src/afrinograph/modules/source_contract/domain/__init__.py`
- `src/afrinograph/modules/source_contract/domain/capabilities.py`
- `src/afrinograph/modules/source_contract/domain/errors.py`
- `src/afrinograph/modules/source_contract/application/__init__.py`
- `tests/unit/source_contract/__init__.py`
- `tests/unit/source_contract/test_errors.py`
- `tests/unit/source_contract/test_capabilities.py`

**Files not to modify:** anything under `shared/`, anything outside `modules/source_contract/` and its tests.

**Implementation instructions:**
1. Implement `SourceCapability` exactly as in §4.1.
2. Implement `AdapterError` and its five subtypes exactly as in §4.6, including the `retryable` default per type and `RateLimitedError.retry_after_seconds`.
3. Do not add any capability or error type not listed here without flagging it first.

**Business rules:** `retryable` is a required, explicit concept on every error instance — never inferred by the caller from the exception's class name alone.

**Dependencies:** standard library only, plus `shared.domain.errors` if the foundation established a base exception to inherit from.

**Tests:**
- `test_capabilities.py`: every enum member is distinct; the set is exactly the eight named in §4.1 (a test that fails loudly if someone silently adds/removes one).
- `test_errors.py`: each subtype's default `retryable` matches §4.6; `RateLimitedError` stores `retry_after_seconds` correctly and defaults it to `None`; each subtype is an instance of `AdapterError`.

**Acceptance criteria:** `pytest -m unit tests/unit/source_contract/ -v` passes with the tests above and no others skipped.

**Completion report:** files created, exact commands run, pass count, anything deviated from this spec and why.

---

### Chunk 2 — DTOs: `RawSourceItem`, `CollectionRequest`, `CollectionResult`

**Objective:** all three DTOs from §4.3–4.5 exist, frozen, validated, and unit-tested including their invalid-input rejection paths.

**Preconditions:** Chunk 1 complete and its tests passing.

**Files to create:**
- `src/afrinograph/modules/source_contract/domain/items.py` (`RawSourceItem`)
- `src/afrinograph/modules/source_contract/application/contracts.py` (`CollectionMode`, `CollectionRequest`, `CollectionResult`)
- `tests/unit/source_contract/test_items.py`
- `tests/unit/source_contract/test_contracts.py`

**Implementation instructions:**
1. Implement `RawSourceItem` per §4.4, `@dataclass(frozen=True)`, with `__post_init__` validation as specified.
2. Implement `CollectionMode`, `CollectionRequest`, `CollectionResult` per §4.2–4.3 and §4.5, same validation discipline.
3. Use `from __future__ import annotations` and precise type hints throughout; run `mypy` on the module (warn-only per foundation config — report any warnings, don't silently ignore them).

**Business rules (must be tested, not just implemented):**
- `RawSourceItem(source_item_type="", raw_payload="x", ...)` raises `ValueError`.
- `RawSourceItem(source_item_id="", ...)` raises `ValueError` (empty string is invalid; `None` is the valid "no ID" sentinel).
- `CollectionRequest(max_items=0, ...)` and `max_items=-1` both raise `ValueError`; `max_items=None` and any positive int are valid.
- `CollectionRequest` with a naive (non-UTC-aware) `window_start` raises `ValueError`.
- `CollectionResult(has_more=True, next_checkpoint=None, ...)` raises `ValueError`.
- `CollectionResult(has_more=False, next_checkpoint=None, items=[], warnings=[])` is valid (the legitimate "nothing more, nothing found" case).

**Dependencies:** standard library (`dataclasses`, `datetime`, `typing`) only.

**Tests:** one positive-construction test and one test per business rule above, at minimum — no rule from this list may ship untested.

**Acceptance criteria:** `pytest -m unit tests/unit/source_contract/ -v` — all of Chunk 1 and Chunk 2 tests pass together.

**Completion report:** same format as Chunk 1.

---

### Chunk 3 — `SourceAdapter` protocol + `FakeSourceAdapter` test double

**Objective:** the `SourceAdapter` Protocol exists; a fully compliant in-memory `FakeSourceAdapter` exists under `tests/` (not `src/` — it is test infrastructure, not shipped product code) and is usable by later chunks and later modules' tests.

**Preconditions:** Chunks 1–2 complete.

**Files to create:**
- `src/afrinograph/modules/source_contract/application/ports.py` (`SourceAdapter` Protocol, per §4.7)
- `tests/fakes/__init__.py`
- `tests/fakes/fake_source_adapter.py` (`FakeSourceAdapter` — constructor takes a pre-programmed list of `RawSourceItem` batches and an injected `Clock`; `collect()` returns them in order, respecting `max_items` and returning `has_more`/`next_checkpoint` correctly across calls)
- `tests/unit/source_contract/test_fake_adapter_shape.py`

**Implementation instructions:**
1. `SourceAdapter` as an exact `Protocol` per §4.7 — no default methods, no base class implementation logic living here.
2. `FakeSourceAdapter` must genuinely exercise pagination: given 3 pre-programmed batches, three sequential `collect()` calls (each passing the prior result's `next_checkpoint`) must return them in order with correct `has_more` flags, and a 4th call past the end must return an empty, `has_more=False` result — this is what makes it useful as a stand-in for a real paginated provider in later modules' tests.
3. `FakeSourceAdapter` takes the `Clock` port from `shared.application.ports` (not a hardcoded `datetime.now()`), so tests can assert exact `retrieved_at` values.

**Business rules:** `FakeSourceAdapter` must be a structurally valid `SourceAdapter` (verified by `isinstance(fake, SourceAdapter)` if using `@runtime_checkable`, or by a `mypy`/structural test otherwise — confirm which mechanism `Protocol` supports in the pinned Python/typing version before choosing).

**Dependencies:** `shared.application.ports.Clock`; nothing from any other module.

**Tests:** pagination sequence as described; empty-programmed-adapter returns empty `has_more=False` immediately; `capabilities()` returns exactly what the test constructed it with.

**Acceptance criteria:** all prior tests plus this chunk's pass; `FakeSourceAdapter` is confirmed usable without any real network dependency (no `httpx`/`aiohttp` import in this file).

**Completion report:** standard format, plus explicit note of which structural-typing check was used for the Protocol conformance test.

---

### Chunk 4 — Reusable adapter contract test suite

**Objective:** a parameterizable pytest suite exists that *any future concrete adapter* (RSS, Reddit, etc.) can import and run against itself to prove contract conformance, per Part 9.5.

**Preconditions:** Chunk 3 complete.

**Files to create:**
- `tests/contract/source_adapter_contract.py` — exposes a function like `run_adapter_contract_tests(adapter_factory: Callable[[], SourceAdapter])` or an equivalent pytest fixture-based pattern (choose one, document the choice, and use it consistently — flag if you find a materially better pattern than a factory callable, but don't silently invent a different testing convention than what future adapter specs will assume).
- `tests/contract/test_fake_adapter_conforms.py` — the first user of that suite, run against `FakeSourceAdapter`, proving the suite itself works before any real adapter exists.

**Implementation instructions:** the shared suite must check, at minimum, everything Part 9.5 lists that's testable without a real provider:
- empty result is representable (`has_more=False`, `items=[]`);
- multiple items round-trip correctly;
- missing optional fields (`source_item_id=None`, `source_published_at=None`) are accepted, not coerced to sentinels;
- `capabilities()` returns a `frozenset[SourceCapability]` (not a list, not a plain set);
- a malformed `CollectionRequest` (e.g., a request the adapter's declared capabilities can't satisfy) — the adapter must raise `InvalidConfigurationError`, not silently return an empty result (this directly enforces Part 7.3: "do not silently convert failed collection into a successful empty result").

**Business rules:** this suite is the template every future adapter's own tests will import — it must not reference `FakeSourceAdapter` or anything else specific to this module's test double; it must be provider-agnostic by construction.

**Dependencies:** `pytest`, this module's public contracts. No provider SDKs — this file must remain importable with zero network-capable dependencies installed.

**Tests:** this chunk's own deliverable *is* a test suite; its acceptance criterion is that `test_fake_adapter_conforms.py` passes when run against `FakeSourceAdapter`.

**Acceptance criteria:** `pytest -m contract tests/contract/ -v` passes.

**Completion report:** standard format, plus an explicit statement confirming the suite has zero provider-specific imports (grep for `reddit`, `feedparser`, `requests`, `httpx` etc. and report the result).

---

### Chunk 5 — Documentation and AI-state update

**Objective:** module documentation exists at `docs/modules/source_contract.md`; `AI_state/` reflects that this module is complete.

**Preconditions:** Chunks 1–4 complete, all tests passing.

**Files to create/modify:**
- `docs/modules/source_contract.md` — copy this specification's §1–6 (purpose, responsibilities, architecture, contracts, persistence, config/security), plus a "Status: Implemented" header and the actual final file paths (confirm they match §3/§7 exactly; note any approved deviation).
- `AI_state/PROGRESS.md` — add a row: `source_contract | Phase 2 | Complete | <date>`.
- `AI_state/COMPLETED_WORK.md` — append a summary entry.
- `AI_state/ARCHITECTURE_STATE.md` — note that the source-contract boundary is now real and testable.
- `AI_state/TEST_STATE.md` — record total test count added by this module and the commands to reproduce them.
- `AI_state/SESSION_HANDOFF.md` — exact next step: begin Source Registry module (blocked on §9 of the foundation doc being confirmed, if it hasn't been yet).

**Acceptance criteria:** documentation and state files reflect only what chunks 1–4 actually produced — no forward-looking claims about Source Registry or any other module.

**Completion report:** confirmation that every file listed above was updated, and a final full-suite run: `pytest -m "unit or contract or architecture" tests/ -v`, with pass count.

### Chunk 6 — Module 2 reconciliation: title/content fields, metadata safety, checkpoint error, architecture scanner scope

Added via the Module 2 (Source Contracts & DTOs) reconciliation — see `AFRINOGRAPH_MODULE_2_SOURCE_CONTRACTS_RECONCILIATION.md` for why. This chunk amends what Chunks 1–2 already built; it is not a request to redo them.

**Objective:** `RawSourceItem` carries `title` and `content_text`; `provider_metadata` is immutable and JSON-validated; `InvalidCheckpointError` exists; unexpected adapter exceptions are wrapped before crossing the `collect()` boundary; the shared architecture scanner checks `application/` as well as `domain/` for forbidden imports.

**Preconditions:** Chunks 1–5 complete.

**Files to modify:**
- `src/afrinograph/modules/source_contract/domain/items.py` (`RawSourceItem`)
- `src/afrinograph/modules/source_contract/domain/errors.py` (`InvalidCheckpointError`)
- `tests/fakes/fake_source_adapter.py` — only if it hardcodes a `RawSourceItem` shape that needs updating; read it first, most likely no change is needed since the new fields are optional
- `tests/architecture/test_module_boundaries.py` — **this file belongs to the Foundation, not this module.** Read it first, then widen its scope from scanning only `domain/` to also scanning `application/` for the same forbidden imports. Do not touch anything else in this file.

**Files not to modify:** `application/contracts.py`, `application/ports.py` — neither is affected by this chunk.

**Implementation instructions:**
1. You read the current contents of every file above before changing anything — this chunk amends existing code, it does not start from a blank file.
2. You add `title: str | None = None` and `content_text: str | None = None` to `RawSourceItem` per the updated §4.4 table. You do not add non-emptiness validation for either — an explicit empty string is a valid, distinct state from `None`.
3. You change `provider_metadata`'s declared type to `Mapping[str, Any]` and, in `__post_init__`, wrap the constructor argument in `types.MappingProxyType` before assignment (via `object.__setattr__`, since the dataclass is frozen) and verify it's JSON-serializable with `json.dumps()`, raising `ValueError` naming the failure if it isn't.
4. You add `InvalidCheckpointError` to `domain/errors.py` exactly as in the updated §4.6 code block.
5. In `tests/fakes/fake_source_adapter.py`, you wrap any exception `collect()` doesn't already recognize as an `AdapterError` subtype in a base `AdapterError(str(e), retryable=False)` using `raise ... from e` — this is the pattern every real adapter will need later, and the fake should model it correctly for the contract suite to exercise.
6. You widen `tests/architecture/test_module_boundaries.py` to scan `application/` directories the same way it already scans `domain/` directories, for every module, not just this one.

**Business rules:**
- `provider_metadata['x'] = 'y'` on a constructed `RawSourceItem` must raise `TypeError`.
- `RawSourceItem(..., provider_metadata={"bad": object()})` must raise `ValueError`.
- `title=""` and `content_text=""` must both construct successfully and remain distinguishable from `title=None`.

**Dependencies:** standard library only (`types.MappingProxyType`, `json`).

**Tests:**
- `title`/`content_text` set, unset, and explicitly empty — all three states round-trip correctly.
- Mutating `provider_metadata` post-construction raises `TypeError`.
- A non-JSON-serializable `provider_metadata` value raises `ValueError`.
- `InvalidCheckpointError` is an instance of `AdapterError`, `retryable is False`.
- A fixture-only module under `application/` with a forbidden import is flagged by the widened scanner (mirrors the existing `domain/` self-test from the foundation's Chunk 5).

**Acceptance criteria:** `pytest -m "unit or contract or architecture" tests/ -v` passes, including every test above.

**Completion report:** standard format, plus explicit confirmation that `tests/architecture/test_module_boundaries.py` was the only file touched outside `modules/source_contract/`.

---

## 8. Manual testing instructions

Since this module has no database and no HTTP surface, manual verification is code-level:

1. **Preconditions:** Chunks 1–4 implemented.
2. **Configuration required:** none.
3. **Command:** `pytest -m "unit or contract" tests/unit/source_contract tests/contract -v`
4. **Action:** run the command above.
5. **Expected result:** every test listed in §7's chunks passes; no skips.
6. **Verify:** open `tests/contract/test_fake_adapter_conforms.py` and confirm by reading it that it genuinely exercises `FakeSourceAdapter` through the shared contract suite, not a hand-rolled duplicate set of assertions.
7. **Expected failure behavior:** a failing test here means either a DTO validation rule was implemented incorrectly or the Protocol/fake adapter pairing is structurally wrong — both are foundation-breaking for every later module, so do not proceed to Source Registry until this suite is green.
8. **Cleanup:** none required (no external resources touched).

## 9. Extension points

- **Adding a new capability:** add a member to `SourceCapability` (§4.1); no other file in this module needs to change; the orchestrator (later module) decides what to do with it.
- **Adding a new adapter error type:** subclass `AdapterError`, set a sensible `retryable` default, add a unit test asserting that default — do not reuse an existing type for a genuinely new failure mode, since the orchestrator's retry logic will key off the type.
- **Adding a new source adapter (RSS, Reddit, etc.):** implement `SourceAdapter` in that adapter's own module, import `tests/contract/source_adapter_contract.py`'s suite, run it against the new adapter. This module does not change when a new adapter is added — that is its entire reason for existing.

## 10. Known limitations and open decisions

- `collect()` is `async` — flagged in §4.7 as a decision made within my engineering authority; cheap to revisit now, expensive after Orchestration is built on top of it.
- The contract suite (Chunk 4) checks what's testable without a real provider. Adapter-specific concerns (real rate-limit headers, real pagination cursor formats) are necessarily deferred to each adapter's own tests.
- This spec assumes Python's `typing.Protocol` structural-typing check is sufficient for conformance testing; Chunk 3 must confirm the exact mechanism against the pinned Python version and report it, not assume it silently works.

## 11. Completion and handoff

This module is done when every item in `AI_instructions/11_DEFINITION_OF_DONE.md` is satisfied or explicitly recorded as outstanding, and specifically:

- [ ] All 6 chunks complete, all tests passing, reported per §7's format.
- [ ] `docs/modules/source_contract.md` exists and matches the implemented code.
- [ ] `AI_state/` fully updated per Chunk 5.
- [ ] No provider-specific code exists anywhere in this module.
- [ ] `FakeSourceAdapter` and the contract suite are confirmed reusable by a next module's tests (Source Registry's spec will reference them directly).
- [ ] Next module (Source Registry) is not started until this checklist is confirmed complete by the project owner.
