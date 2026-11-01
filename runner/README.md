# LEAP Runner runtime (source mirror)

This is a byte-for-byte mirror of the inspectable first-party files inside the supplied **Runner 1.0.0** archive, excluding bundled third-party dependency wheels and archive-specific packaging/checksum files.

The untouched, complete offline runtime can be recovered from [`../releases/runner/`](../releases/runner/) using `python tools/reassemble_runtime.py runner` from the repository root. This writes `reconstructed/runner/02_RUNTIME.zip` and verifies the authoritative SHA-256 of the original supplied archive.

**Important:** Source mirrors are for code review. Use the reconstructed full ZIP for offline installation; it contains all declared wheels, original packaging manifest, checksum list, and source files. Runtime code has not been modified for the portfolio. Python `self-check` is a deterministic smoke test, not proof of semantic accuracy or an independently audited release.
