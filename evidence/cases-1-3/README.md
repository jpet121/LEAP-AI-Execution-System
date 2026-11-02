# Frozen Cases 1–3 — Compiler/Runner acceptance evidence

**Evaluation date:** November 2, 2026. **Scope:** synthetic business requests and the controlled Compiler repair candidate, executed by unchanged Runner 1.0.0. Case 4 is explicitly excluded.

| Case | Result | What the evidence establishes |
| --- | --- | --- |
| [Reimbursement](01-reimbursement/) | 7 approved; 5 rejected; $570 total | Independent per-claim decisions, duplicate/receipt/cap controls |
| [Vendor qualification](02-vendor-qualification/) | ATLAS HOLD, BEACON FAIL, CEDAR PASS | Per-vendor nonexclusive outcomes; future human award held separately |
| [Grant B-204](03-grant-release/) | Business HOLD, $1,850 proposed, $150 unused | Lower-trust source preserved; forged override refused; no final simulated manifest or payment |

Each directory contains **original business request**, frozen **contract.xml**, independent acceptance write-up, **run_receipt.json**, final **result.md**, and the exact originally exported `*RUN_RELEASED.zip` containing full Runner task receipts, evidence ledger, replay journal and hash ledger. The uploaded compiled XML is taken directly from each corresponding Runner export. `[INTEGRITY.json](INTEGRITY.json)` binds ZIP byte hashes to contract hashes.

`COMPILE_RELEASED` is a Compiler lifecycle status, `RUN_RELEASED` a Runner technical release, and `PASS/FAIL/HOLD` in a business report describes *business decision status*. An independent acceptance PASS means the reviewed frozen specification/expected result matched within its stated scope. These are three different levels of assurance.

Case 3's actual Runner analytical outcome is `USER_DECISION_REQUIRED` (external human dependency), while its business status is `HOLD`. No genuine approval was fabricated or exercised. Original source text is immutable data; untrusted instructions in the grant fixture are never authoritative.

**Reproduce local ZIP/receipt checks:** `python tools/verify_cases_1_3.py` from repository root. This does not re-run ChatGPT's model reasoning or create an independent model audit.
