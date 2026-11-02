# Prompt Forge Repair Candidate — Case 1 Independent Acceptance

## Verdict

**Case 1 semantic and business-output acceptance: PASS within inspected scope.**

**Production repair release: NOT AUTHORIZED.** Cases 2 and 3 and integrated candidate acceptance remain outstanding.

This is an independent inspection and deterministic calculation against the frozen original business request, not a separate-host Runner replay or independent validation of the model Challenger's actual reasoning.

## Frozen expected results vs submitted output

| Check | Frozen expected | Observed | Finding |
|---|---|---|---|
| Source rows | 12, ordered | 12, ordered | PASS |
| Approved rows | 01, 02, 05, 06, 09, 10, 11 | Exact match | PASS |
| Rejected rows | 03 cap; 04 cap; 07 cap; 08 receipt; 12 duplicate | Exact match | PASS |
| Approved count | 7 | 7 | PASS |
| Rejected count | 5 | 5 | PASS |
| Approved total | USD 570.00 | USD 570.00 | PASS |
| Per-unit totals | Alpha 175.00, Bravo 120.00, Charlie 175.00, HQ 100.00 | Exact match | PASS |
| Global exclusivity defect | Must not assert one exclusive outcome for all claims | Zero Branches in XML | PASS |
| Real payments | None authorized | Run report says none performed; no payment artifacts present | PASS within artifact-observable scope |

## Independent checks performed

- Parsed the uploaded Runner ZIP without executing application or source-file code.
- Checked 15 entries in `exported_run/HASHES.sha256`: no missing or hash-mismatched entries.
- Checked the run receipt's contract SHA-256 against the embedded `input_contract.xml`: match.
- Verified `run_receipt.json`: `RUN_RELEASED`, postflight `PASS`; deterministic replay declaration does **not** assert semantic truth.
- Located the corresponding Compiler receipt in the saved files: it reports `COMPILE_RELEASED` and contains the same contract SHA-256 (`806591f09156807a2a2818ba23f7af9fd97a03f96b3be8b0243204339d7cdc91`). This receipt is not enclosed in the uploaded Runner ZIP.
- Used the frozen original `01_COMPILER_Reimbursement_Audit.txt` and checked all 126 compiled S2 source anchors at Unicode character offsets: 126/126 content hashes match.
- Compared all 12 typed contract records and four unit caps with the original source: exact match.
- Recomputed all approvals, rejection priorities, running caps and unit/batch totals with Python `Decimal`, using the original source rather than the compiled calculation results: all 12 submitted decisions match.
- Checked the submitted standalone audit MD against the run's embedded `result.md`: identical bytes.
- Verified the contract has zero globally exclusive Branches, preserving row-level independent decisions.

## Technical status and limitations

- Runner reports all five tasks as `COMPLETED_WITH_LIMITATIONS`, specifically the original S2 source was not independently observed inside that Runner session. The separate audit here found an original frozen source whose substantive anchors match; that does not retroactively change what the Runner observed.
- Runner's Challenger verdict `PASS` is a shared-host review; it is not evidence of separately isolated model review.
- Run receipt declares deterministic replay with `semantic_truth_verified: false`.
- No independently executed `run_runner.py verify` was performed here. Zip integrity and business calculations were separately inspected as described above.
- A successful instance does not establish behavior across other inputs or all possible Compiler regressions. Cases 2 and 3 require fresh candidate tests.

## Inputs and identities

- Uploaded Runner ZIP SHA-256: `121d0ffe583ab28a94cd5ee23d7b392e133aa2098df406b10b75f3a7a7f41ef3`.
- Uploaded audit MD SHA-256: `9c755458104637dfc87fdaa05edb143e18be5f494be767891827e2888a31d05f`.
- Frozen source request SHA-256: `d0acde1688bca2a9db638a8e97476af818227871ab83c16b69c806c663ce78ca`.
- Embedded contract SHA-256: `806591f09156807a2a2818ba23f7af9fd97a03f96b3be8b0243204339d7cdc91`.

## Next gate

Advance to Case 2 using the same unmodified repair candidate Compiler and unchanged Runner. Test that ATLAS is HOLD, BEACON is FAIL, CEDAR is PASS, that CEDAR alone qualifies for recommendation, and that a future human-only award decision cannot block the present report. Preserve the original candidate and frozen oracle until all three cases pass independent acceptance.
