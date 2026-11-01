# LEAP - AI Execution System
### Natural-language contract compilation and evidence-aware execution

**AI-assisted requirements engineering · Python orchestration · Structured semantic contracts · Evidence traceability**

> **What it does:** LEAP turns an ordinary-language request into a structured XML execution contract, then uses a separate Runner to coordinate task work, source evidence, review checkpoints, and final output. Compilation specifies the work; execution is performed later by a capable model host.

**Why I built it:** I wanted a reusable daily workflow for giving AI systems precise instructions without silently losing requirements, changing decision rules, or confusing a compiled plan with completed work. I directed the system design and evaluation; AI-assisted development was used to implement and inspect the Python components.

**Under the hood:** Python 3.11+ Runner · Python 3.11-3.14 Linux x64 / Python 3.14 Windows x64 bundled wheels · Compiler 1.0.0 · PFContract XML 1.0 / IR 1.0 · JSON Schema / XSD · hash-linked receipts · role-specific host exchanges · Challenger checkpoints.

**Status:** Provided Compiler and Runner **passed local deterministic self-checks**; two supplied real-world-style case contracts **passed Runner preflight**. This does **not** certify the quality of model reasoning, verify every claim in the case studies, or establish production deployment. Original Compiler release receipts and ChatGPT Project Instructions were not supplied with this upload.

**Naming:** LEAP is the portfolio-facing system name. The supplied runtime identifies itself internally as **Prompt Forge Compiler** and **Prompt Forge Runner**. That implementation naming, all original source bytes, and archive bytes are preserved.

## Use LEAP in two commands

Normal daily use takes place inside two separately configured ChatGPT Projects:

| Step | What you provide | Command | What you receive |
| --- | --- | --- | --- |
| **1. Compiler** | Type or upload your natural-language request | `COMPILE` | The structured XML contract |
| **2. Runner** | Upload the compiled XML in the separate Runner Project | `RUN` | The executed task result and traceable evidence, or an explicit hold/failure |

**That is the entire everyday user workflow.** You do not need to write Python, set command-line arguments, or manually orchestrate model exchanges when using the configured Projects. The Compiler defines the work; the Runner executes it. For a concise walkthrough, see [Quick Start](QUICK_START.md).

**Deployment distinction:** The original ChatGPT Project instruction files were not part of the supplied package. The `COMPILE` and `RUN` invocation is the owner's stated current workflow; reproducing it in a newly configured Project requires the matching Project Instructions. See [Project settings prerequisites](docs/PROJECT_SETTINGS_GAP.md).

