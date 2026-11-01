"""pfrun CLI with a file exchange adapter for the ChatGPT Project host."""
import argparse
import json
from pathlib import Path
import sys
from .contract import preflight
from .engine import start, resume
from .artifacts import export, restore, verify
from .io import loads, read_file, require, verify_hash_inventory, members

EXITS = {'RUN_RELEASED': 0, 'RUN_HELD': 10, 'RUN_REJECTED': 20, 'RUN_FAILED': 50}


def main(argv=None):
    p = argparse.ArgumentParser(prog='pfrun')
    sub = p.add_subparsers(dest='command', required=True)
    for cmd in ['preflight', 'verify', 'inspect', 'self-check']:
        x = sub.add_parser(cmd)
        if cmd != 'self-check':
            x.add_argument('input')
    for cmd in ['run', 'resume', 'step']:
        x = sub.add_parser(cmd)
        x.add_argument('input')
        x.add_argument('--out', required=True)
        if cmd == 'run':
            x.add_argument('--adapter', choices=['project'], default='project')
        if cmd == 'resume':
            x.add_argument('--user-event', required=True)
        if cmd == 'step':
            x.add_argument('--response')
            x.add_argument('--source', help='Host observation descriptor JSON with source_id, path, kind, locator, subject_refs')
            x.add_argument('--candidate', help='Trusted host discovery descriptor JSON')
            x.add_argument('--iteration-binding', help='Explicit host execution-plan JSON: control_id, task_refs, basis')
            x.add_argument('--reference-text', help='Trusted extraction JSON: source_id, segments, extraction_method')
    a = p.parse_args(argv)
    try:
        if a.command == 'self-check':
            import jsonschema
            from lxml import etree
            from .io import schema
            for name in ['semantic_ir.schema.json', 'runner_receipt.schema.json', 'execution_state.schema.json',
                         'evidence_ledger.schema.json', 'runtime_user_event.schema.json', 'host_response.schema.json']:
                jsonschema.Draft202012Validator.check_schema(schema(name))
            etree.XMLSchema(etree.parse(str(Path(__file__).parent / 'schemas/contract.xsd')))
            print(json.dumps({'status': 'PASS', 'runner_version': '1.0.0'}))
            return 0
        if a.command == 'preflight':
            r = preflight(a.input)
            print(json.dumps({'status': r.status, 'diagnostics': r.diagnostics,
                              'contract_sha256': r.contract.sha256 if r.contract else None}, indent=2))
            return 0 if r.status == 'PASS' else 20
        if a.command == 'verify':
            r = verify(a.input)
            print(json.dumps(r, indent=2))
            return 0 if r['status'] == 'VERIFIED' else 40
        if a.command == 'inspect':
            print(json.dumps(restore(a.input).state(), indent=2))
            return 0
        if a.command == 'run':
            r = preflight(a.input)
            if r.status != 'PASS':
                out = Path(a.out)
                require(not out.exists(), 'Output exists')
                out.mkdir(parents=True)
                (out / 'preflight_diagnostics.json').write_text(json.dumps({'lifecycle_state': 'RUN_REJECTED',
                                                                            'diagnostics': r.diagnostics}, indent=2))
                print('RUN_REJECTED')
                return 20
            s = start(r)
        elif a.command == 'resume':
            s = resume(a.input, loads(read_file(a.user_event)))
        else:
            s = restore(a.input)
            if s.lifecycle == 'RUN_HELD':
                s.continue_host()
            if a.source:
                desc = loads(read_file(a.source))
                data = read_file(desc.pop('path'))
                s.observe(data=data, **desc)
            if a.candidate:
                s.discover(**loads(read_file(a.candidate)))
            if a.iteration_binding:
                s.bind_iteration(**loads(read_file(a.iteration_binding)))
            if a.reference_text:
                s.attach_reference_text(**loads(read_file(a.reference_text)))
            if a.response:
                try:
                    s.submit(loads(read_file(a.response)))
                except (ValueError, KeyError, TypeError) as e:
                    try:
                        s.reject(str(e))
                    except ValueError:
                        s.fail(e)
        export(s, a.out, checkpoint=True)
        print(json.dumps({'lifecycle_state': s.lifecycle, 'analytical_outcome': s.outcome,
                          'output': str(Path(a.out).resolve()), 'hold_reason': s.hold_reason}, indent=2))
        return EXITS[s.lifecycle]
    except (ValueError, KeyError, TypeError, OSError) as e:
        print(json.dumps({'error': str(e)}), file=sys.stderr)
        return 30


if __name__ == '__main__':
    sys.exit(main())
