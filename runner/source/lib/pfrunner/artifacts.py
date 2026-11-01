"""Immutable run packaging and replay without model calls or Compiler imports."""
from pathlib import Path
import copy
import mimetypes
import jsonschema
from .io import canonical, sha, loads, require, members, safe_name, schema, verify_hash_inventory, IntegrityError
from .contract import parse
from .engine import Session, artifact_bytes


def pause(session):
    if session.lifecycle == 'RUNNING':
        action = session.next_action()
        if action:
            data = {'reason': 'Awaiting structured host response', 'target_ids': [],
                    'blocked_tasks': session.tasks.copy(),
                    'next_action': 'Use action_packet.json with the named host role, then submit response.'}
            session.lifecycle, session.hold_reason = 'RUN_HELD', data
            session._record('pause', data)
    return session


def product_files(session):
    files = {a['path']: artifact_bytes(a) for a in session.artifacts.values()}
    if session.lifecycle == 'RUN_RELEASED':
        files['result.md'] = session.final['result'].encode('utf-8')
    return files


def export(session, destination, *, checkpoint=False):
    """Write a new directory only; existing state is never overwritten."""
    action = copy.deepcopy(session.next_action())
    if checkpoint:
        pause(session)
    require(session.lifecycle in {'RUN_RELEASED', 'RUN_HELD', 'RUN_FAILED'}, 'Terminal/checkpoint state required')
    out = Path(destination)
    require(not out.exists(), 'Output directory already exists; use a new directory')
    files = product_files(session)
    artifact_rows = []
    for n, b in files.items():
        a = next((a for a in session.artifacts.values() if a['path'] == n), None)
        artifact_rows.append({'path': n, 'media_type': a['media_type'] if a else 'text/markdown',
                              'sha256': sha(b), 'bytes': len(b),
                              'producing_task_ids': a['producing_task_ids'] if a else sorted(session.receipts),
                              'role': a['role'] if a else 'primary_result'})
    receipt = {'runner_version': '1.0.0', 'run_id': session.run_id,
               'contract_sha256': session.contract.sha256, 'lifecycle_state': session.lifecycle,
               'analytical_outcome': session.outcome, 'task_summary': session.tasks,
               'branch_summary': session.branches, 'evidence_summary': {'records': len(session.evidence)},
               'user_only_summary': session.decisions, 'challenge': session.challenge or {},
               'postflight': {'status': 'PASS' if session.lifecycle == 'RUN_RELEASED' else 'NOT_RELEASED'},
               'artifacts': artifact_rows, 'input_hashes': session.input_hashes,
               'source_artifact_hashes': {k: v['sha256'] for k, v in session.sources.items() if 'sha256' in v},
               'runtime_event_chain_head': session.events[-1]['event_hash'] if session.events else None,
               'replay': {'mode': 'deterministic journal replay', 'semantic_truth_verified': False},
               'hold_reason': session.hold_reason, 'failure': session.failure}
    ledger = {'records': [dict(e, source_kind=session.sources[e['source_id']]['kind'],
                              source_title=session.sources[e['source_id']]['title'],
                              accessed_at=session.sources[e['source_id']]['accessed_at'],
                              published_at=session.sources[e['source_id']].get('published_at'),
                              effective_date=session.sources[e['source_id']].get('effective_date'),
                              source_sha256=session.sources[e['source_id']]['sha256'])
                          for e in session.evidence.values()]}
    files.update({'input_contract.xml': session.contract.xml,
                  'run_receipt.json': canonical(receipt), 'execution_state.json': canonical(session.state()),
                  'task_receipts.json': canonical(session.receipts), 'evidence_ledger.json': canonical(ledger),
                  'runtime_events.json': canonical(session.events), 'claims.json': canonical(session.claims),
                  'replay_journal.json': canonical({'run_id': session.run_id, 'input_hashes': session.input_hashes,
                                                   'entries': session.journal})})
    if session.iteration_bindings:
        files['iteration_execution.json'] = canonical({'bindings': session.iteration_bindings,
                                                       'progress': session.iteration_progress})
    if action:
        files['action_packet.json'] = canonical(action)
    jsonschema.validate(receipt, schema('runner_receipt.schema.json'))
    jsonschema.validate(session.state(), schema('execution_state.schema.json'))
    jsonschema.validate(ledger, schema('evidence_ledger.schema.json'))
    for e in session.events:
        jsonschema.validate(e, schema('runtime_user_event.schema.json'))
    manifest = {'format_version': '1.0', 'files': []}
    for n, b in sorted(files.items()):
        row = next((a for a in artifact_rows if a['path'] == n), None)
        manifest['files'].append(row or {'path': n, 'media_type': mimetypes.guess_type(n)[0] or 'application/octet-stream',
                                       'sha256': sha(b), 'bytes': len(b), 'producing_task_ids': [], 'role': 'audit'})
    files['artifact_manifest.json'] = canonical(manifest)
    files['HASHES.sha256'] = ''.join(f'{sha(b)}  {n}\n' for n, b in sorted(files.items())).encode()
    out.mkdir(parents=True)
    for n, b in files.items():
        target = out.joinpath(*safe_name(n))
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(b)
    # A package is deliverable only after its own independent replay from bytes.
    restore(out)
    return out


