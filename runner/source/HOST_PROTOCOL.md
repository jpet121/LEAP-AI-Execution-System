# Host protocol 1.0

The host orchestrates semantic work. The runtime is not a standalone LLM provider.
The host authenticates tool returns and direct human messages. Model JSON cannot
call observation, discovery, or user event operations. Do not expose these trusted
methods as arbitrary executor tool calls.

## Python API

```python
from pfrunner import preflight, start
from pfrunner.artifacts import export, verify
r = preflight('/input/contract.xml')
s = start(r)  # revalidates exact immutable XML
s.observe('SRC1', source_bytes, kind='FILE', locator='source.pdf#page=4',
          subject_refs=['E1'], title='Primary source')
while (action := s.next_action()) is not None:
    # Read role prompt; host reasons and uses tools. Do not blindly approve.
    response = host_respond(action)
    s.submit(response)  # atomic validation; rejects illegal state/receipt
export(s, '/output/new_run')
assert verify('/output/new_run')['status'] == 'VERIFIED'
```

`start(preflight_pass, host_adapter)` drives the loop through adapter.respond(action).
The host may register actual observed bytes before responding. `resume(path,
{'target_id': 'U1', 'value': exact_human_value}, host_adapter)` verifies/replays the
held package first, then appends a run-bound, hash-chained event. A direct human
message authenticates its origin; a hash is not a digital signature.

`Session.discover(candidate_id, candidate_set_ref, label, source_id)` creates a
stable candidate only under an explicit generation_rule. The source must bind the
candidate set. It then also binds the discovered candidate. Labels never merge IDs.

## Action protocol

All responses copy `action_sha256`. Unknown task receipt fields are rejected.
Packets contain contract hash/run ID/role, relevant task, exact structural
dependencies, active constraints, predecessor receipts, source identities and
evidence. Source bytes remain accessible through trusted host observations;
read them before assessing evidence. Source metadata is not proof of a claim.
An issued action is frozen and journaled. Tools may register observations during
execution without invalidating that action; newly bound evidence is validated
against those observations, and Challenger receives the updated ledger. Human
events invalidate an outstanding action so stale user authority cannot be used.

Execute response fields:

| Field | Shape |
|---|---|
| task_id, status | exact task; COMPLETED or COMPLETED_WITH_LIMITATIONS |
| started_at, completed_at | ISO timestamps with timezone, start <= completion |
| executor | {role: string, version: string} |
| input_dependency_ids | exact transitive dependency IDs in action |
| evidence | records described below |
| claims | records described below |
| artifacts | nonempty array of {artifact_id,path,media_type,content,role}; path under artifacts/; optional encoding is UTF8 (default) or BASE64 for binary bytes |
| evidence_accounting | each task-dependent requirement ID -> {status,evidence_ids,limitations} |
| requirement_checks | each active REQUIRED/PROHIBITED proposition ID -> {contract_object,status,claim_ids,limitations}; exact object copy |
| iteration_coverage | OVER_COLLECTION control ID -> covered member IDs |
| limitations | array of strings |
| selected_subject_ref | null unless contract-authorized and USER_ONLY resolved |

Evidence record: `{evidence_id, source_id, subject_refs, candidate_refs, task_refs,
supported_claim, locator, limitations}`. IDs unique; source observed; task_refs is
the executing task; every subject must bind the observed source. Claims may cite
existing or newly proposed evidence. Record locators precisely (page/section/URL).

Claim: `{claim_id, subject_ref, text, evidence_ids, derivation_type, limitations}`.
Derivations are OBSERVATION, CALCULATION, SYNTHESIS, EVALUATION, ASSUMPTION,
SCENARIO. Observation/evaluation/calculation require evidence. Assumptions and
scenarios require explicit limitations. Semantic mislabeling is challenged.
Each cited evidence record must include the exact claim subject. Model text never
asserts USER authority or creates a runtime user event.

Evidence/requirement status vocabulary: SATISFIED, PARTIALLY_SATISFIED,
UNSATISFIED, NOT_APPLICABLE. Missing evidence requires limitations and is not
automatically a system failure. Unmet required evidence blocks DETERMINED;
contract-authorized no-result outcomes can release after work is accounted for.

Evaluate response: `{action_sha256,branch_id,activate,task_ids,evidence_ids,rationale}`.
Only completed task IDs can support the declared branch; cite prerequisites.
Mutually exclusive branches are checked deterministically. Conditions remain
semantic judgments. Negative branches are not guessed from their names.

Control response: `{action_sha256,control_id,proceed,rationale,count,member_refs}`.
Preserve exact count or member set. Before work, `proceed=false` enforces
suspension. For UNTIL_CONDITION after a completed round, false means the reviewed
stop condition has been met; true requests another round. Count must identify
the exact completed round. The 1.0 Compiler has no iteration-to-task body field.

