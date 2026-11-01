"""Auditable scheduler and structured host protocol.

Semantic proposals are always reviewed. Neither a prose status nor a host-selected
task can bypass eligibility or deterministic postflight.
"""
import base64
import copy
from datetime import datetime, timezone
import uuid
import jsonschema
from typing import Protocol
from .contract import parse, PreflightResult
from .io import canonical, sha, require, Invalid, MAX_FILE, schema
from .planning import IterationPlans
from .references import References

DONE = {'COMPLETED', 'COMPLETED_WITH_LIMITATIONS'}
EVIDENCE_STATES = {'SATISFIED', 'PARTIALLY_SATISFIED', 'UNSATISFIED', 'NOT_APPLICABLE'}
DERIVATIONS = {'OBSERVATION', 'CALCULATION', 'SYNTHESIS', 'EVALUATION', 'ASSUMPTION', 'SCENARIO'}


class HostAdapter(Protocol):
    def respond(self, action: dict) -> dict:
        """Return {action_sha256, ... structured role response}; use host tools first."""


def now():
    return datetime.now(timezone.utc).isoformat()


class Session(IterationPlans, References):
    def __init__(self, contract, run_id=None, input_hashes=()):
        # Reparse immutable bytes at the execution boundary, never trust a forged view.
        self.contract = parse(contract.xml)
        self._frozen_contract_sha256 = self.contract.sha256
        self.ir = self.contract.ir
        self.run_id = run_id or str(uuid.uuid4())
        self.input_hashes = dict(input_hashes)
        self.index = {n['id']: n for k, v in self.ir.items() if isinstance(v, list)
                      for n in v if isinstance(n, dict) and 'id' in n}
        self.task_ids = {t['id'] for t in self.ir['tasks']}
        self.branch_ids = {b['id'] for b in self.ir['branches']}
        self.decision_ids = {d['id'] for d in self.ir['user_decisions']}
        self.parents = {n: [] for n in self.index}
        for e in self.ir['dependencies']:
            self.parents[e['successor_ref']].append(e['predecessor_ref'])
        self.journal = []
        self.sources = {}
        self.reference_texts = {}
        self.events = []
        self.decisions = {}
        self.repair_count = 0
        self.executions = 0
        self.lifecycle = 'RUNNING'
        self.outcome = None
        self.hold_reason = None
        self.failure = None
        self.last_errors = []
        self._replaying = False
        self.iteration_bindings = {}
        self._reset_work()

    def _reset_work(self):
        self.tasks = {t: 'PENDING' for t in self.task_ids}
        self.branches = {}
        self.receipts = {}
        self.evidence = {}
        self.claims = {}
        self.artifacts = {}
        self.pending = None
        self.final = None
        self.challenge = None
        self.controls = {}
        self.iteration_progress = {}
        self._issued = None

    def _record(self, op, data):
        if self._replaying:
            return
        entry = {'op': op, 'data': copy.deepcopy(data), 'timestamp': now(),
                 'previous_hash': self.journal[-1]['entry_hash'] if self.journal else None}
        entry['entry_hash'] = sha(canonical(entry))
        self.journal.append(entry)

    def observe(self, source_id, data, *, kind, locator, subject_refs, accessed_at=None, title='',
                published_at=None, effective_date=None):
        """Trusted host tool boundary. Never invoke from model response dispatch.

        Host provides actual returned bytes, preserving a file/page/tool identity.
        The model subsequently cites source_id; it cannot register a tool success.
        """
        record = {'source_id': source_id, 'data_base64': base64.b64encode(data).decode(),
                  'kind': kind, 'locator': locator, 'subject_refs': subject_refs,
                  'accessed_at': accessed_at or now(), 'title': title, 'sha256': sha(data),
                  'published_at': published_at, 'effective_date': effective_date}
        self._observe(record)
        self._record('observe', record)

    def _observe(self, record):
        require(self.lifecycle in {'RUNNING', 'RUN_HELD'}, 'Cannot add sources to a terminal run')
        require(len(self.sources) < 1000, 'Source count cap')
        require(record['source_id'] not in self.sources and record['source_id'], 'Duplicate/empty source ID')
        data = base64.b64decode(record['data_base64'], validate=True)
        require(len(data) <= MAX_FILE and sha(data) == record['sha256'], 'Source byte/hash mismatch')
        require(sum(len(v.get('data_base64', '')) for v in self.sources.values()) + len(record['data_base64'])
                <= 44_000_000, 'Observed source total cap')
        require(record['kind'] in {'FILE', 'WEB', 'TOOL'} and record['locator'] and record['accessed_at'],
                'Source provenance required')
        require(record['kind'] != 'WEB' or record['locator'].startswith(('https://', 'http://')),
                'Web observations require actual source URL')
        require(set(record['subject_refs']) <= set(self.index), 'Unknown observed subject')
        self.sources[record['source_id']] = copy.deepcopy(record)

    def user_event(self, target_id, value):
        """Call only for an explicit human message targeting a declared slot.

        The trusted host, not an executor JSON response, authenticates the human.
        """
        event = {'event_id': 'U' + str(len(self.events) + 1), 'run_id': self.run_id,
                 'target_id': target_id, 'value': copy.deepcopy(value), 'timestamp': now(),
                 'previous_event_hash': self.events[-1]['event_hash'] if self.events else None}
        event['event_hash'] = sha(canonical(event))
        self._user(event)
        self._record('user', event)

    def _user(self, event):
        require(self.lifecycle in {'RUNNING', 'RUN_HELD'}, 'Cannot append user events to terminal run')
        require(event['run_id'] == self.run_id and event['target_id'] in self.decision_ids,
                'Unauthorized USER_ONLY slot/run')
        require(event['target_id'] not in self.decisions, 'User event cannot overwrite a resolved decision')
        require(event['value'] is not None and event['value'] != '', 'Explicit user value required')
        require(event['event_id'] == 'U' + str(len(self.events) + 1), 'Event order mismatch')
        require(event['previous_event_hash'] == (self.events[-1]['event_hash'] if self.events else None),
                'Event chain mismatch')
        require(event['event_hash'] == sha(canonical({k: v for k, v in event.items() if k != 'event_hash'})),
                'Event hash mismatch')
        self.events.append(copy.deepcopy(event))
        self.decisions[event['target_id']] = copy.deepcopy(event['value'])
        self._issued = None
        if self.lifecycle == 'RUN_HELD':
            self.lifecycle, self.hold_reason = 'RUNNING', None

    def scopes(self, nid):
        seen = set()
        n = self.index[nid]
        if n.get('condition_ref'):
            seen.add(n['condition_ref'])
        scope = n.get('scope_ref', 'GLOBAL')
        while scope != 'GLOBAL':
            if scope in self.branch_ids:
                seen.add(scope)
            scope = self.index[scope].get('scope_ref', 'GLOBAL')
        return seen

    def active(self, nid):
        states = [self.branches.get(b) for b in self.scopes(nid)]
        if False in states:
            return False
        if None in states:
            return None
        return True

    def prerequisites(self, nid):
        result, stack = set(), list(self.parents.get(nid, []))
        while stack:
            v = stack.pop()
            if v in result:
                continue
            result.add(v)
            stack.extend(self.parents.get(v, []))
        return result

    def ready(self, nid):
        return self.active(nid) is True and self._iteration_allows(nid) and all(
            (self.tasks[p] in DONE if p in self.task_ids else
             p in self.decisions if p in self.decision_ids else
             self.branches.get(p) is True if p in self.branch_ids else True)
            for p in self.prerequisites(nid))

    def unresolved_for(self, nid):
        return self.prerequisites(nid) & (self.decision_ids - set(self.decisions))

    def _refresh(self):
        for t in self.ir['tasks']:
            tid = t['id']
            if tid in self.receipts:
                continue
            if self.active(tid) is False:
                self.tasks[tid] = 'SKIPPED_INACTIVE_BRANCH'
            elif self.ready(tid):
                self.tasks[tid] = 'READY'
            elif self.unresolved_for(tid) and self.active(tid) is True:
                self.tasks[tid] = 'BLOCKED_USER_ONLY'
            else:
                self.tasks[tid] = 'PENDING'
        if self.pending and self.pending['kind'] == 'task':
            self.tasks[self.pending['task_id']] = 'RUNNING'

    def _packet(self, role, payload):
        packet = {'protocol_version': '1.0', 'run_id': self.run_id,
                  'contract_sha256': self.contract.sha256, 'role': role,
                  'payload': copy.deepcopy(payload), 'repair_count': self.repair_count}
        packet['action_sha256'] = sha(canonical(packet))
        self._issued = copy.deepcopy(packet)
        self._record('issue', {'action_sha256': packet['action_sha256']})
        return copy.deepcopy(packet)

    def context(self):
        result = {'objective': self.ir['objective'], 'propositions': self.ir['propositions'],
                'candidate_sets': self.ir['candidate_sets'], 'entities': self.ir['entities'],
                'evidence_requirements': self.ir['evidence_requirements'],
                'outputs': self.ir['outputs'], 'iteration_controls': self.ir['iteration_controls'],
                'result_policy': self.ir['result_policy'], 'user_decisions': self.ir['user_decisions'],
                'runtime_user_values': self.decisions,
                'sources': {k: {x: v for x, v in s.items() if x != 'data_base64'} for k, s in self.sources.items()},
                'evidence': self.evidence, 'claims': self.claims}
        if self.iteration_bindings:
            result['iteration_bindings'] = self.iteration_bindings
            result['iteration_progress'] = self.iteration_progress
        if self.reference_texts:
            result['reference_renditions'] = {sid: {
                'source_sha256': self.sources[sid]['sha256'], 'rendition_sha256': sha(canonical(r)),
                'segment_count': len(r['segments']), 'extraction_method': r['extraction_method'],
                'role': r['role']} for sid, r in self.reference_texts.items()}
        return result

    def task_scope_applies(self, node_id, task_id):
        scope = self.index[node_id].get('scope_ref', 'GLOBAL')
        while scope != 'GLOBAL':
            if scope in self.task_ids and scope != task_id:
                return False
            scope = self.index[scope].get('scope_ref', 'GLOBAL')
        return True

    def next_action(self):
        require(self.contract.sha256 == self._frozen_contract_sha256 and canonical(self.ir) == self.contract.payload,
                'Immutable contract projection was modified')
        if self.lifecycle != 'RUNNING':
            return None
        if self._issued is not None:
            return copy.deepcopy(self._issued)
        self._refresh()
        if self.pending:
            return self._packet('challenge', {'contract': self.ir, 'proposal': self.pending,
                                'context': self.context(), 'task_states': self.tasks,
                                'artifacts': self.artifacts,
                                'review_context': 'same-host-context; no isolated-model independence'})
        # Iteration controls are assessed against explicit collection/count/stop
        # payloads; text stop conditions remain host semantic judgments.
        for control in self.ir['iteration_controls']:
            if control['id'] not in self.controls:
                if control['mode'] in {'UNTIL_CONDITION', 'BOUNDED_COUNT'}:
                    if control['id'] in self.iteration_bindings:
                        return self._packet('control', {'control': control, 'context': self.context(),
                            'binding': self.iteration_bindings[control['id']]})
                    self.lifecycle = 'RUN_HELD'
                    self.hold_reason = {'reason': 'Compiler 1.0 iteration control has no executable-body binding; '
                                        'automatic repeated execution would invent a task mapping.',
                                        'target_ids': [control['id']], 'blocked_tasks': self.tasks.copy(),
                                        'next_action': 'Provide explicit bind_iteration 1.0 host plan for semantic challenge; never infer body.'}
                    return None
                return self._packet('control', {'control': control, 'context': self.context()})
        handled, packet = self._repeat_action()
        if handled:
            return packet
        self._refresh()
        for t in self.ir['tasks']:
            if self.tasks[t['id']] == 'READY':
                context = self.context()
                # Keep branch-local constraints scoped; do not globalize them.
                context['propositions'] = [p for p in self.ir['propositions'] if self.active(p['id']) is True
                                           and self.task_scope_applies(p['id'], t['id'])]
                return self._packet('execute', {'task': t, 'context': context,
                    'predecessor_receipts': {k: v for k, v in self.receipts.items()
                                             if k in self.prerequisites(t['id'])},
                    'dependencies': sorted(self.prerequisites(t['id'])),
                    'last_errors': self.last_errors})
        for b in self.ir['branches']:
            if b['id'] in self.branches or self.active(b['id']) is not True:
                continue
            external = set()
            for n in b['active_node_refs']:
                external.update(self.prerequisites(n) - set(b['active_node_refs']))
            unfinished_loop = any(not self.iteration_progress.get(cid, {}).get('done', False)
                                  and set(binding['task_refs']) & external
                                  for cid, binding in self.iteration_bindings.items())
            if not unfinished_loop and all(self.tasks[p] in DONE for p in external & self.task_ids) and not (
                    external & (self.decision_ids - set(self.decisions))):
                return self._packet('evaluate', {'branch': b, 'context': self.context(),
                    'completed_tasks': sorted(k for k, v in self.tasks.items() if v in DONE),
                    'prerequisites': sorted(external)})
        if any(v not in DONE | {'SKIPPED_INACTIVE_BRANCH'} for v in self.tasks.values()):
            self.lifecycle = 'RUN_HELD'
            self.outcome = 'USER_DECISION_REQUIRED' if any(self.unresolved_for(t) for t in self.task_ids
                                                          if self.active(t) is True) else None
            self.hold_reason = {'reason': 'Unresolved required dependency',
                                'target_ids': sorted({u for t in self.task_ids if self.active(t) is True
                                                      for u in self.unresolved_for(t)}),
                                'blocked_tasks': {t: s for t, s in self.tasks.items()
                                                  if s not in DONE | {'SKIPPED_INACTIVE_BRANCH'}},
                                'next_action': 'Supply explicit user event for target IDs, or required host evidence/capability.'}
            return None
        if not self.final:
            return self._packet('finalize', {'contract': self.ir, 'context': self.context(),
                                'task_receipts': self.receipts, 'branches': self.branches})
        self._postflight()
        return None

    def submit(self, response):
        action = self.next_action()
        require(action is not None, 'No pending action')
        require(response.get('action_sha256') == action['action_sha256'], 'Stale/substituted action response')
        # Validate and commit atomically. Rejected receipts cannot partially add evidence.
        trial = copy.deepcopy(self)
        trial._submit(action, copy.deepcopy(response))
        trial._issued = None
        self.__dict__.update(trial.__dict__)
        self._record('response', response)

    def _submit(self, action, response):
        try:
            jsonschema.Draft202012Validator(schema('host_response.schema.json')).validate(response)
        except jsonschema.ValidationError as e:
            raise Invalid('Host response schema: ' + e.message[:500]) from e
        role = action['role']
        if response.get('blocked'):
            require(response['blocked'] in {'BLOCKED_EVIDENCE', 'BLOCKED_CAPABILITY'}, 'Invalid block reason')
            require(isinstance(response.get('reason'), str) and response['reason'], 'Block explanation required')
            if role == 'execute':
                self.tasks[action['payload']['task']['id']] = response['blocked']
            self.lifecycle = 'RUN_HELD'
            self.hold_reason = {'reason': response['reason'], 'target_ids': [],
                                'blocked_tasks': self.tasks.copy(), 'next_action': 'Provide required source/capability and continue.'}
            return
        if role == 'execute':
            self._validate_task(action, response)
            self.pending = {'kind': 'task', 'task_id': response['task_id'], 'response': response}
        elif role == 'evaluate':
            self._validate_branch(action, response)
            self.pending = {'kind': 'branch', 'response': response}
        elif role == 'control':
            self._validate_control(action, response)
            self.pending = {'kind': 'control', 'response': response}
        elif role == 'finalize':
            self._validate_final(response)
            self.pending = {'kind': 'final', 'response': response}
        elif role == 'challenge':
            require(set(response) == {'action_sha256', 'verdict', 'findings', 'reviewed_sha256'}, 'Challenge fields')
            require(response['reviewed_sha256'] == sha(canonical(self.pending)), 'Challenge proposal binding')
            require(response['verdict'] in {'PASS', 'CHALLENGE'} and isinstance(response['findings'], list),
                    'Structured challenge required')
            require((response['verdict'] == 'PASS') == (len(response['findings']) == 0), 'False challenge PASS')
            if response['verdict'] == 'CHALLENGE':
                self._repair(response['findings'])
            else:
                self._commit_pending()
                self.challenge = copy.deepcopy(response)
        else:
            raise Invalid('Unknown action role')

    def _validate_task(self, action, r):
        fields = {'action_sha256', 'task_id', 'status', 'input_dependency_ids', 'evidence', 'claims',
                  'artifacts', 'evidence_accounting', 'limitations', 'executor', 'selected_subject_ref',
                  'requirement_checks', 'iteration_coverage', 'started_at', 'completed_at'}
        require(set(r) == fields, 'Task receipt fields mismatch')
        tid = action['payload']['task']['id']
        require(r['task_id'] == tid and self.ready(tid), 'Task not eligible')
        require(r['status'] in DONE and isinstance(r['limitations'], list) and r['executor'], 'Task completion shape')
        require(isinstance(r['executor'], dict) and set(r['executor']) == {'role', 'version'}
                and all(isinstance(v, str) and v for v in r['executor'].values()), 'Executor role/version required')
        start_time, end_time = datetime.fromisoformat(r['started_at']), datetime.fromisoformat(r['completed_at'])
        require(start_time.tzinfo is not None and end_time.tzinfo is not None and start_time <= end_time,
                'Task timestamps require timezone and legal order')
        require(set(r['input_dependency_ids']) == self.prerequisites(tid), 'Dependency receipt mismatch')
        require(self.executions < 1000, 'Task execution cap')
        if r['status'] == 'COMPLETED_WITH_LIMITATIONS':
            require(r['limitations'], 'Limitations required')
        known = set(self.index) | set(self.runtime_candidates())
        evidence = copy.deepcopy(self.evidence)
        for e in r['evidence']:
            ef = {'evidence_id', 'source_id', 'subject_refs', 'candidate_refs', 'task_refs',
                  'supported_claim', 'locator', 'limitations'}
            require(set(e) in (ef, ef | {'segment_refs'}), 'Evidence fields mismatch')
            require(e['evidence_id'] and e['evidence_id'] not in evidence, 'Duplicate evidence ID')
            require(e['source_id'] in self.sources, 'Unobserved source / fabricated tool success')
            require(e['subject_refs'] and set(e['subject_refs']) <= known, 'Unknown/empty evidence subject')
            require(set(e['candidate_refs']) <= set(e['subject_refs']) and e['task_refs'] == [tid], 'Evidence candidate/task mismatch')
            require(e['supported_claim'] and e['locator'], 'Evidence claim/locator required')
            source = self.sources[e['source_id']]
            if 'segment_refs' in e:
                require(e['segment_refs'] and e['source_id'] in self.reference_texts,
                        'Segment evidence requires a bound reference rendition')
                for segment in e['segment_refs']:
                    self.reference_pages(e['source_id'], segment, segment)
            require(set(e['subject_refs']) <= set(source['subject_refs']),
                    'Evidence/source subject contamination')
            evidence[e['evidence_id']] = e
        require(len(evidence) <= 5000, 'Evidence count cap')
        claims = copy.deepcopy(self.claims)
        source_subjects = {x for s in self.sources.values() for x in s.get('subject_refs', [])}
        for claim in r['claims']:
            base_fields = {'claim_id', 'subject_ref', 'text', 'evidence_ids', 'derivation_type', 'limitations'}
            require(set(claim) in (base_fields, base_fields | {'premise_claim_ids', 'attributed_to'}),
                    'Claim fields mismatch')
            require(claim['claim_id'] and claim['claim_id'] not in claims and claim['text'], 'Duplicate/empty claim')
            require(claim['subject_ref'] in known and claim['derivation_type'] in DERIVATIONS, 'Claim subject/derivation')
            require(set(claim['evidence_ids']) <= set(evidence), 'Fabricated evidence ID')
            if claim['derivation_type'] not in {'ASSUMPTION', 'SCENARIO', 'SYNTHESIS'}:
                require(claim['evidence_ids'], 'Evidence required for observation/evaluation/calculation')
            if claim['derivation_type'] in {'ASSUMPTION', 'SCENARIO'}:
                require(claim['limitations'], 'Assumption/scenario must be labeled')
            if 'premise_claim_ids' in claim:
                require(claim['derivation_type'] == 'SYNTHESIS' and claim['attributed_to'] == 'EXECUTOR',
                        'Derived integration must be explicitly attributed to executor')
                require(claim['premise_claim_ids'] and set(claim['premise_claim_ids']) <= set(claims),
                        'Unknown/forward/cyclic synthesis premise')
                if claim['subject_ref'] in source_subjects:
                    require(all(claims[x]['subject_ref'] == claim['subject_ref'] for x in claim['premise_claim_ids']),
                            'Cross-source synthesis cannot masquerade as a source-specific claim')
            for eid in claim['evidence_ids']:
                e = evidence[eid]
                require(claim['subject_ref'] in e['subject_refs'], 'Cross-subject evidence contamination')
                if e['candidate_refs']:
                    require(claim['subject_ref'] in e['candidate_refs'], 'Cross-candidate evidence contamination')
            claims[claim['claim_id']] = claim
        require(len({c['claim_id'] for c in r['claims']}) == len(r['claims']), 'Duplicate claim ID')
        self._validate_selection(r['selected_subject_ref'], tid)
        required = {e['id']: e for e in self.ir['evidence_requirements'] if e['dependent_ref'] == tid}
        require(set(r['evidence_accounting']) == set(required), 'Missing evidence requirement accounting')
        for eid, a in r['evidence_accounting'].items():
            require(set(a) in ({'status', 'evidence_ids', 'limitations'},
                              {'status', 'evidence_ids', 'limitations', 'claim_ids'}) and a['status'] in EVIDENCE_STATES,
                    'Evidence satisfaction shape')
            require(set(a['evidence_ids']) <= set(evidence), 'Unknown accounting evidence')
            if a['status'] == 'SATISFIED':
                require(a['evidence_ids'] or a.get('claim_ids'), 'Empty evidence cannot satisfy requirement')
            else:
                require(a['limitations'], 'Missing evidence disclosure')
            for x in a['evidence_ids']:
                require(required[eid]['subject_ref'] in evidence[x]['subject_refs'], 'Requirement subject contamination')
            for x in a.get('claim_ids', []):
                require(x in claims and claims[x]['subject_ref'] == required[eid]['subject_ref'],
                        'Requirement claim subject contamination')
                stack, roots, visited = [x], set(), set()
                while stack:
                    cid = stack.pop()
                    if cid in visited:
                        continue
                    visited.add(cid)
                    roots.update(claims[cid]['evidence_ids'])
                    stack.extend(claims[cid].get('premise_claim_ids', []))
                require(roots or a['status'] != 'SATISFIED', 'Unsupported synthesis cannot satisfy evidence')
        props = {p['id']: p for p in self.ir['propositions'] if self.active(p['id']) is True
                 and self.task_scope_applies(p['id'], tid)
                 and p['modality'] in {'REQUIRED', 'PROHIBITED'}}
        require(set(r['requirement_checks']) == set(props), 'Hard requirement accounting missing')
        for pid, check in r['requirement_checks'].items():
            require(set(check) == {'contract_object', 'status', 'claim_ids', 'limitations'}, 'Requirement check fields')
            require(canonical(check['contract_object']) == canonical(props[pid]['object']), 'Altered hard requirement value')
            require(check['status'] in EVIDENCE_STATES and check['limitations'] is not None, 'Requirement status')
            require(set(check['claim_ids']) <= set(self.claims) | {c['claim_id'] for c in r['claims']},
                    'Unknown requirement claim')
        require(isinstance(r['iteration_coverage'], dict), 'Iteration coverage shape')
        for cid, refs in r['iteration_coverage'].items():
            c = self.index.get(cid, {})
            require(c in self.ir['iteration_controls'] and c['mode'] == 'OVER_COLLECTION', 'Unknown collection control')
            members = set(self.index[c['collection_ref']]['members'])
            require(set(refs) <= members | set(self.runtime_candidates()), 'Unknown iteration member')
            require(set(refs) <= {c['subject_ref'] for c in r['claims']},
                    'Iteration member coverage requires a produced claim per member')
        require(r['artifacts'], 'Completion requires work product artifact')
        for artifact in r['artifacts']:
            require(set(artifact) in ({'artifact_id', 'path', 'media_type', 'content', 'role'},
                                     {'artifact_id', 'path', 'media_type', 'content', 'role', 'encoding'}), 'Artifact fields')
            from .io import safe_name
            safe_name(artifact['path'])
            require(artifact['path'].startswith('artifacts/') and artifact['artifact_id'] not in self.artifacts,
                    'Unsafe/duplicate artifact')
            require(artifact['artifact_id'] != 'RESULT', 'RESULT is reserved for the final assembled artifact')
            require(isinstance(artifact['content'], str) and 0 < len(artifact['content'].encode()) <= MAX_FILE,
                    'Empty/oversized output')
            artifact_bytes(artifact)
            require(artifact['path'] not in {a['path'] for a in self.artifacts.values()}, 'Artifact path collision')
        require(len({a['path'] for a in r['artifacts']}) == len(r['artifacts']) and
                len({a['artifact_id'] for a in r['artifacts']}) == len(r['artifacts']), 'Duplicate proposed artifact')

    def runtime_candidates(self):
        return {k: v for k, v in self.sources.items() if v.get('candidate_set_ref')}

    def discover(self, candidate_id, candidate_set_ref, label, source_id):
        record = {'candidate_id': candidate_id, 'candidate_set_ref': candidate_set_ref,
                  'label': label, 'source_id': source_id}
        self._discover(record)
        self._record('discover', record)

    def _discover(self, r):
        c = self.index.get(r['candidate_set_ref'], {})
        require(c in self.ir['candidate_sets'] and c.get('generation_rule'), 'Candidate discovery unauthorized')
        require(r['source_id'] in self.sources and r['candidate_id'] not in self.index and
                r['candidate_id'] not in self.sources and r['label'], 'Candidate identity/provenance')
        require(r['candidate_set_ref'] in self.sources[r['source_id']]['subject_refs'],
                'Discovery source must bind the authorized candidate set')
        self.sources[r['candidate_id']] = copy.deepcopy(r)
        self.sources[r['source_id']]['subject_refs'].append(r['candidate_id'])

    def _validate_selection(self, subject, tid):
        if subject is None:
            return
        require(subject in self.index or subject in self.runtime_candidates(), 'Unknown selected subject')
        # Selection never resolves USER slots. Unresolved final choice is withheld;
        # recommendation can remain in text with its distinct authority.
        require(not self.decision_ids - set(self.decisions), 'USER_ONLY selection withheld')
        require(self.index[tid]['kind'] in {'SELECT', 'RECOMMEND', 'RANK', 'EVALUATE'}, 'Unauthorized selection task')
        if self.decisions:
            values = list(self.decisions.values())
            require(subject in values or any(isinstance(v, dict) and subject in v.values() for v in values),
                    'Selection differs from explicit user value')

    def _validate_branch(self, action, r):
        require(set(r) == {'action_sha256', 'branch_id', 'activate', 'task_ids', 'evidence_ids', 'rationale'},
                'Branch response fields')
        require(r['branch_id'] == action['payload']['branch']['id'] and type(r['activate']) is bool,
                'Unauthorized branch')
        require(r['task_ids'] and set(r['task_ids']) <= {k for k, v in self.tasks.items() if v in DONE},
                'Branch requires completed-task citations')
        require(set(r['evidence_ids']) <= set(self.evidence) and r['rationale'], 'Invalid branch evidence/rationale')
        require(set(action['payload']['prerequisites']) & self.task_ids <= set(r['task_ids']),
                'Branch prerequisite citations missing')
        group = self.index[r['branch_id']].get('exclusivity_group')
        if group and r['activate']:
            require(not any(self.branches.get(b['id']) is True and b.get('exclusivity_group') == group
                            for b in self.ir['branches']), 'Mutually exclusive branches both active')

    def _validate_control(self, action, r):
        require(set(r) == {'action_sha256', 'control_id', 'proceed', 'rationale', 'count', 'member_refs'},
                'Control response fields')
        c = action['payload']['control']
        require(r['control_id'] == c['id'] and type(r['proceed']) is bool and r['rationale'], 'Control identity')
        if c['mode'] == 'BOUNDED_COUNT':
            require(type(r['count']) is int and r['count'] == c['count'], 'Iteration count altered')
        if c['mode'] == 'UNTIL_CONDITION' and 'completed_round' in action['payload']:
            require(r['count'] == action['payload']['completed_round'] and not r['member_refs'],
                    'Stop judgment must bind completed round')
        if c['mode'] == 'OVER_COLLECTION':
            require(set(r['member_refs']) == set(self.index[c['collection_ref']]['members']), 'Iteration members altered')

    def _validate_final(self, r):
        require(set(r) == {'action_sha256', 'analytical_outcome', 'result', 'output_artifact_ids',
                          'evidence_limitations', 'iteration_coverage'}, 'Final response fields')
        require(r['analytical_outcome'] in self.ir['result_policy']['allowed_states'], 'Outcome not contract-authorized')
        unresolved = self.decision_ids - set(self.decisions)
        if unresolved:
            require(r['analytical_outcome'] == 'USER_DECISION_REQUIRED', 'Unresolved endpoint USER_ONLY')
        require(isinstance(r['result'], str) and 0 < len(r['result'].encode()) <= MAX_FILE, 'Finished result required')
        require(set(r['output_artifact_ids']) == {o['id'] for o in self.ir['outputs']}, 'Output accounting missing')
        for aids in r['output_artifact_ids'].values():
            require(aids and set(aids) <= set(self.artifacts) | {'RESULT'}, 'Output artifact absent')
        gaps = [eid for rec in self.all_task_receipts() for eid, a in rec['evidence_accounting'].items()
                if a['status'] != 'SATISFIED']
        require(set(gaps) <= set(r['evidence_limitations']), 'Evidence gaps omitted')
        if gaps:
            require(r['analytical_outcome'] != 'DETERMINED', 'Missing required evidence cannot support determination')
        hard_gaps = [pid for rec in self.all_task_receipts() for pid, c in rec['requirement_checks'].items()
                     if c['status'] in {'UNSATISFIED', 'PARTIALLY_SATISFIED'}]
        require(not hard_gaps or r['analytical_outcome'] != 'DETERMINED', 'Unmet hard requirement blocks determination')
        for c in self.ir['iteration_controls']:
            if c['mode'] == 'OVER_COLLECTION':
                expected = set(self.index[c['collection_ref']]['members'])
                require(set(r['iteration_coverage'].get(c['id'], [])) == expected,
                        'Collection coverage incomplete')
                produced = {ref for rec in self.receipts.values()
                            for ref in rec['iteration_coverage'].get(c['id'], [])}
                require(expected <= produced, 'Final coverage has no task-produced member work')

    def _commit_pending(self):
        p, r = self.pending, self.pending['response']
        if p['kind'] == 'iteration_binding':
            self.iteration_bindings[r['control_id']] = copy.deepcopy(r)
        elif p['kind'] == 'task':
            tid = r['task_id']
            self.receipts[tid] = dict(copy.deepcopy(r), evidence_ids=[e['evidence_id'] for e in r['evidence']],
                                      produced_claim_ids=[c['claim_id'] for c in r['claims']],
                                      produced_artifact_ids=[a['artifact_id'] for a in r['artifacts']])
            self.tasks[tid] = r['status']
            self.evidence.update({e['evidence_id']: copy.deepcopy(e) for e in r['evidence']})
            self.claims.update({c['claim_id']: copy.deepcopy(c) for c in r['claims']})
            self.artifacts.update({a['artifact_id']: dict(copy.deepcopy(a), producing_task_ids=[tid]) for a in r['artifacts']})
            self.executions += 1
        elif p['kind'] == 'branch':
            self.branches[r['branch_id']] = r['activate']
        elif p['kind'] == 'control':
            cid = r['control_id']
            if cid in self.iteration_bindings and cid in self.controls:
                # UNTIL_CONDITION: semantic stop assessment after a reviewed round.
                if r['proceed']:
                    self._next_round(cid)
                else:
                    self.iteration_progress[cid]['done'] = True
                self.controls[cid] = copy.deepcopy(r)
                self.pending = None
                return
            self.controls[r['control_id']] = copy.deepcopy(r)
            if cid in self.iteration_bindings and r['proceed']:
                self.iteration_progress[cid] = {'round': 1, 'rounds': [], 'done': False}
                if self.index[cid].get('count') == 0:
                    require(False, 'Zero-count body requires explicit skip semantics; unsupported')
            if not r['proceed']:
                self.lifecycle = 'RUN_HELD'
                self.hold_reason = {'reason': r['rationale'], 'target_ids': [r['control_id']],
                                    'blocked_tasks': self.tasks.copy(), 'next_action': 'Stop condition enforced; inspect control.'}
        else:
            self.final = copy.deepcopy(r)
        self.pending = None

    def _repair(self, findings):
        require(self.repair_count < 2, 'Internal repair budget exhausted')
        self.repair_count += 1
        self.last_errors = copy.deepcopy(findings)
        self._reset_work()

    def reject(self, message):
        self._repair([str(message)])
        self._record('repair', str(message))

    def continue_host(self):
        require(self.lifecycle == 'RUN_HELD' and not self.failure, 'Only held runs may continue')
        self.lifecycle, self.hold_reason = 'RUNNING', None
        self._record('continue', {})

    def fail(self, error):
        self.lifecycle, self.outcome = 'RUN_FAILED', None
        self.failure = str(error)
        self._record('failure', self.failure)

    def _postflight(self):
        self._refresh()
        require(self.final and not self.pending and self.challenge and self.challenge['verdict'] == 'PASS',
                'Final structured challenge required')
        require(all(s in DONE | {'SKIPPED_INACTIVE_BRANCH'} for s in self.tasks.values()), 'Required task pending')
        require(set(self.receipts) == {t for t, s in self.tasks.items() if s in DONE}, 'Task receipt accounting')
        require(self.decisions == {e['target_id']: e['value'] for e in self.events}, 'USER_ONLY event accounting')
        require(all(self.active(t) is False for t, s in self.tasks.items() if s == 'SKIPPED_INACTIVE_BRANCH'),
                'Illegal branch skip')
        require(all(p['done'] for p in self.iteration_progress.values()), 'Repeated body incomplete')
        for cid, progress in self.iteration_progress.items():
            control = self.index[cid]
            require(progress['rounds'] and len(progress['rounds']) == progress['round'],
                    'Iteration history incomplete')
            if control['mode'] == 'BOUNDED_COUNT':
                require(len(progress['rounds']) == control['count'], 'Repeated execution count mismatch')
            else:
                require(self.controls[cid]['proceed'] is False, 'Until stop judgment absent')
        self._validate_final(self.final)
        self.lifecycle, self.outcome = 'RUN_RELEASED', self.final['analytical_outcome']

    def state(self):
        return {'run_id': self.run_id, 'contract_sha256': self.contract.sha256,
                'lifecycle_state': self.lifecycle, 'analytical_outcome': self.outcome,
                'tasks': self.tasks, 'branches': self.branches, 'user_decisions': self.decisions,
                'repair_count': self.repair_count, 'executions': self.executions,
                'hold_reason': self.hold_reason, 'failure': self.failure,
                'journal_head': self.journal[-1]['entry_hash'] if self.journal else None}


