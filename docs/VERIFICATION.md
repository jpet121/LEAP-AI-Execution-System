# Verification — scopes and evidence

**Updated November 2, 2026.** Separate technical integrity, semantic fidelity, execution outcome and human authorization.

## Historical baseline (October 31, 2026)

The released Compiler and Runner 1.0.0 self-checks passed deterministic local smoke tests. Two older provided XML examples passed Runner structural preflight. That historical publication did **not** independently rerun full Compiler→Runner model reasoning. The original large offline runtime ZIP/parts are **not present in this Git tree** even though archive manifests survive. The release source mirrors are available for review, but a checkout does not reconstruct an offline deployment.

## Controlled improvement and independent frozen acceptance (November 2, 2026)

- **Phase 1 diagnostics:** the frozen historical negative controls identified global-exclusivity defects in Case 1 and Case 2, an incorrectly active future award dependency, and a provenance gap for Case 3. Initial diagnostic status did *not* constitute repair acceptance.
- **Repair candidate:** packaged role-prompt controls and fail-closed archive production. Deterministic candidate checks passed, but those checks alone do not establish semantic correctness.
- **Three fresh test cases:** new Compiler contracts were executed by the unchanged Runner. Business outputs matched their frozen independent oracle; case-by-case independent reviews examined contract/source mapping and exported Runner artifacts, including per-file SHA-256 ledgers.

| Case | Compiler contract SHA-256 | Business result | Accepted scope |
|---|---|---|---|
| 1 | `806591f09156807a2a2818ba23f7af9fd97a03f96b3be8b0243204339d7cdc91` | 7 approved / 5 rejected / $570 | Original rule fidelity and claim scope |
| 2 | `58037993f157e7419bfe583f9c0e9f11460778759be95acc9fd0d6865dfe5638` | ATLAS HOLD / BEACON FAIL / CEDAR PASS | Vendor-specific mixed statuses and future human gating |
| 3 | `f8a4fa3130af62a7a5ee9bb9eace0849498bd6b1daa9f986e4fafe971c51b282` | Business HOLD; $1,850 proposed | Imported source trust boundary, genuine approval absent, no final manifest |

Inspect the [original prompts, exact Runner ZIPs, receipts, final results and independent assessments](../evidence/cases-1-3/README.md). The [candidate source delta](../candidate/compiler-1.0.0-cases1-3/README.md) is separate from released source.

## Run checks

```bash
python tools/verify_cases_1_3.py
python -m unittest discover -s tests -v
```

`tools/verify_cases_1_3.py` verifies archive checksum, manifest-listed entries, frozen contract SHA, receipt identity and postflight fields. This checks **integrity**, not model comprehension. CI checks repository packaging, not live model-host ability.

## Not demonstrated

Complete stochastic/alternate-branch reliability, fully isolated model evaluators, formal proofs, independent separate-host replay of every run, new-account ChatGPT Project installation and permission grant, or explicit authorization to promote this candidate. Also, the original baseline source-identity caveats remain historical facts, even though the three case documents have subsequently been corroborated against frozen prompts/attachments within their individual reviews. **Case 4 is outside this evaluation.**

## November 2 final Compiler and Case 4 publication

The user authorized designating the **byte-identical Cases 1–3 repair runtime** as the final Compiler Project build, without changing its internal `1.0.0` version. The historical October baseline remains immutable under `compiler/source/`; the full first-party final source snapshot appears in `compiler/final-2026-11-02/source/`. Its original 26.3-MB offline ZIP and third-party wheelhouse are not published here. `python tools/verify_portfolio_publication.py` checks the final first-party source snapshot against the original package's SHA-256 values.

[Case 4](../case4/README.md) is **separate** from Cases 1–3. The submitted implementation reported locally passing PostgreSQL HTTP, mutation and coverage gates; an additional independent review verified source integrity and pure-data behavior but could not rerun live PostgreSQL or hosted CI. The repository now contains source, frozen acceptance tests and a PostgreSQL GitHub Actions workflow. Hosted runs must be checked directly and any failure reported; their presence alone does not establish PASS. Human release remains NOT_GRANTED and no real payments have been made.
