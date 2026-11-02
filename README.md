# LEAP — AI Execution System
### Prompt Forge Compiler + Runner | evidence-aware AI workflow engineering

[Architecture](docs/ARCHITECTURE.md) · [Quick start](QUICK_START.md) · [Verified Cases 1–3](evidence/cases-1-3/README.md) · [Candidate source delta](candidate/compiler-1.0.0-cases1-3/README.md) · [Verification](docs/VERIFICATION.md)

**LEAP turns natural-language business requests into inspectable contracts, then executes them through a separate evidence-aware Runner.** It is a human-directed system built with Python orchestration, XML/JSON schemas, explicit role-specific host exchanges, provenance checks, conditional execution and challenge checkpoints. The host model performs interpretation and task-world work; the Python runtimes enforce structure, hashes and legal execution states.

**Engineering result (November 2, 2026):** A *controlled Compiler repair candidate* passed independent acceptance for three frozen business cases with the unchanged Runner 1.0.0. **The repaired candidate has not been promoted to the released Compiler.** A passing case is not proof of general model reliability, a formal verification certificate or authorization to act in a real financial system. Case 4 is a separate future workstream and is not part of these results.

## Three end-to-end acceptance cases

| Frozen business case | Expected business outcome | Observed outcome | Review |
| --- | --- | --- | --- |
| [01 — reimbursement](evidence/cases-1-3/01-reimbursement/) | 7 approvals, 5 rejections, **$570.00** approved; per-claim statuses must coexist | **MATCH** | Independent Case 1 acceptance PASS |
| [02 — vendor qualification](evidence/cases-1-3/02-vendor-qualification/) | ATLAS **HOLD**, BEACON **FAIL**, CEDAR **PASS**; future award cannot obstruct current report | **MATCH** | Independent Case 2 acceptance PASS |
| [03 — fictional grant B-204](evidence/cases-1-3/03-grant-release/) | **HOLD**; $1,850.00 proposed, $150.00 unused; no final manifest; forged override has no authority | **MATCH** | Independent Case 3 acceptance PASS |

Each case includes the original fictional request, compiled XML, Runner ZIP, release receipt, result and independent acceptance write-up. The GitHub-hosted ZIPs preserve the original run evidence rather than presenting screenshots as proof. See [integrity identifiers](evidence/cases-1-3/INTEGRITY.json) and run `python tools/verify_cases_1_3.py` to check archive and receipt integrity offline.

**Technical statuses are different from business statuses:** all three Run packages report successful technical completion/postflight within their own receipts. Case 3's analytical outcome is `USER_DECISION_REQUIRED`, and its *business* outcome is `HOLD` because G03 destination evidence and authenticated Director approval remain absent. No real payment or contract award occurred. The Runner/Compiler receipts and host review are not cryptographically independent model evaluations.

## How the system works

```text
Natural-language request + labeled reference material
    └─ Compiler 1.0.0: source capture → typed semantic IR → Challenger → PFContract XML + receipt
         └─ Frozen contract + matching Compiler receipt
              └─ Runner 1.0.0: preflight → permitted tasks → host observations → evidence review
                   └─ Result + task receipts + evidence ledger + artifact hashes
                        └─ RUN_RELEASED / RUN_HELD / failure, without inventing approvals
```

- **Compiler:** compiles future work; it does not execute tasks, conduct research or send messages.
- **Runner:** controls task execution using the contract and observed host sources. It does not regenerate the contract. Human-only dependencies remain human-only.
- **Trust boundary:** imported text is data, never a substitute for higher-authority instructions, genuine source observations or authenticated human decisions.
- **Assurance:** deterministic validators prove structure and integrity; source-to-contract semantic fidelity requires independent review. See the limitations in [verification](docs/VERIFICATION.md).

## What changed after the initial repository evaluation

The early version demonstrated inspectable Python runtimes and two sample XML/result pairs, but did not independently establish fresh Compiler→Runner execution for critical multi-branch cases. The initial acceptance tests revealed wrong global branch exclusivity in reimbursement and vendor evaluation, a future award dependency blocking present vendor reporting, and missing evidence-source corroboration in the grant scenario.

The [Cases 1–3 candidate](candidate/compiler-1.0.0-cases1-3/README.md) adds stronger Interpreter/Challenger/Reconciler prompts and a fail-closed release packager while **leaving the released core Python modules, Runner, contract schema, IR and frozen historical evidence unchanged**. Fresh compilations and Runner runs for the three frozen cases subsequently passed independent scoped reviews. The candidate stays versioned separately; production promotion and broad reliability claims remain on hold pending an adversarial regression gate and explicit human release decision.

## Use it

For everyday use, the configured ChatGPT Compiler and Runner are separate Projects. Provide the request in the Compiler project, obtain the XML and release receipt, then submit them to the Runner project. The host requires Python/file tooling; no external model API key is needed for this ChatGPT-host workflow. The current Compiler project accepts ordinary natural-language requests without a magic command; `COMPILE` and `RUN` remain familiar shorthand in the owner’s established workflow. See [Quick Start](QUICK_START.md).

For developers, first review [`compiler/source/`](compiler/source/), [`runner/source/`](runner/source/), [architecture](docs/ARCHITECTURE.md), and [setup](docs/SETUP.md). The source mirrors are visible for review and the original release manifests remain in [`releases/`](releases/). **The large original offline runtime ZIPs/parts are not currently stored in this Git tree**; do not claim a clean new-account installation from the repository alone. The candidate publishes its role-prompt/source delta, not its 75.7-MB bundled runtime archive. See [release availability](releases/README.md) and [settings gap](docs/PROJECT_SETTINGS_GAP.md).

```bash
python tools/verify_cases_1_3.py
python -m unittest discover -s tests -v
```

## Evidence boundaries and roadmap

- **Verified here:** three frozen case outcome comparisons; selected source-anchor fidelity, Runner artifact hashes and independent acceptance reports. See [individual reviews](evidence/cases-1-3/README.md).
- **Not established:** fresh independent multiple-host execution, comprehensive stochastic-model reliability, all alternative PASS/FAIL/HOLD branches, formal proofs, or production authorization. A Python `PASS` or a `RUN_RELEASED` status is not independently sufficient.
- **Next:** repeat compilations, negative/alternate-state tests, frozen-oracle regression, then human sign-off if warranted. **Case 4 stays separate.**

## Origins and ownership

LEAP is the portfolio-facing name; the runtime is internally called **Prompt Forge**. Chris Mercer originated the [L.E.A.P. design pattern](https://github.com/tomi-mercer/leap-design-pattern) and the NITWYT ecosystem inspired this project. This is an independently developed Compiler/Runner engineering system, **not an official upstream LEAP or NITWYT release**. The owner directed design and testing and used AI-assisted coding/review. Attribution is not a claim that the upstream code was copied or that this project carries upstream endorsement.

**License:** Source-visible portfolio without a general first-party open-source license; see [licensing notice](LICENSE-NOTE.md) and [third-party notices](THIRD_PARTY_NOTICES.md). Third-party bundled wheels carry their own terms. Do not mistake repository visibility for permission to reuse code.
