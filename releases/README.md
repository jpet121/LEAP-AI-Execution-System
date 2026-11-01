# Original runtime releases  -  exact-byte reconstruction

The supplied Compiler and Runner archives were both named `02_RUNTIME.zip`. Their **original bytes have not been edited**, but for GitHub browser-upload compatibility each is represented as a sequence of parts in a separate subdirectory:

- `compiler/02_RUNTIME.zip.part01` + `part02` (with `archive_manifest.json`)
- `runner/02_RUNTIME.zip.part01` + `part02` (with `archive_manifest.json`)

Run `python tools/reassemble_runtime.py compiler` and `python tools/reassemble_runtime.py runner` from the repository root. It writes each restored ZIP to `reconstructed/<kind>/02_RUNTIME.zip`, verifies per-part hashes and the final original hash. `reconstructed/` is excluded by `.gitignore`.

Do not rename or modify any part before reassembly. Do not confuse the Compiler and Runner archives even though their recovered names are identical.

For connected GitHub upload, runtime ZIPs are divided into approximately 1.5 MiB sequential parts without changing the reconstructed ZIP bytes.
