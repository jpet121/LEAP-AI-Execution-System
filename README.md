# LEAP-AI Execution System
### Compiler + Runner | Evidence-Aware AI workflow engineering

[Architecture](docs/ARCHITECTURE.md) · [Quick start](QUICK_START.md) · [Final Compiler build](compiler/final-2026-11-02/README.md) · [Verified Cases 1–3](evidence/cases-1-3/README.md) · [Case 4 API](case4/README.md) · [Verification](docs/VERIFICATION.md)

**LEAP turns natural-language business requests into inspectable contracts, then executes them through a separate evidence-aware Runner.** It is a human-directed system built with Python orchestration, XML/JSON schemas, explicit role-specific host exchanges, provenance checks, conditional execution and challenge checkpoints. The host model performs interpretation and task-world work; the Python runtimes enforce structure, hashes and legal execution states.

## Origins

LEAP is the portfolio-facing name; the runtime is internally called **Prompt Forge**. Chris Mercer originated the [L.E.A.P. design pattern](https://github.com/tomi-mercer/leap-design-pattern) and the NITWYT ecosystem inspired this project. This is an independently developed Compiler/Runner engineering system, **not an official upstream LEAP or NITWYT release**. The owner directed design and testing and used AI-assisted coding/review. Attribution is not a claim that the upstream code was copied or that this project carries upstream endorsement.

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

## Use it

For everyday use, the configured ChatGPT Compiler and Runner are separate Projects. Provide the request in the Compiler project, obtain the XML and release receipt, then submit them to the Runner project. The host requires Python/file tooling; no external model API key is needed for this ChatGPT-host workflow. The current Compiler project accepts ordinary natural-language requests without a magic command; `COMPILE` and `RUN` remain familiar shorthand in the owner’s established workflow. See [Quick Start](QUICK_START.md).

For developers, browse [final Compiler first-party source](compiler/final-2026-11-02/source/), [the unchanged Runner source](runner/source/), [Case 4's FastAPI/PostgreSQL implementation and tests](case4/reconciliation-api/), [architecture](docs/ARCHITECTURE.md), and [setup](docs/SETUP.md). The original baseline and frozen case evidence remain intact. **The 26.3-MB final Compiler offline wheelhouse ZIP and original historical runtime archives are not stored in this Git tree**; GitHub exposes the source plus hashes and instructions, not a complete offline-bundled installation. See [final build availability](compiler/final-2026-11-02/README.md), [release availability](releases/README.md) and [settings gap](docs/PROJECT_SETTINGS_GAP.md).

```bash
python tools/verify_cases_1_3.py
python -m unittest discover -s tests -v
```

## Evidence boundaries and roadmap

- **Verified here:** three frozen case outcome comparisons; selected source-anchor fidelity, Runner artifact hashes and independent acceptance reports. See [individual reviews](evidence/cases-1-3/README.md).
- **Not established:** fresh independent multiple-host execution, comprehensive stochastic-model reliability, all alternative PASS/FAIL/HOLD branches, formal proofs, or production authorization. A Python `PASS` or a `RUN_RELEASED` status is not independently sufficient.
- **Final Compiler designation:** explicitly owner-approved for their Compiler Project, while maintaining the original baseline and disclosing bounded frozen-case evidence.
- **Case 4:** [browse source/tests](case4/reconciliation-api/), [standalone architecture and setup](case4/reconciliation-api/README.md), and [release HOLD](case4/reconciliation-api/evidence/RELEASE_READINESS.md). Independent pure-data checks and submitted local PostgreSQL replay are documented; hosted GitHub Actions must complete before revising its CI status. Publication does not imply human production authorization.
- **Next:** continue regression/alternate-state testing and maintain adversarial regression tests; consult [Case 4 Actions](https://github.com/jpet121/LEAP-AI-Execution-System/actions/workflows/case4-reconciliation-api.yml) for ongoing CI results.


**License:** Source-visible portfolio without a general first-party open-source license; see [licensing notice](LICENSE-NOTE.md) and [third-party notices](THIRD_PARTY_NOTICES.md). Third-party bundled wheels carry their own terms. Do not mistake repository visibility for permission to reuse code.
