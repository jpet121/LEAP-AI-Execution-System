# Case 4 — Synthetic USD Transaction Reconciliation API

**Portfolio implementation, not an operational banking or payment service.**

[Browse the implementation](reconciliation-api/) · [Case 4 project README](reconciliation-api/README.md) · [Assurance report](reconciliation-api/evidence/RELEASE_READINESS.md)

This is the separately scoped Case 4 following three Prompt Forge Compiler/Runner business-rule acceptance cases. The application implements FastAPI, strict Pydantic v2 validation, exact USD decimal handling, authenticated endpoints, PostgreSQL transaction locking and composite-key idempotency, and deterministic rejection/rollback behavior. Includes migrations, Docker/Compose, unit tests, frozen HTTP acceptance tests, adversarial tests, and a PostgreSQL-backed GitHub Actions workflow.

**Evidence boundary:** the submitted implementation's earlier clean replay reported 100% first-party line/branch coverage, nine unit/integration tests, four frozen HTTP acceptance tests, seven advanced assurance tests and six mutation detections. Separate reviewer checks passed 12,493 pure arithmetic/validation cases and archive/source-integrity tests, but did not independently rerun live PostgreSQL or hosted GitHub Actions. Hosted CI should be reviewed on this repository before revising the release HOLD.

**Explicit hold:** no human deployment approval; no live financial system, payment processor, bank, or external production integration. Code publication is approved for portfolio review, **not** production release.

## Hosted GitHub Actions result (November 2, 2026)

[GitHub Actions run 41482364607](https://github.com/jpet121/LEAP-AI-Execution-System/actions/runs/41482364607) **PASS**, with both Python 3.12 and Python 3.13 PostgreSQL-backed jobs successful. This provides real hosted CI evidence in addition to the submitted local replay; it is not a substitute for an independent organizational audit or owner approval for deploying a real financial system.

The exact original [Case 4 complete delivery ZIP](releases/Case4_Complete_Delivery.zip) is included for provenance and offline audit (SHA-256 `85961522d6aef3393e58c53f76fe8c097383d61d682124b84b590295650b482b`). The first-party application remains browsable under `reconciliation-api/`; inspect that tree rather than relying solely on a binary archive. Do not run untrusted archive code without reviewing it.
