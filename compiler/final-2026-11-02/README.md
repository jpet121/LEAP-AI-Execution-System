# Prompt Forge Compiler — Final Build (2026-11-02)

**Owner-designated final Compiler build; internal runtime version: `1.0.0`.** This directory preserves an inspectable source mirror of the 2026-11-02 revised ZIP. It is a promotion of the tested Cases 1–3 repair candidate, not a claim that all possible inputs have been certified.

The `source/` directory contains the first-party Python runtime, schemas, revised Interpreter/Challenger/Reconciler prompts and fail-closed release packager. `00_PROJECT_INSTRUCTIONS_COMPILER.txt` contains the project instructions; the start and runtime guide files document host setup. The unchanged Runner remains v1.0.0.

**Source package integrity:** the owner-supplied `COMPILER REVISED 02NOV2026.zip` has SHA-256 `c263ed676539c22a44675cd4048dab590614e13ae1d82d9341a38c69d415acfb`. Its nested `02_RUNTIME (2).zip` has SHA-256 `e80e1e4c40e9c760030fc9b288fd09e579512a65acb65fd5c122ca3b0a21d2f0`, exactly matching the previously tested Cases 1–3 repair-candidate runtime archive. The nested runtime manifest verified all 39 declared members in the source inspection.

**Availability:** GitHub stores the inspectable first-party source and project instructions here, not the 26.3-MB bundled offline runtime ZIP or third-party wheelhouse. A repository checkout therefore cannot by itself recreate the full original offline-bundled installation. The authoritative ZIP is retained separately by the owner. Do not represent a repackaged source-only ZIP as byte-identical to the distributed runtime.

**Evidence:** [Cases 1–3](../../evidence/cases-1-3/README.md) passed frozen-case scoped acceptance, not open-ended stochastic reliability testing. No independent formal proof or production deployment is asserted. The owner explicitly approved using this as their final Compiler build on 2026-11-02.
