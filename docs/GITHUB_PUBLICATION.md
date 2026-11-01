# Manual GitHub publication - exact steps

**Repository name:** `LEAP-AI-Execution-System` (public portfolio repository). **About:** `Turn natural-language requests into structured XML contracts with COMPILE, then use RUN in a separate Runner to execute the work with traceable evidence and replay-verifiable receipts.`

1. Create the repository named `LEAP-AI-Execution-System`. Set visibility to **Public**, and choose **No license** under GitHub licensing options. Do not initialize it with another README if importing this package via Git.
2. Extract the *outer* `LEAP-AI-Execution-System-GitHub-Ready.zip` delivery file on your computer. Upload the **contents** of the extracted `LEAP-AI-Execution-System-GitHub-Ready` directory, not the ZIP as a single GitHub file.
3. For browser-only GitHub use, upload files in groups. Every individual release `.partNN` is **under 2 MiB**; the smaller parts preserve the exact original ZIP bytes and support reliable upload through the connected GitHub interface. Keep all numbered parts and `archive_manifest.json` in their exact folders.
4. Verify nested folders in the GitHub tree, especially `compiler/source`, `runner/source`, `examples`, `releases`, `tools` and `docs`. The repository root must contain `README.md`.
5. After a local clone, run `python tools/verify_repo.py`, `python -m unittest discover -s tests -v`, and (on a compatible Python host) the runtime self-checks and preflights from [SETUP](SETUP.md).
6. Review [Licensing notice](../LICENSE-NOTE.md), [Third-party notices](../THIRD_PARTY_NOTICES.md), the **limitations**, and the **Project settings gap** before publication. Do not publish proprietary settings, customer data or API credentials. The current release contains no first-party reuse license.
7. For users, the only commands are `COMPILE` in the existing Compiler Project and `RUN` in the existing Runner Project. Do not present reconstruction, CLI, or self-check commands as required daily steps.

**Routine user workflow:** [QUICK_START.md](../QUICK_START.md). Engineering commands in this guide are only for repository upload and independent verification.

**Recommended GitHub topics:** `ai-engineering`, `python`, `llm-orchestration`, `requirements-engineering`, `structured-output`, `xml`, `verification`, `human-in-the-loop`, `evidence-traceability`, `software-assurance`.

**If you use git CLI** (instead of the browser, on your computer):

```bash
git init
git add .
git commit -m "Publish LEAP Compiler and Runner portfolio with source, samples and verification"
git branch -M main
git remote add origin https://github.com/jpet121/LEAP-AI-Execution-System.git
git push -u origin main
```

Create the empty remote repository first. These commands are illustrative and have **not** been run against your GitHub account.

**Connected upload packaging note:** Binary archive parts were repacked into smaller lossless segments for reliable GitHub transfer. The original archived runtimes, first-party source code and historical examples remain byte-identical. Verify with `python tools/verify_repo.py`.
