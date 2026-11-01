"""Exact adapter for the released Compiler 1.0.0 JSON-in-XML renderer."""
from dataclasses import dataclass
from pathlib import Path
from collections import defaultdict
from datetime import date
from decimal import Decimal
import zipfile
import re
import jsonschema
from lxml import etree
from .io import Invalid, require, canonical, sha, loads, read_file, members, schema, verify_hash_inventory

SECTIONS = [('entities', 'Entities'), ('tasks', 'Tasks'), ('candidate_sets', 'CandidateSets'),
            ('propositions', 'Propositions'), ('branches', 'Branches'), ('dependencies', 'Dependencies'),
            ('evidence_requirements', 'EvidenceRequirements'), ('user_decisions', 'UserDecisions'),
            ('iteration_controls', 'IterationControls'), ('outputs', 'Outputs'), ('result_policy', 'ResultPolicy')]
COLLECTIONS = [k for k, _ in SECTIONS if k != 'result_policy']


@dataclass(frozen=True)
class ExecutionContractView:
    xml: bytes
    payload: bytes
    metadata: bytes

    @property
    def ir(self):
        return loads(self.payload)

    @property
    def identity(self):
        return loads(self.metadata)

    @property
    def sha256(self):
        return sha(self.xml)


@dataclass(frozen=True)
class PreflightResult:
    status: str
    contract: ExecutionContractView | None
    diagnostics: tuple
    input_hashes: tuple = ()


def acyclic(graph):
    colors = {}
    for root in list(graph):
        stack = [(root, False)]
        while stack:
            node, done = stack.pop()
            if done:
                colors[node] = 2
                continue
            require(colors.get(node) != 1, 'Graph cycle')
            if colors.get(node) == 2:
                continue
            colors[node] = 1
            stack.append((node, True))
            stack.extend((v, False) for v in graph.get(node, []))


def validate_structure(ir):
    jsonschema.Draft202012Validator(schema('semantic_ir.schema.json')).validate(ir)
    nodes = [n for k in COLLECTIONS for n in ir[k]]
    require(len(nodes) <= 10000, 'Node resource cap')
    index = {n['id']: n for n in nodes}
    require(len(index) == len(nodes) and 'GLOBAL' not in index, 'Duplicate/reserved ID')
    kinds = {n['id']: k for k in COLLECTIONS for n in ir[k]}
    def ref(v, allowed=None, global_ok=False):
        require(global_ok and v == 'GLOBAL' or v in index and (not allowed or kinds[v] in allowed),
                'Invalid reference: ' + str(v))
    scopes, graph = defaultdict(list), defaultdict(list)
    for n in nodes:
        for k in ['subject_ref', 'dependent_ref', 'predecessor_ref', 'successor_ref']:
            if k in n:
                ref(n[k])
        if 'scope_ref' in n:
            ref(n['scope_ref'], {'tasks', 'branches', 'candidate_sets'}, True)
            scopes[n['id']].append(n['scope_ref'])
        if n.get('condition_ref'):
            ref(n['condition_ref'], {'branches'})
        for k in ['members', 'dependent_refs', 'active_node_refs']:
            require(len(n.get(k, [])) == len(set(n.get(k, []))), 'Duplicate reference')
            for v in n.get(k, []):
                ref(v, {'entities'} if k == 'members' else None)
        if n.get('collection_ref'):
            ref(n['collection_ref'], {'candidate_sets'})
        for a in n.get('source_anchors', []):
            require(a['start'] < a['end'] and a['event_id'] == a['source_id'], 'Invalid source anchor')
        if n.get('authority') == 'USER':
            require(n.get('source_anchors'), 'USER authority lacks provenance')
        if n in ir['propositions']:
            validate_value(n['object'], index)
        if n in ir['iteration_controls']:
            require(n['mode'] != 'BOUNDED_COUNT' or n.get('count') is not None, 'Missing iteration count')
            require(n['mode'] != 'UNTIL_CONDITION' or n.get('stop_condition'), 'Missing stop condition')
            require(n['mode'] != 'OVER_COLLECTION' or n.get('collection_ref'), 'Missing iteration collection')
    for e in ir['dependencies']:
        graph[e['predecessor_ref']].append(e['successor_ref'])
    acyclic(graph)
    acyclic(scopes)
    for b in ir['branches']:
        for target in b['active_node_refs']:
            n = index[target]
            require(n.get('scope_ref') == b['id'] or n.get('condition_ref') == b['id'], 'Branch scope mismatch')
    for d in ir['user_decisions']:
        require('USER_DECISION_REQUIRED' in ir['result_policy']['allowed_states'], 'USER_ONLY policy')
        require(set(d['dependent_refs']) <= set(graph[d['id']]), 'USER_ONLY dependency missing')
    # Only executable predecessors can establish ordering. Unknown node obligations
    # remain explicit compatibility diagnostics, never implicitly marked complete.
    return index


