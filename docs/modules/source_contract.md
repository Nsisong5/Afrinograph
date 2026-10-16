# Afrinograph Module Specification — Source Contract & Adapter Interface

**Module ID:** `source_contract`
**Status:** Implemented
**Corresponds to:** Module 2: Source Contracts & DTOs
**Depends on:** Foundation phase only (`shared/domain/errors.py`, `shared/application/ports.py::Clock`)
**Depended on by:** Source Registry, Raw Evidence & Provenance, Collection Orchestration, Normalization & Identity, every future source adapter

---

## 1. Purpose

This module defines the **stable boundary** between Afrinograph's core and every external source. It is pure contract: interfaces, DTOs, an error taxonomy, and a capability vocabulary. It contains **no provider-specific code and no persistence**.

## 2. Responsibilities

**Owns:**
- The `SourceAdapter` interface every concrete adapter must implement.
- `CollectionRequest` / `CollectionResult` DTOs exchanged between the orchestrator and an adapter.
- `RawSourceItem` — the shape of one unprocessed item as an adapter hands it back.
- `SourceCapability` — the vocabulary for declaring what a given source can and can't do.
- The adapter-facing error hierarchy (`AdapterError` and subtypes).
- A reusable, parameterizable **contract test suite** any future adapter's tests can plug into.

## 3. Architecture context

Pure domain + application-layer `Protocol`. No infrastructure package is needed for this module in V1.

- `src/afrinograph/modules/source_contract/domain/` — `capabilities.py`, `errors.py`, `items.py`
- `src/afrinograph/modules/source_contract/application/` — `contracts.py`, `ports.py`

## 4. Public contracts

- `SourceCapability` (`domain/capabilities.py`)
- `CollectionMode`, `CollectionRequest`, `CollectionResult` (`application/contracts.py`)
- `RawSourceItem` (`domain/items.py`)
- `AdapterError` hierarchy (`domain/errors.py`)
- `SourceAdapter` Protocol (`application/ports.py`)

## 5. Persistence

None.

## 6. Configuration and security

No configuration keys, no secrets.
