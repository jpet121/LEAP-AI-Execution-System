# Live Compiler boundary

Inspected release: Prompt Forge Compiler 1.0.0; contract 1.0; IR 1.0.
Other versions reject pending a tested versioned adapter.

The actual render.py emits PFContract, Objective, eleven ordered semantic
sections, then Provenance. Each section contains Node elements with canonical
JSON text. ResultPolicy has exactly one object. The released XSD, IR schema and
receipt schema are copied unchanged into the Runner.

Canonical JSON: UTF-8, ensure_ascii=False, sorted keys, comma/colon separators,
allow_nan=False, one trailing LF. The reconstructed IR includes every section,
objective, ir_version and source_state_sha256. This exact renderer emits all IR
fields, enabling independent reproduction of verified_ir_sha256. Contract ID is
PF- plus that hash. Exact XML bytes are frozen and hashed separately. Provenance
must equal the sorted unique union of node source anchors.

Original source-state authority/span hashes remain Compiler assertions for bare
XML without RequestState. That differs from reproducing the embedded IR hash.
Optional receipts use the released strict schema. Release status, challenge PASS,
versions, identity hashes, and every listed artifact hash must match. A receipt
with missing artifacts rejects. Bare XML is accepted with an explicit warning
that no external receipt binding was supplied. Input package code never runs.

Seven unchanged real fixtures cover payroll/HR, Austin property, single-book podcast, two-book
comparison, article concepts with terminal USER_ONLY, membership strategy, and
four-day workweek branches. All pass schema, structural references, provenance
inventory and reconstructed IR identity checks. The unnumbered payroll contract
and exact article transcript were subsequently found in Downloads. Referenced
books were found in D:/Books; both comparison-book hashes match the embedded
contract labels. No actual emitted Compiler receipt accompanied the XML files;
receipt integration is exercised by a complete schema-conformant synthetic release.

Dependency reachability includes intermediate non-task nodes. Only reachable
executable consumers force a USER_ONLY HOLD; an explicitly future entity outside
the current executable tasks does not. This is exercised by the article fixture.
Branch decision prerequisites come from incoming dependencies of active nodes;
condition truth remains reviewed host reasoning. Branch-local constraints stay
scoped. New candidates require generation_rule and observed source provenance.

OVER_COLLECTION preserves member identities and checks final coverage. The 1.0
interface does not bind BOUNDED_COUNT/UNTIL_CONDITION to an executable loop body.
The released schema has no body field; validation checks count/stop condition,
and render.py serializes the standalone node unchanged. Actual unchanged-Compiler
compilations in tests/fixtures/iteration_compiler demonstrate COMPILE_RELEASED
for both modes without a body binding, including full receipt preflight.
Their synthetic semantic adapter proves protocol emission, not semantic quality.
See acceptance/iteration_interface_proof/INTERFACE_PROOF.json in the acceptance
delivery for implementation fingerprints and the seven supplied controls.

Therefore the answer to the interface question is YES. Runner adds optional
host execution metadata: bind_iteration(control_id, task_refs, basis), separately
challenged before execution. It does not change XML, IR, Compiler schemas or
contracts, or infer relationships the Compiler does not guarantee. Unbound input
still holds. Supported plans are explicit, disjoint, dependency-convex GLOBAL
task bodies within the documented resource caps. Until termination is a reviewed
round-bound semantic judgment. All rounds remain in the replay journal/history.
