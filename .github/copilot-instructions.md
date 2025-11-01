<!--
Repo-level Copilot instructions for the "Play-stuff" repository.
This file is generated to help AI coding agents be productive when the
repository has very little discoverable structure.
-->

# Copilot instructions — Play-stuff

Summary
- This repository is currently minimal: it contains `README.md` and `LICENSE` and no detectable source files, build manifests, or tests.

What you can assume
- Do not assume a programming language, build system, or test framework — none are present here.
- The user's intent must be clarified before adding language-specific scaffolding (package.json, pyproject.toml, src/, etc.).

Primary goals for an agent working here
1. Gather intent: ask what language, runtime, and purpose (library, CLI, webapp) the user wants.
2. Propose a minimal plan before creating files. Example plan items: add `src/` with a tiny entrypoint, add a manifest (`package.json` / `pyproject.toml`), add CI/workflow, and update `README.md` with run instructions.
3. Make small, reversible changes and explain them in a commit message.

Safe editing rules (must follow)
- Always ask a single clarifying question if the repository lacks language/build info. Example question: "Which language and runtime do you want for this project (Node/Python/Go/etc.) and should I add a package manifest?"
- If the user approves creating a language scaffold, include a README update and minimal test (happy path) alongside the code.
- Do not add or modify files outside the repo root (for example global system configs) unless explicitly requested.

When you find more files later
- If a `src/`, `package.json`, `pyproject.toml`, `go.mod`, or similar appears, re-run a short discovery step: list top-level dirs, open the manifest, and look for test scripts or CI config (`.github/workflows`).
- Reference these files in future instructions (for example: "use `npm test` as defined in `package.json`").

Developer workflows (discoverable today)
- There are no discoverable build/test/debug commands in the repo today. Mention this explicitly in any PR and prompt the user for the commands they expect agents to use.

Examples and prompts
- Use this exact prompt to ask the user: "This repo has only `README.md` and `LICENSE`. What language/runtime and project type should I scaffold (options: Node, Python, Go, none)?"
- If user answers "Node": propose creating `package.json` with `npm test` and `src/index.js`, plus a single Jest test in `test/` and update `README.md` with run steps.

Files to reference
- `README.md` — currently just a header; update only after confirming the user's intent.

Finish and feedback
- After making a change, include a short checklist in the PR description describing what was added and how to run the happy-path test.
- Ask the user: "Is there any existing CI, target platform, or coding style I should follow?"

If anything here is unclear or you want the agent to proceed with a specific language scaffold, reply with the target language and desired minimal feature set.