def validate_value(v, index):
    k, value = v['kind'], v['value']
    if k in {'NUMBER', 'MONEY', 'PERCENT', 'QUANTITY', 'DURATION'}:
        require(not isinstance(value, bool) and isinstance(value, (int, float, str)), 'Numeric payload required')
        require(Decimal(str(value)).is_finite(), 'Nonfinite scalar')
        require(k not in {'QUANTITY', 'DURATION'} or v.get('unit'), 'Missing unit')
        require(k != 'MONEY' or v.get('currency'), 'Missing currency')
        if v.get('normalization'):
            n = v['normalization']
            require(Decimal(n['input']) * Decimal(n['multiplier']) + Decimal(n['offset']) == Decimal(str(value)),
                    'False normalization claim')
    elif k == 'BOOLEAN':
        require(type(value) is bool, 'Boolean payload required')
    elif k == 'DATE':
        require(isinstance(value, str) and date.fromisoformat(value).isoformat() == value, 'ISO date required')
    elif k == 'ENTITY_REF':
        require(isinstance(value, str) and value in index and 'type' in index[value], 'Entity reference required')
    elif k == 'SET':
        require(isinstance(value, list), 'Typed set required')
        for child in value:
            validate_value(child, index)
    elif k == 'RANGE':
        require(isinstance(value, dict) and set(value) == {'min', 'max'} and value['min'] <= value['max'], 'Invalid range')
    elif k == 'NULL':
        require(value is None, 'NULL must be null')
    elif k in {'TEXT', 'SYMBOL'}:
        require(isinstance(value, str), 'String payload required')


def parse(xml):
    require(len(xml) <= 16_000_000 and b'<!DOCTYPE' not in xml.upper() and b'<!ENTITY' not in xml.upper(),
            'XML resource cap / DTD / entity forbidden')
    parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False)
    r = etree.fromstring(xml, parser)
    require(not r.getroottree().docinfo.doctype, 'DTD forbidden regardless of encoding')
    etree.XMLSchema(etree.parse(str(Path(__file__).parent / 'schemas/contract.xsd'), parser)).assertValid(r)
    require((r.get('contract_version'), r.get('compiler_version'), r.get('ir_version')) ==
            ('1.0', '1.0.0', '1.0'), 'Unsupported version')
    for k in ['source_state_sha256', 'verified_ir_sha256']:
        require(re.fullmatch('[0-9a-f]{64}', r.get(k)), 'Invalid identity hash')
    ir = {'objective': r.findtext('Objective'), 'ir_version': r.get('ir_version'),
          'source_state_sha256': r.get('source_state_sha256')}
    for k, tag in SECTIONS:
        values = [loads(n.text or '') for n in r.find(tag)]
        if k == 'result_policy':
            require(len(values) == 1, 'Expected one result policy')
            ir[k] = values[0]
        else:
            ir[k] = values
    validate_structure(ir)
    # Exact IR reconstruction is possible for THIS renderer: all IR fields are
    # emitted as canonical Node payloads, plus objective and two root attributes.
    require(sha(canonical(ir)) == r.get('verified_ir_sha256'), 'Reconstructed IR hash mismatch')
    require(r.get('contract_id') == 'PF-' + r.get('verified_ir_sha256'), 'Contract ID mismatch')
    anchors = {canonical(a) for k in COLLECTIONS for n in ir[k] for a in n.get('source_anchors', [])}
    require([canonical(loads(n.text or '')) for n in r.find('Provenance')] == sorted(anchors),
            'Provenance inventory mismatch')
    return ExecutionContractView(bytes(xml), canonical(ir), canonical(dict(r.attrib)))