def restore(path):
    files = members(path)
    verify_hash_inventory(files)
    require('HASHES.sha256' in files, 'Run hash inventory required')
    manifest = loads(files['artifact_manifest.json'])
    expected = set(files) - {'HASHES.sha256', 'artifact_manifest.json'}
    require(len(manifest['files']) == len(expected) and {r['path'] for r in manifest['files']} == expected,
            'Run manifest inventory mismatch')
    for row in manifest['files']:
        require(sha(files[row['path']]) == row['sha256'] and len(files[row['path']]) == row['bytes'],
                'Artifact byte/hash mismatch')
    j = loads(files['replay_journal.json'])
    session = Session(parse(files['input_contract.xml']), j['run_id'], j['input_hashes'].items())
    session._replaying = True
    for entry in j['entries']:
        require(entry['previous_hash'] == (session.journal[-1]['entry_hash'] if session.journal else None),
                'Journal chain mismatch')
        require(entry['entry_hash'] == sha(canonical({k: v for k, v in entry.items() if k != 'entry_hash'})),
                'Journal entry hash mismatch')
        op, data = entry['op'], entry['data']
        if op == 'issue':
            action = session.next_action()
            require(action and action['action_sha256'] == data['action_sha256'], 'Issued action replay mismatch')
        elif op == 'response':
            action = session.next_action()
            require(action and action['action_sha256'] == data['action_sha256'], 'Replay action binding mismatch')
            session._submit(action, copy.deepcopy(data))
            session._issued = None
        elif op == 'observe':
            session._observe(data)
        elif op == 'iteration_binding':
            session._bind_iteration(data)
        elif op == 'reference_text':
            session._attach_reference_text(data)
        elif op == 'discover':
            session._discover(data)
        elif op == 'user':
            session.next_action()
            session._user(data)
        elif op == 'repair':
            session._repair([data])
        elif op == 'continue':
            require(session.lifecycle == 'RUN_HELD', 'Illegal continuation')
            session.lifecycle, session.hold_reason = 'RUNNING', None
        elif op == 'pause':
            require(session.next_action(), 'Illegal host pause')
            session.lifecycle, session.hold_reason = 'RUN_HELD', copy.deepcopy(data)
        elif op == 'failure':
            if session.lifecycle == 'RUNNING':
                try:
                    session.next_action()
                except Exception:
                    pass
            session.lifecycle, session.outcome, session.failure = 'RUN_FAILED', None, data
        else:
            raise IntegrityError('Unknown journal operation')
        session.journal.append(copy.deepcopy(entry))
    if session.lifecycle == 'RUNNING':
        session.next_action()
    session._replaying = False
    require(session.state() == loads(files['execution_state.json']), 'Replayed execution state mismatch')
    require(session.receipts == loads(files['task_receipts.json']), 'Replayed task receipt mismatch')
    require(session.events == loads(files['runtime_events.json']), 'Replayed user events mismatch')
    require(session.claims == loads(files['claims.json']), 'Replayed claims mismatch')
    if session.iteration_bindings:
        require(loads(files['iteration_execution.json']) == {'bindings': session.iteration_bindings,
                'progress': session.iteration_progress}, 'Iteration execution replay mismatch')
    ledger = loads(files['evidence_ledger.json'])
    expected_ledger = [dict(e, source_kind=session.sources[e['source_id']]['kind'],
                            source_title=session.sources[e['source_id']]['title'],
                            accessed_at=session.sources[e['source_id']]['accessed_at'],
                            published_at=session.sources[e['source_id']].get('published_at'),
                            effective_date=session.sources[e['source_id']].get('effective_date'),
                            source_sha256=session.sources[e['source_id']]['sha256']) for e in session.evidence.values()]
    require(ledger == {'records': expected_ledger}, 'Replayed evidence mismatch')
    receipt = loads(files['run_receipt.json'])
    jsonschema.validate(receipt, schema('runner_receipt.schema.json'))
    for k, v in [('run_id', session.run_id), ('contract_sha256', session.contract.sha256),
                 ('lifecycle_state', session.lifecycle), ('analytical_outcome', session.outcome),
                 ('task_summary', session.tasks), ('branch_summary', session.branches),
                 ('user_only_summary', session.decisions), ('challenge', session.challenge or {}),
                 ('runner_version', '1.0.0'), ('input_hashes', session.input_hashes),
                 ('source_artifact_hashes', {k: v['sha256'] for k, v in session.sources.items() if 'sha256' in v}),
                 ('evidence_summary', {'records': len(session.evidence)}),
                 ('runtime_event_chain_head', session.events[-1]['event_hash'] if session.events else None),
                 ('hold_reason', session.hold_reason), ('failure', session.failure),
                 ('replay', {'mode': 'deterministic journal replay', 'semantic_truth_verified': False})]:
        require(receipt[k] == v, 'Receipt replay mismatch: ' + k)
    require(receipt['postflight']['status'] == ('PASS' if session.lifecycle == 'RUN_RELEASED' else 'NOT_RELEASED'),
            'Forged postflight PASS')
    products = product_files(session)
    require({n: files[n] for n in products} == products, 'Replayed work product mismatch')
    require({r['path'] for r in receipt['artifacts']} == set(products), 'Receipt output inventory')
    for row in receipt['artifacts']:
        require(row['sha256'] == sha(products[row['path']]) and row['bytes'] == len(products[row['path']]),
                'Receipt output hash mismatch')
        a = next((v for v in session.artifacts.values() if v['path'] == row['path']), None)
        require(row['producing_task_ids'] == (a['producing_task_ids'] if a else sorted(session.receipts))
                and row['role'] == (a['role'] if a else 'primary_result')
                and row['media_type'] == (a['media_type'] if a else 'text/markdown'), 'Artifact provenance mismatch')
    return session


def verify(path):
    try:
        s = restore(path)
        return {'status': 'VERIFIED', 'run_id': s.run_id, 'lifecycle_state': s.lifecycle,
                'contract_sha256': s.contract.sha256, 'semantic_truth_verified': False}
    except (ValueError, OSError, KeyError, TypeError, jsonschema.ValidationError) as e:
        return {'status': 'INVALID', 'diagnostic': str(e)}
