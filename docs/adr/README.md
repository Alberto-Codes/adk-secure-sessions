# Architecture Decision Records

This directory contains Architecture Decision Records (ADRs) for adk-secure-sessions.

ADRs document significant architectural decisions made during the project's development. Each record captures the context, decision, and consequences so that future contributors understand *why* things are the way they are.

## Index

| ADR | Title | Status | Date |
|-----|-------|--------|------|
| [ADR-000](ADR-000-strategy-decorator-architecture.md) | Strategy + Direct Implementation Architecture | Accepted | 2026-02-01 |
| [ADR-001](ADR-001-protocol-based-interfaces.md) | Protocol-Based Interfaces | Accepted | 2026-02-01 |
| [ADR-002](ADR-002-async-first.md) | Async-First Design | Accepted | 2026-02-01 |
| [ADR-003](ADR-003-field-level-encryption.md) | Field-Level Encryption by Default | Accepted | 2026-02-01 |
| [ADR-004](ADR-004-adk-schema-compatibility.md) | ADK Interface Compatibility Strategy | Accepted | 2026-02-01 |
| [ADR-005](ADR-005-exception-hierarchy.md) | Exception Hierarchy | Accepted | 2026-02-01 |

## Format

Each ADR follows this structure:

- **Status**: `Proposed` → `Accepted` → `Superseded` or `Deprecated`
- **Context**: The forces at play — what problem or constraint led to this decision
- **Decision**: What we chose and why
- **Consequences**: Trade-offs, what becomes easier, what becomes harder
- **Alternatives Considered**: What we didn't choose and why not

## Creating a New ADR

1. Copy the format from an existing ADR
2. Number sequentially: `ADR-NNN-short-title.md`
3. Set status to `Proposed` until reviewed
4. Update this README's index
