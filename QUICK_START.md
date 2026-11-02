# LEAP quick start

## Normal owner workflow

1. In the existing **Compiler** ChatGPT Project, enter an ordinary request and add separately labeled reference files where relevant. The Compiler generates the frozen XML contract and a matching compiler receipt. `COMPILE` is an optional shorthand; the configured Compiler also processes ordinary user requests automatically.
2. In the existing **Runner** ChatGPT Project, provide **both** the generated XML and its compiler receipt. Invoke `RUN`. The Runner performs preflight, then executes only currently authorized work; it may release, hold or report failure, but cannot invent evidence or human approvals.
3. Keep the compiled XML unchanged. A user-only missing dependency is reported as a hold; never edit the XML to bypass it.

These are two separately configured ChatGPT Projects with different runtimes and responsibility boundaries. Neither Python runtime calls an external model API by itself; the ChatGPT host supplies the model and permitted tools.

## Candidate acceptance (not production promotion)

The [Cases 1–3 controlled repair candidate](candidate/compiler-1.0.0-cases1-3/README.md) was tested using **one new Compiler test project and the existing Runner 1.0.0**, in fresh Runner sessions. Do not overwrite the baseline Compiler project or replace the Runner. Cases 1–3 passed the frozen acceptance comparisons; Case 4 was excluded.

## Reproduction limitation

The Git repository contains inspectable source mirrors, the candidate delta and the three run-evidence ZIPs. **It does not currently contain all original offline runtime ZIP/parts or original production ChatGPT Project Instructions.** Therefore a new-account full ChatGPT deployment cannot be reproduced solely from GitHub checkout. The candidate project instruction text is included for inspection, but not evidence that original production configuration was reconstructed. See [settings gap](docs/PROJECT_SETTINGS_GAP.md) and [release availability](releases/README.md).
