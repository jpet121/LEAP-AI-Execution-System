# LEAP quick start

LEAP is used in two separate, already configured ChatGPT Projects. These are the **only two commands the user needs for normal operation**.

## Step 1: COMPILE

In the **LEAP Compiler** Project, type or upload a natural-language request and enter:

```text
COMPILE
```

The Compiler produces a structured XML contract representing the requested work. The Compiler does not execute the work.

## Step 2: RUN

In the separate **LEAP Runner** Project, upload the XML produced by the Compiler and enter:

```text
RUN
```

The Runner uses its model host and tools to execute the contract. Its output is the completed work and evidence, an explicit hold if something material is missing, or a reported failure. It does not silently modify the compiled XML.

**That is the full routine user workflow.** No Python commands, command-line flags, API keys or configuration steps are required in the normal chat interaction with the two already configured Projects.

**For a new deployment:** The original Project Instructions were not included in the materials for this public portfolio package. They must be exported from the working Projects before recreating these exact chat commands in another account. See [Project settings gap](docs/PROJECT_SETTINGS_GAP.md). Technical installation and integrity commands are documented separately in [Developer setup](docs/SETUP.md) and are **not** additional user steps.
