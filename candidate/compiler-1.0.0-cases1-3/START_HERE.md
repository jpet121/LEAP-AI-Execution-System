# Prompt Forge 1.0 — Cases 1–3 controlled repair candidate

**Status: CANDIDATE_ONLY — NOT PROMOTED.** The production Compiler, Runner, schema, archived historical business cases, original contract and receipts were not modified. No Case 4 material is included.

## Concrete changes
1. Improved `interpreter.txt`, `challenger.txt`, and `reconciler.txt` role prompts to explicitly reject per-subject GLOBAL status mutual exclusions, preserve mixed vendor/claim outcomes and separate present report work from future human-only approvals.
2. Added runtime `make_compiler_release.py` which calls Compiler replay, verifies all eight receipt-bound files, and refuses omitted files, extras, symlinks, changed hashes and overwrite before publishing one complete archive.
3. Added independent historical negative controls and illustrative *in-memory* corrected v1 IR structural probes for Cases 1 and 2; these pass both Compiler structural validation and Runner 1.0 bare-XML preflight. Case 3's original global **batch** branches are intentionally retained as valid, with lower-trust S2 observed at execution time.
4. Added `VERIFY/forward_gate.py` for screening **fresh released** candidate output packages; it cannot independently establish semantic correctness.

## How to use
`CANDIDATE_PROJECT/PROJECT_LOAD/02_RUNTIME.zip` is the complete candidate Compiler runtime, including pinned offline wheelhouse. The project instructions remain compatible with v1.0.0; this is **not** an authorized production release. The original Runner package remains unchanged. For a clean environment, verify the bundled HASHES and DEPLOYMENT_MANIFEST before extraction, bootstrap offline as instructed, and run role-host compilation. To independently screen outputs, run:

```
python VERIFY/forward_gate.py 1 new_case_1_compiler_release.zip
python VERIFY/forward_gate.py 2 new_case_2_compiler_release.zip
python VERIFY/forward_gate.py 3 new_case_3_compiler_release.zip
```

To reproduce candidate smoke checks AND 42 frozen historical diagnostic tests from the unchanged original Compiler and Runner archives, run `python VERIFY/run_tests.py` (requires Python with pinned runtime dependencies present, or use the included offline bootstrap). The original source archives are bundled under `VERIFY/ORIGINAL_ARCHIVES`; their 42/42 historical execution is a **diagnostic baseline**, not corrected-compiler acceptance.

## Still required before promotion
- Fresh semantic Interpreter → independent-source Challenger → Reconciler compilation for Cases 1–3 with verified source captures and provenance. Prompt changes are **not proven** to reliably correct the host-model's outputs until this is run.
- Dynamic new-output artifact completeness, Runner preflight and full legally authorized Runner task/evidence/challenge/export/verify cycles, including Case 3 actual S2 observe(). No simulated or forged approval.
- Separate-host / independent reviewer semantic audit and human release decision. Historical source identity is unresolved; never claim this candidate equals the historic build.
- Case 1 expected 7 approvals, 5 rejections, USD 570.00 approved; Case 2 mixed Atlas HOLD / Beacon FAIL / Cedar PASS without current award block; Case 3 baseline B-204 HOLD, USD 1,850.00 proposed, USD 150.00 unused, no manifest.

Only after all dynamic checks pass is there evidence for a promotion decision. This ZIP makes concrete fixes but **does not certify the model-level semantic defects as closed**.
