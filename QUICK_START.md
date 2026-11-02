# LEAP quick start

## Normal owner workflow

1. In the existing **Compiler** ChatGPT Project, enter an ordinary request and add separately labeled reference files where relevant. The Compiler generates the frozen XML contract and a matching compiler receipt. `COMPILE` is an optional shorthand; the configured Compiler also processes ordinary user requests automatically.
2. In the existing **Runner** ChatGPT Project, provide **both** the generated XML and its compiler receipt. Invoke `RUN`. The Runner performs preflight, then executes only currently authorized work; it may release, hold or report failure, but cannot invent evidence or human approvals.
3. Keep the compiled XML unchanged. A user-only missing dependency is reported as a hold; never edit the XML to bypass it.

These are two separately configured ChatGPT Projects with different runtimes and responsibility boundaries. Neither Python runtime calls an external model API by itself; the ChatGPT host supplies the model and permitted tools.

## Owner-designated final Compiler

The owner selected the [November 2 final Compiler build](compiler/final-2026-11-02/README.md), byte-identical to the accepted Cases 1–3 repair candidate, as their final Compiler. Set the Compiler Project Instructions from `compiler/final-2026-11-02/00_PROJECT_INSTRUCTIONS_COMPILER.txt`. For full offline setup, use the owner-supplied original `COMPILER REVISED 02NOV2026.zip` (not present in the Git tree), extract its three files, and upload the runtime ZIP along with start/guide documents. The internal runtime remains `1.0.0`. The unchanged Runner v1.0.0 still executes verified Compiler XML + receipt in new sessions.

Case 4 is independent of normal Compiler→Runner tasks: it is a [synthetic ledger API project](case4/README.md). To develop it, read its own README and start the disposable PostgreSQL environment; it is not a financial production deployment.

## Reproduction limitation

The Git repository contains the original source mirrors, explicit final Compiler source snapshot and Project Instructions, candidate delta, and three frozen-case Runner evidence ZIPs. **It does not contain the owner's complete offline runtime ZIP or the historical original Project Instructions.** A full offline clean install therefore still requires the owner's separately retained runtime bundle. Case 4 includes source, dependencies, tests, Docker/Compose and GitHub Actions to exercise a disposable database; publication is not deployment. See [settings gap](docs/PROJECT_SETTINGS_GAP.md) and [release availability](releases/README.md).
