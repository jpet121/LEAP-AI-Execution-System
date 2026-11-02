# Prompt Forge Compiler 1.0.0 — Cases 1–3 controlled repair candidate

**Status: ACCEPTED on the three frozen business-case baselines; NOT promoted to the released Compiler.** Existing Runner 1.0.0 unchanged. Case 4 excluded.

The repair candidate corrects historical semantic-representation failures by changing the packaged **Interpreter, Challenger and Reconciler role prompts**. It also adds a **fail-closed release packager** (`make_compiler_release.py`) to prevent publication of incomplete compiler artifact sets. The original Python Compiler engine, schema, semantic IR, Runner source and frozen historical artifacts are unchanged.

## Included files

- [`PROJECT_INSTRUCTIONS.txt`](PROJECT_INSTRUCTIONS.txt): candidate ChatGPT Compiler project setup text, from the candidate package.
- [`runtime_delta/lib/pfcompiler/prompts/`](runtime_delta/lib/pfcompiler/prompts/): three exact candidate role prompt files, not changes applied to `compiler/source/`.
- [`runtime_delta/make_compiler_release.py`](runtime_delta/make_compiler_release.py): candidate release packager.
- [`candidate_test_results.json`](candidate_test_results.json): structural candidate checks and acknowledged limitations.
- [`frozen_gate/`](frozen_gate/): frozen acceptance harness/readme and **evaluator-only** oracle data. Do not feed the oracle to the Compiler or Runner.

## Repairs by class

1. **Case 1 — independent claim decisions:** do not collapse 12 individual claim classifications into a globally exclusive PASS/FAIL/HOLD branch; preserve original order and full reconciliation.
2. **Case 2 — independent vendor statuses:** allow ATLAS HOLD, BEACON FAIL and CEDAR PASS simultaneously; a *future* award decision must not block the *current* evaluation/report.
3. **Case 3 — lower-trust source and future authorization:** preserve original imported records, reject embedded privilege claims and explicitly hold missing Director approval and destination verification.

## Evidence, limits, and safe use

The candidate ZIP used for tests had SHA-256 recorded in [integrity manifest](../../evidence/cases-1-3/INTEGRITY.json). The Git tree contains **inspectable source delta only**, not the full original 75.7-MB bundle. The three frozen Compiler→Runner runs and acceptance reviews are under [`evidence/cases-1-3/`](../../evidence/cases-1-3/). Do not replace the baseline Compiler `compiler/source/` or change the published Runner on the basis of these three examples alone.

Next acceptance gate: repeated model-driven compilation, alternate-state/adversarial cases, artifact/hash checks, external independent review, then explicit human release decision. **No production promotion is implied.**
