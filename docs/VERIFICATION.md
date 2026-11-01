# Verification  -  observed results and unverified claims

**Review date:** October 31, 2026 (project portfolio build). 

## Executed here

| Action | Observed output | Scope |
| --- | --- | --- |
| `python run_compiler.py self-check` | `status: PASS`, `runner_required: false`, `semantic_model_tested: false` | Compiler deterministic smoke test with a stub model protocol. |
| `python run_runner.py self-check` | `status: PASS`, `runner_version: 1.0.0` | Runner deterministic smoke test. |
| Runner `preflight` on four-day XML | `status: PASS`; contract SHA-256 `0b3a9bcb800abc6c85901d072aff85a344bcc777e2944b99e51d2bf4b3495adc` | XML structural/identity checks. Source provenance asserted and receipt absent. |
| Runner `preflight` on payroll XML | `status: PASS`; contract SHA-256 `1e2f8a19b5dad1ef44bd6be54ccfafd504d4dac96ff50ff3d165c01637f6e292` | XML structural/identity checks. Source provenance asserted and receipt absent. |
| Archive and mirror construction | SHA-256 and equality checks in repo scripts | Checks bytes, not correctness of task semantics. |

Preflight diagnostics for both case contracts explicitly included:

> Source provenance asserted by Compiler; original source events not independently reproduced. Bare XML: no external Compiler receipt binding supplied.

## Not established by this work

- No full, fresh host-model `COMPILE -> RUN -> RUN_RELEASED` research replay was performed for these historical examples.
- The particular source claims in the October 2026 payroll and workweek reports have not been independently re-researched for this portfolio release.
- No 100% coverage, formal verification proof, mutation score, large fuzzing campaign, independent certification, ChatGPT UI install certification or production deployment approval has been demonstrated for **these specific supplied artifacts**.
- The source bundle's own `KNOWN_LIMITATIONS.md` and `COMPATIBILITY.md` describe broader recorded historical acceptance activities; this project did not independently reproduce those reports or treat narrative claims as test receipts.

## Reproducibility

The full original offline packages are preserved byte-for-byte via browser-uploadable segments. `tools/reassemble_runtime.py` verifies each part and the final restored archive. `tools/verify_repo.py` checks archive segment hashes, archived code mirrors, and provided example XML shapes/hashes. Project unit tests run against the repository packaging itself, not the host's subjective judgments.

A true independent assurance campaign would include original user requests, frozen compiler receipt and release artifacts, source observations, run receipt/ledger, full artifact checksums, test commands, independent corroboration of material source claims, and verified human release decision. None should be fabricated to improve portfolio appearance.
