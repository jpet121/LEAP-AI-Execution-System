# Protocol and evidence flow

## Compile

The Compiler's host exchange produces a request JSON containing role instructions, the current input and a JSON output schema. A valid host response is saved in `exchange/` using a hash-bound response envelope. Compile continues until a terminal outcome; `HostResponseRequired` is an internal handoff, not a final failure. The Independent Challenger sees only the defined request state and candidate IR; a PASS envelope alone does not prove genuine source review.

## Run

Runner preflight checks XML structure/identity and supported versions. The host then registers actual observations and supplies task-specific role responses. The engine enforces prerequisites, branch decisions, source/evidence references, authorization boundaries, and terminal status. A separate Challenger response checks each proposed action. The engine emits `RUN_RELEASED`, `RUN_HELD` or an explicit rejection/failure, with a verifiable execution record when export is completed.

## Evidence vocabulary

Claims distinguish observations, calculations, syntheses, evaluations, assumptions and scenarios. Source IDs, subject references, task references and location strings are recorded for traceability. Missing evidence can lead to documented limitations or no-determination outcomes. It must not be silently recoded as proof.

The system checks structure and binding, but no local Python method can establish that a source was authoritative, an extracted page faithful, or a factual conclusion justified. That responsibility remains with the host and human reviewer.

## Authoritative references

- [`compiler/03_RUNTIME_GUIDE.txt`](../compiler/03_RUNTIME_GUIDE.txt)  -  compiler host exchange and replay controls.
- [`runner/03_RUNTIME_GUIDE.txt`](../runner/03_RUNTIME_GUIDE.txt)  -  Runner CLI progression and exit codes.
- [`runner/source/HOST_PROTOCOL.md`](../runner/source/HOST_PROTOCOL.md)  -  complete model-host evidence/action protocol.
- [`runner/source/COMPATIBILITY.md`](../runner/source/COMPATIBILITY.md)  -  exact Compiler/Runner contract boundary.
- [`runner/source/KNOWN_LIMITATIONS.md`](../runner/source/KNOWN_LIMITATIONS.md)  -  explicit implementation and evidence limits.
