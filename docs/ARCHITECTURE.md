# Architecture and authority boundaries

**User interface:** Enter natural language and type `COMPILE` in the configured Compiler Project; upload the XML into the configured Runner Project and type `RUN`. All detailed host exchanges described here happen internally. The engineering commands are not additional daily user instructions.

## Component 1  -  Compiler 1.0.0 (Prompt Forge)

The Compiler takes ordinary language, constructs structured semantic intermediate representation (IR), and renders `PFContract` XML. The released host adapter performs role-specific model exchanges (classifier, interpreter, reconciler and challenger). Runtime code checks structural invariants and serializes immutable artifacts. Compiler result states include released contracts, clarification, unsupported meaning and real infrastructure failure. The Compiler describes future authorized work; it does not execute the requested downstream task.

The XML contains an Objective and the following sections: Entities, Tasks, CandidateSets, Propositions, Branches, Dependencies, EvidenceRequirements, UserDecisions, IterationControls, Outputs, ResultPolicy, and Provenance. `Node` text is canonical JSON. Consumers decode the typed JSON, not a free-form reinterpretation of the user prompt. Contract version 1.0, Compiler 1.0.0 and IR 1.0 are the tested interface.

## Component 2  -  Runner 1.0.0

The Runner accepts the immutable compiled XML (or an eligible full Compiler release package), validates its structure and identity, orchestrates a model host with trusted tools, records source observations and evidence, manages dependencies, branches, user-only decisions and bounded repair cycles, then exports task artifacts and a replay-verifiable receipt.

The Runner does not import the Compiler and may not modify the XML bytes. It accepts bare XML with an explicit provenance limitation. It refuses unsupported contracts instead of guessing compatibility. The model host must carry out research, use tools, read source material and produce artifacts; the Python process alone cannot do that semantic task work.

## Trust boundaries

| Boundary | What can be checked | What cannot be established by hashing alone |
| --- | --- | --- |
| Natural language → IR | Internal schema, references, Challenger exchange | Exact adequacy of the model's interpretation of every human intention |
| IR → XML | Canonical rendering, byte identity, section integrity | Whether the user wanted what the IR encodes |
| XML → Runner | Version compatibility, contract structure, dependency edges | Authenticity of the original source events for bare XML |
| Model host → evidence | Source IDs, supported claim references, preserved observed bytes | Whether a web result was truthful or a model actually read/understood a document |
| Review → release | Action hash, separate review response, receipt chain | Human independence, full semantic correctness, or an externally certified audit |

## Important iteration limitation

Compiler 1.0 does not bind a `BOUNDED_COUNT` or `UNTIL_CONDITION` control to a task body. Runner therefore requires an explicit host `bind_iteration` plan and Challenger approval before work. It does not infer the body from XML order or labeling. Unsupported body shapes or unresolved plans stay held/rejected. Source: the included unchanged `runner/source/COMPATIBILITY.md` and `runner/source/KNOWN_LIMITATIONS.md`.

## Separate Case 4 application

[Case 4 — Synthetic USD Reconciliation API](../case4/README.md) is a distinct implementation exercise, not a plugin or privileged extension to the Compiler/Runner. It uses FastAPI and Pydantic input guards, psycopg parameterized queries, a PostgreSQL account lock and atomic ledger/balance write, and idempotent transaction IDs. The `X-API-Key` secret is supplied by the local operator, never stored here. External banking and live payment operations are outside the design. Refer to its application README for full boundaries, tests, and limitations. Engineering release remains HOLD pending independent live-host verification, hosted CI and human authorization.
