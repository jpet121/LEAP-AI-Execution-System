# Synthetic Reimbursement Claim Audit

**Scope:** 12 fictional claims evaluated in contract source order; classifications only; no money moved.

**Analytical outcome: DETERMINED from the compiled contract records.** This does not independently validate the original compiler source event S2.

## 1. Row-by-row decisions

| Row | Claim | Unit | Requested | Decision | Approved | Controlling reason |
|---:|---|---|---:|---|---:|---|
| 01 | A01 | Alpha | $99.95 | APPROVED | $99.95 | Fits cap; valid first occurrence and receipt |
| 02 | A02 | Alpha | $75.05 | APPROVED | $75.05 | Fits cap; valid first occurrence and receipt |
| 03 | A03 | Alpha | $0.01 | REJECTED | $0.00 | EXCEEDS_UNIT_CAP |
| 04 | B01 | Bravo | $176.00 | REJECTED | $0.00 | EXCEEDS_UNIT_CAP |
| 05 | B02 | Bravo | $120.00 | APPROVED | $120.00 | Fits cap; valid first occurrence and receipt |
| 06 | H01 | Headquarters | $100.00 | APPROVED | $100.00 | Fits cap; valid first occurrence and receipt |
| 07 | H02 | Headquarters | $5.00 | REJECTED | $0.00 | EXCEEDS_UNIT_CAP |
| 08 | C01 | Charlie | $70.00 | REJECTED | $0.00 | MISSING_RECEIPT |
| 09 | C02 | Charlie | $45.25 | APPROVED | $45.25 | Fits cap; valid first occurrence and receipt |
| 10 | C03 | Charlie | $50.00 | APPROVED | $50.00 | Fits cap; valid first occurrence and receipt |
| 11 | C04 | Charlie | $79.75 | APPROVED | $79.75 | Fits cap; valid first occurrence and receipt |
| 12 | A01 | Alpha | $20.00 | REJECTED | $0.00 | DUPLICATE_CLAIM |

## 2. Per-unit reconciliation

| Unit | Cap | Approved total | Rejected rows | Unused balance |
|---|---:|---:|---:|---:|
| Alpha | $175.00 | $175.00 | 2 | $0.00 |
| Bravo | $175.00 | $120.00 | 1 | $55.00 |
| Charlie | $175.00 | $175.00 | 1 | $0.00 |
| Headquarters | $100.00 | $100.00 | 1 | $0.00 |

## 3. Batch reconciliation

| Metric | Value |
|---|---:|
| Processed rows | 12 |
| Approved rows | 7 |
| Rejected rows | 5 |
| Approved grand total | $570.00 |

## 4. Rejection explanations and non-disbursement

- Row 03 (A03, Alpha): **EXCEEDS_UNIT_CAP** — Full claim would exceed the unit’s remaining cap; partial approvals are prohibited.
- Row 04 (B01, Bravo): **EXCEEDS_UNIT_CAP** — Full claim would exceed the unit’s remaining cap; partial approvals are prohibited.
- Row 07 (H02, Headquarters): **EXCEEDS_UNIT_CAP** — Full claim would exceed the unit’s remaining cap; partial approvals are prohibited.
- Row 08 (C01, Charlie): **MISSING_RECEIPT** — Receipt is NO, whereas YES is required.
- Row 12 (A01, Alpha): **DUPLICATE_CLAIM** — Repeated claim ID already encountered in an earlier source row; duplicate precedence controls.

No funds disbursed; no checks issued, accounting writes, external communications, external research or system modifications performed. All approvals are audit classifications, not payments.

**Source provenance limitation:** Original Compiler input S2 is not separately attached; values, original source anchors and policy were read from the uploaded immutable compiled contract and were not independently corroborated against S2.
