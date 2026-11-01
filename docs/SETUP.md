# Developer setup, recovery, and smoke testing

**Not required for daily users:** The regular LEAP workflow is natural language plus `COMPILE` in the existing Compiler Project, followed by XML plus `RUN` in the separate Runner Project. The commands below are for technical installation, inspection, and independent verification only. See [Quick Start](../QUICK_START.md).

## 1. Obtain the original intact runtime ZIPs

The exact archives supplied for this project were each too large for GitHub's standard browser single-file upload. They are stored here as verified binary segments. Reassemble **from the repository root**:

```bash
python tools/reassemble_runtime.py compiler
python tools/reassemble_runtime.py runner
```

This writes separate `reconstructed/compiler/02_RUNTIME.zip` and `reconstructed/runner/02_RUNTIME.zip` with the **original filename**. The script rejects modified/missing parts and compares the final SHA-256 to the supplied original archive. It does not run any untrusted ZIP entries.

## 2. Extract separately and set up dependencies

Use distinct directories. Do not overlay the Compiler and Runner; their entrypoints differ. Run these commands with a Python interpreter matching a supported wheel platform. For example, on Linux x86_64 Python 3.13:

```bash
mkdir -p work/compiler work/runner
python -m zipfile -e reconstructed/compiler/02_RUNTIME.zip work/compiler
python -m zipfile -e reconstructed/runner/02_RUNTIME.zip work/runner

cd work/compiler
python -m venv .venv
.venv/bin/python bootstrap.py
.venv/bin/python run_compiler.py self-check
cd ../runner
python -m venv .venv
.venv/bin/python bootstrap.py
.venv/bin/python run_runner.py self-check
```

The supplied `bootstrap.py` performs offline dependency installation using the bundled `wheelhouse/`. Exact supported bundled wheels: Linux x86_64 CPython 3.11-3.14 and Windows x86_64 CPython 3.14. Python 3.11+ is required by Runner; other Python/OS combinations require compatible pinned dependencies. On Windows use the virtual environment interpreter at `.venv\Scripts\python.exe` instead.

## 3. Preflight a preserved example contract

```bash
# From repository root, using the Python environment created for Runner:
work/runner/.venv/bin/python work/runner/run_runner.py preflight examples/four-day-workweek/contract.xml
work/runner/.venv/bin/python work/runner/run_runner.py preflight examples/payroll-platform-evaluation/contract.xml
```

Expected in the tested 1.0.0 setup: **PASS** plus a warning that the contracts are bare XML without the full original Compiler release receipts. PASS is structural, **not** validation of the vendor claims or workplace assessment conclusions.

## 4. The actual model-host workflow

The Compiler Project needs its original project-instructions text and the supplied runtime/guides. In the owner's current workflow, the user submits a natural-language request and types `COMPILE`; the host orchestrates internal compilation and model-role responses. It produces the released XML, brief, and receipt *when the full release flow completes*.

The Runner Project needs its separate original project-instructions text and the correct Runner runtime/guides. Upload the compatible XML (or complete Compiler release package) and any necessary supporting sources, then type `RUN`. The host performs the work and supplies genuine tool observations. This is not a standalone command that manufactures research outputs.

**Missing from this handoff:** The exact `00_PROJECT_INSTRUCTIONS_COMPILER.txt` and `00_PROJECT_INSTRUCTIONS_RUNNER.txt` referenced by the supplied start guides. They are not recreated here from guesses. If starting new ChatGPT Projects, export the original settings from the already functioning Compiler and Runner Projects first. See [`PROJECT_SETTINGS_GAP.md`](PROJECT_SETTINGS_GAP.md).

## 5. Verify publication integrity

```bash
python tools/verify_repo.py
python -m unittest discover -s tests -v
```

For machine-level execution, also run the two runtime self-checks and preflight commands, recording Python version/OS and output. Those are smoke tests, not a coverage report, security penetration test or external approval.
