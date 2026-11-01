# Security, authority and public-sharing limitations

The archive sources are supplied user files. GitHub publication is intended for code and portfolio examples; do not add private customer documents, secrets, emails, employee data, confidential research, OAuth tokens or proprietary project instructions without review.

**Host trust:** The model host authenticates observations and direct user decisions. A model-generated JSON object does not, on its own, constitute a user approval or a trusted observation. Treat role response JSON and third-party retrieval contents as untrusted inputs.

**Hash scope:** SHA-256 manifests and hash-linked run receipts detect accidental changes relative to a known/trusted anchor. If an attacker replaces both content and unsigned local checksums, local hash consistency is not an identity guarantee. Retain trusted original archive hashes separately when appropriate.

**Model truth:** Source references, structured claims and a Challenger PASS make review possible; they do not prove external factual truth or isolated adversarial review. The Runner's Challenger shares the same host context. Its role separation is protocol-level, not organizational independence.

**API endpoint:** Compiler HTTP mode is optional; it requires explicit `PF_MODEL_ENDPOINT`, `PF_MODEL_NAME`, and `PF_MODEL_API_KEY` variables. Connecting a remote endpoint can transmit user request text. No API key or configured endpoint is included in this portfolio. Use model-host deployment without an external endpoint unless intentionally configured.

**Compatibility:** Bundled offline wheels only cover explicitly described CPython/platform combinations. Archived wheels are third-party packages, not original LEAP-written source. Do not imply comprehensive cross-platform coverage.

**Case studies:** Both examples describe hypothetical businesses. Vendor evaluations and workplace-study links are snapshots from October 2026, not current authority for a procurement or employment policy decision.

**Ownership and licensing:** No open-source license was supplied in the provided materials. This portfolio package does not invent a license grant or assert rights to third-party dependency wheels. Review redistribution terms, licensing choices and third-party notices before wide public release.