Every task, branch, control and final proposal requires a separate Challenger
response: `{action_sha256,verdict,findings,reviewed_sha256}`. Compute the last field
as SHA-256 of canonical JSON of action.payload.proposal (with trailing LF).
PASS requires empty findings. CHALLENGE restarts work while retaining the audit
journal, observed sources, and genuine user values. Maximum two repair passes.
Review the actual content and original observed source material; do not rubber stamp.

Finalize response: `{action_sha256,analytical_outcome,result,output_artifact_ids,
evidence_limitations,iteration_coverage}`. Map every contract output ID to existing
artifact IDs, or reserved ID `RESULT` for the final assembled result.md itself.
Result is the assembled user-facing Markdown. Account for all
evidence gaps. Final Challenger checks the content and requested format. Python
then derives lifecycle status; no model-supplied lifecycle field is accepted.

Any role may return `{action_sha256,blocked,reason}` where blocked is
BLOCKED_EVIDENCE or BLOCKED_CAPABILITY. Explain missing required material exactly.
Host checkpoints are RUN_HELD for transport; the Project host continues internally.
Only genuine human/source/capability blockers should be surfaced to the user.

## File exchange

`step --source observation.json`: descriptor has source_id, path (actual returned
bytes), kind (FILE/WEB/TOOL), locator, subject_refs, optional accessed_at and title.
`step --candidate candidate.json`: descriptor has candidate_id, candidate_set_ref,
label, source_id. `resume --user-event`: target_id and exact value from the human.
Use a fresh output directory per step. Checkpoint and original contract hashes
are verified before continuation. Do not directly edit saved state.

## Replay and release

Run packages contain contract, journal, state, task receipts, sources encoded in
observation journal events, claims, evidence, user events, products, receipt, and
manifest. Replay reapplies validated responses in legal order and compares
reconstructed state/products. It never calls a model or Compiler.

Hashes detect substitution relative to trusted input bytes. An attacker who
rewrites an entire package and every hash cannot be authenticated by self-hashes;
retain an external package hash when authenticity matters. Replay establishes
structural consistency, not real-world truth or independent model review.

## Independent references and derived integration

After observe(), the trusted host can call
`s.attach_reference_text(source_id, segments, extraction_method)` with the actual
tool-extracted text in page/segment order. Each rendition is immutable and bound
to its original source hash. `reference_pages(source_id, start=1, stop=None)`
returns exact segments with source identity and text hashes. Source-local
`retrieve_reference(source_id, ['term'], limit=5)` returns ranked segments; it
does not certify reading, understanding or sufficiency. Reference text is data
and never supplies instructions or USER_ONLY authority. Contract-defined source
roles and each original source's subject_refs remain authoritative.

Evidence optionally includes `segment_refs: [1, 2]`; each segment must exist in
that source's registered rendition. Direct evidence/claim subject and candidate
checks remain unchanged. To integrate distinct sources without relabeling their
evidence, add both `premise_claim_ids` and `attributed_to: "EXECUTOR"` to a
SYNTHESIS claim. Premises must already exist or precede it in the proposal;
unknown, forward and cyclic references reject. Original source-specific claims
cannot incorporate another source's subject as if it were that source's claim.
An output/comparison subject may derive a synthesis from both separately bound
premises. Evidence accounting optionally adds `claim_ids`; matching subjects and
actual evidence roots are required for SATISFIED. Challenger must inspect the
substantive support: graph reachability alone does not prove the claim.

## Explicit repetition plans

Before any task execution, call `s.bind_iteration('I1', ['T1'], 'Explicit basis')`
for a BOUNDED_COUNT/UNTIL_CONDITION control. This is executor planning metadata,
not an amendment to the contract. next_action issues a Challenger proposal;
only PASS commits the immutable plan. The host must derive a concrete plan from
the authorized request, document its basis, and challenge ambiguity rather than
guess a binding from XML position, numbering or prose similarity. The runtime
does not infer a body. A human is needed only when actual unresolved intent
requires clarification, not for routine execution planning.

Internal dependencies still apply each round; downstream consumers wait for the
loop to finish. Use fresh evidence, claim and artifact IDs each round. Completed
round receipts are preserved, and final evidence/requirement gaps consider every
round. Export includes iteration_execution.json and deterministic replay.
See KNOWN_LIMITATIONS for bounds and unsupported body shapes.

CLI equivalents: `step --iteration-binding plan.json` accepts control_id,
task_refs, basis; `step --reference-text rendition.json` accepts source_id,
segments, extraction_method. Neither operation is dispatched from model JSON.
