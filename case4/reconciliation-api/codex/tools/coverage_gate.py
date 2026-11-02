"""Portable, intentionally narrow coverage-first gate for Python Codex jobs.

This file may be copied into Codex handoffs and invoked directly. It requires
coverage.py in the target environment. It does not depend on PEHAVOS imports.
It never asserts code correctness on the basis of coverage alone.
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile

POLICY_VERSION = 'PEHAVOS-COVERAGE-FIRST-1.2'
BANNED_MODULES = {'unittest.mock', 'mock', 'pytest_mock', 'pytest_mock.plugin', 'mockito', 'flexmock', 'doublex'}
BANNED_CALLS = {'patch', 'patch.object', 'patch.dict', 'mock.patch', 'unittest.mock.patch', 'monkeypatch.setattr', 'monkeypatch.setitem', 'monkeypatch.delattr', 'monkeypatch.delitem'}


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _dotted(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        left = _dotted(node.value)
        return left + '.' + node.attr if left else node.attr
    return ''


def _violations(path: Path) -> list[dict]:
    """Conservative AST check, including imports and common patch APIs.

    The check is not a proof that dynamic imports or custom mock mechanisms are
    absent. That requires human review, recorded separately.
    """
    try:
        tree = ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
    except (SyntaxError, UnicodeError) as exc:
        return [{'file': str(path), 'line': getattr(exc, 'lineno', 0), 'rule': 'INVALID_PYTHON'}]
    issues = []
    aliases: dict[str, str] = {}
    patch_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                aliases[a.asname or a.name.split('.')[0]] = a.name
                if a.name in BANNED_MODULES or a.name.startswith('unittest.mock.'):
                    issues.append({'file': str(path), 'line': node.lineno, 'rule': 'BANNED_IMPORT:' + a.name})
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ''
            if mod in BANNED_MODULES or mod.startswith('unittest.mock.'):
                issues.append({'file': str(path), 'line': node.lineno, 'rule': 'BANNED_IMPORT:' + mod})
            if mod == 'unittest' and any(a.name == 'mock' for a in node.names):
                issues.append({'file': str(path), 'line': node.lineno, 'rule': 'BANNED_IMPORT:unittest.mock'})
            for a in node.names:
                aliases[a.asname or a.name] = mod + '.' + a.name
                if mod in ('unittest.mock', 'mock') and a.name in ('patch', 'Mock', 'MagicMock'):
                    patch_names.add(a.asname or a.name)
        elif isinstance(node, ast.Call):
            name = _dotted(node.func)
            if name in BANNED_CALLS or name in patch_names or name.endswith('.monkeypatch') or name in ('Mock', 'MagicMock'):
                issues.append({'file': str(path), 'line': node.lineno, 'rule': 'BANNED_CALL:' + name})
            if name in ('getattr', 'setattr') and node.args:
                # Normal getattr and setattr are allowed; not synonymous with patching.
                pass
            if name.startswith('pytest.') and name.endswith('MonkeyPatch'):
                issues.append({'file': str(path), 'line': node.lineno, 'rule': 'BANNED_CALL:' + name})
    return issues


def _assertion_count(paths: list[Path]) -> int:
    count = 0
    for path in paths:
        try:
            tree=ast.parse(path.read_text(encoding='utf-8'))
        except (SyntaxError, UnicodeError):
            continue
        for node in ast.walk(tree):
            if isinstance(node, ast.Assert):
                count += 1
            elif isinstance(node, ast.Call):
                name=_dotted(node.func)
                if name.split('.')[-1].startswith('assert'):
                    count += 1
    return count


def run_gate(root: Path, sources: list[str], tests: str = 'tests', timeout: int = 180,
             output: Path | None = None) -> dict:
    root = Path(root).resolve(strict=True)
    if not root.is_dir() or not sources or not 1 <= timeout <= 3600:
        raise ValueError('valid root, first-party source list and timeout are required')
    if not re.fullmatch(r'[A-Za-z0-9_.\-/]+', tests) or tests.startswith('/') or '..' in Path(tests).parts:
        raise ValueError('unsafe test directory')
    test_dir = (root / tests).resolve(strict=True)
    if not test_dir.is_relative_to(root) or not test_dir.is_dir():
        raise ValueError('test directory must be inside the project')
    selected: list[Path] = []
    src_files: set[Path] = set()
    for source in sources:
        if not re.fullmatch(r'[A-Za-z0-9_.\-/]+', source) or source.startswith('/') or '..' in Path(source).parts:
            raise ValueError('unsafe first-party scope')
        src = (root / source).resolve(strict=True)
        if not src.is_relative_to(root) or not (src.is_file() and src.suffix == '.py' or src.is_dir()):
            raise ValueError('first-party scope is not a Python file or directory')
        selected.append(src)
        if src.is_dir():
            src_files.update(f for f in src.rglob('*.py') if f.is_file() and f.resolve().is_relative_to(root))
        else:
            src_files.add(src)
    if not src_files:
        raise ValueError('first-party scope contains no Python files')
    tests_files = sorted(test_dir.rglob('test*.py'))
    if not tests_files:
        raise ValueError('no test modules discovered')
    assertion_count=_assertion_count(tests_files)
    source_files = sorted(src_files)
    all_files = sorted(set(source_files) | {f for f in test_dir.rglob('*.py') if f.is_file()})
    forbidden = [issue for path in all_files for issue in _violations(path)]
    if forbidden:
        result = {'status':'FAIL', 'policy':POLICY_VERSION, 'reason':'BANNED_MOCK_OR_INVALID_PYTHON',
                  'violations':forbidden, 'first_party_scope':sources, 'coverage_pass':False}
        if output is not None:
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        return result
    source_hashes = {f.relative_to(root).as_posix():_sha(f) for f in all_files}
    if assertion_count == 0:
        result={'status':'FAIL','policy':POLICY_VERSION,'reason':'NO_ASSERTIONS_IN_TESTS',
                'coverage_pass':False,'source_hashes':source_hashes}
        if output is not None:
            output.parent.mkdir(parents=True,exist_ok=True)
            output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        return result
    try:
        import coverage  # type: ignore[import-not-found]
    except ImportError:
        return {'status':'BLOCKED', 'policy':POLICY_VERSION, 'reason':'coverage.py not installed',
                'coverage_pass':False, 'first_party_scope':sources, 'source_hashes':source_hashes}
    # Subprocess re-executes real tests; do not trust externally supplied coverage JSON.
    with tempfile.TemporaryDirectory(prefix='pehavos_coverage_') as tmp:
        temp = Path(tmp)
        config = temp/'coverage.ini'
        config.write_text('[run]\nbranch = True\nparallel = False\n[report]\nshow_missing = True\n',encoding='utf-8')
        data = temp/'.coverage'
        report = temp/'coverage.json'
        cmd = [sys.executable,'-m','coverage','run','--rcfile',str(config),
               '--data-file',str(data),'--branch','--source',','.join(str(s) for s in selected),
               '-m','unittest','discover','-s',str(test_dir),'-p','test*.py','-v']
        try:
            cp = subprocess.run(cmd,cwd=root,capture_output=True,text=True,timeout=timeout,check=False)
        except subprocess.TimeoutExpired:
            return {'status':'FAIL','policy':POLICY_VERSION,'reason':'TEST_TIMEOUT',
                    'coverage_pass':False,'source_hashes':source_hashes}
        log = (cp.stdout + '\n' + cp.stderr)[-25000:]
        match = re.search(r'Ran\s+(\d+)\s+tests?', log)
        cases = int(match.group(1)) if match else 0
        if cp.returncode or cases < 1:
            result = {'status':'FAIL','policy':POLICY_VERSION,'reason':'TESTS_FAILED_OR_ZERO',
                      'test_returncode':cp.returncode,'tests_run':cases,'test_log':log,
                      'coverage_pass':False,'source_hashes':source_hashes}
        else:
            export = subprocess.run([sys.executable,'-m','coverage','json','--rcfile',str(config),
                                     '--data-file',str(data),'-o',str(report)],
                                    cwd=root,capture_output=True,text=True,timeout=timeout,check=False)
            if export.returncode or not report.is_file():
                result={'status':'FAIL','policy':POLICY_VERSION,'reason':'COVERAGE_REPORT_FAILED',
                        'test_log':log,'coverage_pass':False,'source_hashes':source_hashes,
                        'report_stderr':export.stderr[-3000:]}
            else:
                detail = json.loads(report.read_text(encoding='utf-8'))
                files = detail.get('files', {})
                # Coverage filenames may be relative to root; all claimed first-party
                # Python files must be present in the report, including unimported ones.
                reported = {(root / name).resolve(): value for name,value in files.items()}
                missing_files = [p.relative_to(root).as_posix() for p in source_files if p not in reported]
                missed = {p.relative_to(root).as_posix():reported[p].get('missing_lines',[])
                          for p in source_files if p in reported and reported[p].get('missing_lines')}
                statements = sum(reported[p]['summary']['num_statements'] for p in source_files if p in reported)
                covered = sum(reported[p]['summary']['covered_lines'] for p in source_files if p in reported)
                branches = sum(reported[p]['summary'].get('num_branches',0) for p in source_files if p in reported)
                covered_branches = sum(reported[p]['summary'].get('covered_branches',0) for p in source_files if p in reported)
                excluded = sum(reported[p]['summary'].get('excluded_lines',0) or len(reported[p].get('excluded_lines',[]))
                               for p in source_files if p in reported)
                # No blanket exclusions are permitted in the generic gate. Exceptions
                # need separate explicit owner-governed review, not silent PASS.
                passed = bool(statements and not missing_files and not missed and covered==statements and excluded==0)
                result={'status':'PASS' if passed else 'FAIL','policy':POLICY_VERSION,
                        'reason':'100_PERCENT_LINES' if passed else 'UNCOVERED_FIRST_PARTY_LINES',
                        'tests_run':cases, 'test_returncode':cp.returncode,'test_log':log,
                        'first_party_scope':[s.relative_to(root).as_posix() for s in selected],
                        'source_hashes':source_hashes,'files_in_scope':len(source_files),
                        'first_party_executable_statements':statements,
                        'covered_executable_statements':covered,
                        'missing_first_party_files':missing_files,'missing_lines':missed,
                        'excluded_lines':excluded,'assertion_sites_detected':assertion_count,
                        'line_percent':round(100 * covered/statements,2) if statements else 0,
                        'branch_percent':round(100 * covered_branches/branches,2) if branches else None,
                        'branch_status':'REVIEW_ONLY_NOT_A_UNIVERSAL_GATE',
                        'coverage_pass':passed,
                        'test_method':'unittest discover executed under coverage.py',
                        'coverage_version':coverage.__version__,
                        'limitations':['Line execution does not establish semantic correctness or assertion adequacy.',
                                       'AST policy scan is not a proof against dynamic/import-time mocking.',
                                       'Coverage scope requires review against the complete first-party manifest.']}
    if output is not None:
        output.parent.mkdir(parents=True,exist_ok=True)
        output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n',encoding='utf-8')
    return result


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description='PEHAVOS 100% Python line coverage early gate')
    p.add_argument('--root',type=Path,default=Path('.'))
    p.add_argument('--source',action='append',required=True,
                   help='first-party package or Python file relative to root; repeat for all packages')
    p.add_argument('--tests',default='tests',help='unit test directory relative to project root')
    p.add_argument('--timeout',type=int,default=180)
    p.add_argument('--json-out',type=Path)
    a = p.parse_args(argv)
    try:
        result = run_gate(a.root,a.source,a.tests,a.timeout,a.json_out)
    except (ValueError,OSError,subprocess.TimeoutExpired) as exc:
        result={'status':'FAIL','policy':POLICY_VERSION,'reason':'INVALID_GATE_INPUT',
                'detail':str(exc),'coverage_pass':False}
    print(json.dumps(result,indent=2,sort_keys=True))
    return 0 if result['status']=='PASS' else 2


if __name__ == '__main__':
    raise SystemExit(main())