def preflight(path):
    try:
        p = Path(path)
        files = {'contract.xml': read_file(p)} if p.is_file() and p.suffix.lower() == '.xml' else members(p)
        verify_hash_inventory(files)
        candidates = [n for n in files if Path(n).name == 'contract.xml']
        require(len(candidates) == 1, 'Expected exactly one contract.xml')
        name = candidates[0]
        c = parse(files[name])
        receipt_name = str(Path(name).with_name('compiler_receipt.json')).replace('\\', '/')
        notes = ['Source provenance asserted by Compiler; original source events not independently reproduced.']
        if receipt_name in files:
            receipt = loads(files[receipt_name])
            jsonschema.validate(receipt, schema('compiler_receipt.schema.json'))
            require(receipt['status'] == 'COMPILE_RELEASED' and receipt['challenge_verdict'] == 'PASS',
                    'Compiler release required')
            require(receipt['contract_sha256'] == c.sha256, 'Compiler receipt contract hash mismatch')
            for k in ['source_state_sha256', 'verified_ir_sha256', 'compiler_version', 'ir_version', 'contract_version']:
                require(receipt[k] == c.identity[k], 'Receipt identity mismatch: ' + k)
            prefix = name[:-len('contract.xml')]
            require(set(receipt['artifacts']) == {'request_state.json', 'semantic_ir.json', 'contract.xml',
                    'portable_brief.txt', 'diagnostics.json', 'clarifications.json', 'semantic_audit.json'},
                    'Compiler release artifact inventory mismatch')
            for n, h in receipt['artifacts'].items():
                require(prefix + n in files and sha(files[prefix + n]) == h, 'Compiler artifact hash mismatch: ' + n)
            require(files[prefix + 'semantic_ir.json'] == c.payload, 'Compiler IR bytes differ from XML payload')
            require(sha(files[prefix + 'portable_brief.txt']) == receipt['portable_brief_sha256'], 'Portable brief hash mismatch')
            verify_source_state(loads(files[prefix + 'request_state.json']), c.ir)
            audit = loads(files[prefix + 'semantic_audit.json'])
            require(audit and audit[-1]['role'] == 'challenge' and
                    audit[-1]['candidate_sha256'] == c.identity['verified_ir_sha256'] and
                    audit[-1]['source_state_sha256'] == c.identity['source_state_sha256'] and
                    audit[-1]['output']['verdict'] == 'PASS' and audit[-1]['output']['findings'] == [],
                    'Compiler final challenge binding missing')
            notes = ['Original source events, authority spans and source-state hash independently verified.']
            notes.append('Compiler receipt and supplied artifact hashes verified.')
        else:
            notes.append('Bare XML: no external Compiler receipt binding supplied.')
        return PreflightResult('PASS', c, tuple(notes), tuple(sorted((n, sha(b)) for n, b in files.items())))
    except (ValueError, OSError, KeyError, TypeError, ArithmeticError, zipfile.BadZipFile, etree.Error, jsonschema.ValidationError) as e:
        return PreflightResult('RUN_REJECTED', None, (str(e),))


def verify_source_state(state, ir):
    events = state['events']
    require(events and len(events) <= 10000, 'Source event cap/empty state')
    known = {}
    for i, e in enumerate(events):
        require(set(e) == {'id', 'role', 'content', 'content_sha256', 'sequence', 'clarification_target'},
                'Source event fields')
        require(e['id'] and e['id'] not in known and e['sequence'] == i, 'Source event order/identity')
        require(e['role'] in {'USER_DIRECTIVE', 'USER_CLARIFICATION', 'REFERENCE_MATERIAL', 'SYSTEM_POLICY'},
                'Source role')
        require('\r' not in e['content'] and sha(e['content'].encode()) == e['content_sha256'], 'Source byte identity')
        require(e['role'] != 'USER_CLARIFICATION' or e['clarification_target'], 'Clarification target missing')
        known[e['id']] = e
    require(any(e['role'] == 'USER_DIRECTIVE' for e in events), 'Original directive absent')
    require(sha(canonical(events)) == state['source_state_sha256'] == ir['source_state_sha256'], 'Source-state hash mismatch')
    for k in COLLECTIONS:
        for n in ir[k]:
            user_anchor = False
            for a in n.get('source_anchors', []):
                e = known.get(a['source_id'])
                require(e and a['event_id'] == a['source_id'] and 0 <= a['start'] < a['end'] <= len(e['content'])
                        and sha(e['content'][a['start']:a['end']].encode()) == a['excerpt_sha256'], 'Source anchor mismatch')
                user_anchor |= e['role'] in {'USER_DIRECTIVE', 'USER_CLARIFICATION'}
            if n.get('authority', 'USER') == 'USER':
                require(user_anchor, 'USER provenance does not originate from a user event')
