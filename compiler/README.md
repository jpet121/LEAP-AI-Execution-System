# LEAP Compiler runtime (source mirror)

This is a byte-for-byte mirror of the inspectable first-party files inside the supplied **Compiler 1.0.0** archive, excluding bundled third-party dependency wheels and archive-specific packaging/checksum files.

The untouched, complete offline runtime can be recovered from [`../releases/compiler/`](../releases/compiler/) using `python tools/reassemble_runtime.py compiler` from the repository root. This writes `reconstructed/compiler/02_RUNTIME.zip` and verifies the authoritative SHA-256 of the original supplied archive.

**Important:** Source mirrors are for code review. Use the reconstructed full ZIP for offline installation; it contains all declared wheels, original packaging manifest, checksum list, and source files. Runtime code has not been modified for the portfolio. Python `self-check` is a deterministic smoke test, not proof of semantic accuracy or an independently audited release.

## Current owner-designated build

See [Prompt Forge Compiler 1.0.0 — Final Build (2026-11-02)](final-2026-11-02/README.md). The historic `source/` tree above is **intentionally unchanged** for historical hash verification; the new final source is in its own namespace. The owner-designated runtime matches the accepted repair candidate byte-for-byte. The offline ZIP and third-party wheels are retained outside GitHub.
