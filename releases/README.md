# Runtime source and archive availability

`compiler/source/` and `runner/source/` contain readable first-party copies of original released sources. Both `releases/compiler/archive_manifest.json` and `releases/runner/archive_manifest.json` describe the original binary runtime ZIPs and their chunk checksums.

**Current Git-tree limitation:** the referenced binary parts (`02_RUNTIME.zip.partXX`) were not uploaded to this repository. The existing `tools/reassemble_runtime.py` can reconstruct exact archives **only after those parts are actually supplied**. Do not treat an archive manifest as the archive itself. The historical core sources have not been modified by the Cases 1–3 repair.

The separate controlled candidate publishes its precise source delta under [`candidate/compiler-1.0.0-cases1-3/`](../candidate/compiler-1.0.0-cases1-3/), but not its full bundled 75.7-MB ZIP. Three small complete run-evidence ZIPs *are* published under [`evidence/cases-1-3/`](../evidence/cases-1-3/) with byte hash verification. The actual release promotion remains unapproved.