def drive(session, adapter):
    try:
        while (action := session.next_action()) is not None:
            try:
                session.submit(adapter.respond(action))
            except (Invalid, KeyError, TypeError, ValueError) as e:
                session.reject(str(e))
    except Exception as e:
        session.fail(e)
    return session


def artifact_bytes(artifact):
    encoding = artifact.get('encoding', 'UTF8')
    require(encoding in {'UTF8', 'BASE64'}, 'Unsupported artifact encoding')
    data = (artifact['content'].encode('utf-8') if encoding == 'UTF8' else
            base64.b64decode(artifact['content'], validate=True))
    require(0 < len(data) <= MAX_FILE, 'Artifact byte resource cap')
    return data


def start(preflight_pass: PreflightResult, host_adapter=None):
    require(preflight_pass.status == 'PASS' and preflight_pass.contract, 'Preflight PASS required')
    session = Session(preflight_pass.contract, input_hashes=preflight_pass.input_hashes)
    return drive(session, host_adapter) if host_adapter else session


def resume(held_state, runtime_user_event, host_adapter=None):
    from .artifacts import restore
    session = restore(held_state)
    require(session.lifecycle == 'RUN_HELD', 'Resume requires verified held state')
    session.user_event(runtime_user_event['target_id'], runtime_user_event['value'])
    return drive(session, host_adapter) if host_adapter else session