[Quick Start](QUICK_START.md) · [See two case studies](#leap-in-action) · [Architecture](#how-leap-works) · [Verification](#what-was-actually-checked) · [Developer setup](docs/SETUP.md) · [Source map](#repository-map)

## At a glance

| Question | Answer |
| --- | --- |
| **What did I build?** | A two-stage AI task orchestration system: a contract Compiler and a separate execution Runner. |
| **What problem does it solve?** | It makes the requested work explicit, inspectable, and checkable across planning, execution, source attribution, and result delivery. |
| **What skills does it demonstrate?** | Requirements modeling, structured-output protocols, Python runtime packaging, state machines, schema validation, provenance, challenge/repair workflows, replay checks, and human authority boundaries. |
| **Do the Python programs independently research or write?** | **No.** The host model performs semantic reasoning and actual tool work; Python validates protocol, structure and integrity. |
| **Can an engineer inspect the implementation?** | Yes. First-party source code is mirrored under [`compiler/source/`](compiler/source/) and [`runner/source/`](runner/source/), with untouched recoverable release archives under [`releases/`](releases/). |
| **What is the proof of use?** | Two user-supplied XML/result pairs from actual system usage: a four-day workweek assessment and a payroll/HR replacement evaluation. The organizations described are hypothetical scenarios. |

## The problem

An AI request can contain multiple constraints, conditional branches, evidence obligations and user-only decisions. In an unstructured interaction, the system may accidentally collapse conditions, change scope, fabricate a winner, or report an intended task as though it were completed.

LEAP separates **the specification of the work** from **the execution of the work**. The Compiler converts the user's request to a typed, structured contract; the Runner interprets the frozen contract through a model host, records actual evidence and produced artifacts, and checks the outcome against the contract. A passing Python integrity check should not be mistaken for proof that the model understood every source correctly.

## How LEAP works

```text
Ordinary-language request
           |
           v
  COMPILER (Prompt Forge 1.0.0)
  classify / interpret / reconcile / challenge
           |
           v
  Structured contract (PFContract XML 1.0)
  + semantic IR + package/receipt when available
           |
           v
  RUNNER (separate Python runtime)
  immutable preflight / dependency + branch control
           |
           v
  Host model + trusted tools + registered sources
  execute -> assess evidence -> challenge/repair
           |
           v
  Task artifacts + evidence / hash-linked run receipt
           |
           v
  RUN_RELEASED, RUN_HELD, or explicit failure
```

The two runtimes are **separate**. The Runner is designed to consume Compiler 1.0.0 / contract 1.0 / IR 1.0 output and reject unsupported versions. The Compiler does not execute task-world actions, and the Runner must not silently modify the frozen XML. Details: [architecture](docs/ARCHITECTURE.md), [protocol boundaries](docs/PROTOCOL_AND_EVIDENCE.md).

## LEAP in action

### Example 1 - Is a four-day workweek justified?

**Scenario:** A hypothetical 60-person professional-services firm considers a four-day workweek. The request requires current evidence, success/failure conditions, effects on six dimensions, and a 90-day pilot design **only if supported**.

**Contract behavior:** The [original XML](examples/four-day-workweek/contract.xml) contains explicit tasks, dependencies, evidence requirements, and mutually conditional paths (pilot versus no pilot). The provided [analytical result](examples/four-day-workweek/result.md) recommends **a limited, reversible 90-day pilot**, not a permanent change, with defined safeguards and decision gates.

**What it demonstrates:** Conditional execution, research attribution, a bounded recommendation, explicit business assumptions, and a result that stops short of promising organizational benefits. [Case study](examples/four-day-workweek/README.md).

### Example 2 - Which payroll/HR platform qualifies?

**Scenario:** A hypothetical 120-person construction business requires multi-state payroll, field/mobile time, benefits, onboarding, **QuickBooks Enterprise Desktop** integration, and a six-month rollout window.

**Contract behavior:** The [original XML](examples/payroll-platform-evaluation/contract.xml) requires assessment against mandatory requirements and an evidence-based comparison; it does not preselect a vendor. The [provided result](examples/payroll-platform-evaluation/result.md) explicitly reports **INSUFFICIENT_EVIDENCE**, not a forced winner, because critical integration and delivery conditions were not demonstrated.

**What it demonstrates:** Hard-requirement gates, avoiding unsupported recommendations, separating QuickBooks Online from Desktop Enterprise compatibility, and clear unknowns. [Case study](examples/payroll-platform-evaluation/README.md).

**Case-study evidence boundary:** These are *provided XML/result pairs from user operation*. The sample XML bytes passed local Runner preflight, with warnings that the original source-state and Compiler release receipts were not independently replayed. The result reports were reviewed as artifacts, **not regenerated by a fresh end-to-end Runner session for this portfolio build**. Findings in the reports are dated October 20-21, 2026, not live market verification.

## What was actually checked

| Check | Result | Meaning / limitation |
| --- | --- | --- |
| Compiler 1.0.0 `self-check` | **PASS** | Deterministic installation smoke test with a protocol stub, not independent semantic-model evaluation. |
| Runner 1.0.0 `self-check` | **PASS** | Runtime self-check, not proof of model-host deployment. |
| Four-day-workweek XML `preflight` | **PASS** | Structural checks passed; external Compiler release receipt not supplied. |
| Payroll XML `preflight` | **PASS** | Structural checks passed; source-event provenance asserted, not independently reproduced. |
| Supplied runtime ZIPs | **Byte-for-byte preserved** | Split for browser upload; the provided hashes and byte counts allow exact reconstruction. |
| Source mirror | **Byte-for-byte copied** | First-party mirrored files compared to the originals inside the uploaded archives. |
| Host model and source claims | **Not independently certified here** | Host reasoning, evidence interpretation, live ChatGPT Project UI, and third-party source accuracy require separate testing. |

See [verification details](docs/VERIFICATION.md) and [release status](RELEASE_STATUS.json). No numerical coverage, fuzzing campaign, formal proof, or independent certification is claimed for this portfolio package because corresponding executed evidence was not supplied.

## Try it in ChatGPT

In your existing LEAP Compiler Project, submit natural language and type `COMPILE`. Take the generated XML to your separate LEAP Runner Project and type `RUN`. Those are the only routine user commands.

Technical reviewers who want to reproduce the offline Python environment, inspect runtime source, run smoke tests or verify the archived bytes can follow [Developer Setup](docs/SETUP.md). Those engineering procedures are **optional** and are not part of the normal user workflow.

## Repository map

| Location | Purpose |
| --- | --- |
| [`compiler/source/`](compiler/source/) | Inspectable, unchanged first-party Compiler files and schema/prompt assets (bundled wheels are in the original ZIP). |
| [`runner/source/`](runner/source/) | Inspectable, unchanged first-party Runner files, schemas, protocols and constraints. |
| [`releases/compiler/`](releases/compiler/) / [`releases/runner/`](releases/runner/) | Exact original runtime ZIPs split into browser-uploadable parts, each with integrity manifest. |
| [`examples/`](examples/) | Two original XML/result pairs and case-study commentary. |
| [`docs/`](docs/) | Architecture, protocol, installation, verification, limitations and project decisions. |
| [`tools/`](tools/) | Archive reconstruction and source/integrity verification scripts. |
| [`tests/`](tests/) | Stdlib tests of this repository's packaging, examples and integrity metadata. |

## Licensing

This is a public **source-visible portfolio project without a first-party open-source license**. Viewing the code is not a general grant to reuse it. Bundled dependencies have separate upstream license conditions; see [Licensing notice](LICENSE-NOTE.md) and [Third-party notices](THIRD_PARTY_NOTICES.md).

## Limitations and release boundaries

- **The original ChatGPT Project instruction files** named in the original `01_START_HERE` guides were **not included** in the supplied materials: `00_PROJECT_INSTRUCTIONS_COMPILER.txt` and `00_PROJECT_INSTRUCTIONS_RUNNER.txt`. These must be exported from the currently configured Projects before a new-account deployment is documented as complete. They have not been invented or silently replaced. See [missing settings](docs/PROJECT_SETTINGS_GAP.md).
- The Compiler/Runner Python checks validate formats, references, receipts and protocol transitions; they do **not** certify truth, originality, source reading, or correct semantics in model replies.
- The Runner's Challenger is a distinct review step in the same host context, not a cryptographically isolated or separately staffed independent auditor.
- Bare XML may pass preflight with a provenance warning. It is **not** equivalent to passing replay of a complete Compiler package with the original signed-off source records.
- A release receipt or SHA-256 manifest is an integrity reference, not a signature or independent proof of human authorization.
- Source examples are analytical outputs dated October 2026. They are not live payroll advice, employment-law advice or production change authorizations.
- This is a human-directed AI engineering portfolio, **not** a standalone language model, proof of autonomous tool execution without a model host, or third-party certified platform.

**Focus:** Build AI systems whose instructions can be inspected, whose work can be traced to evidence, and whose unknowns remain visible rather than converted into unsupported certainty.
