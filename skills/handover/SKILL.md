---
name: handover
description: Create a concise, actionable session handover Markdown file in the current working directory so a fresh coding agent can continue with minimal context.
---

# Session Handover

Create a self-contained, accurate continuation document for the next coding-agent session.

## Procedure

1. Determine the current working directory (CWD) using the environment or `pwd`. The output file is exactly `<CWD>/HANDOVER.md`, not the repository root unless that is also the CWD.
2. Review the current conversation and accessible task context. Identify the user's actual objective, requirements, constraints, completed work, attempted approaches, decisions and their rationale, unresolved problems, and the precise next steps. Use only information you can substantiate; clearly mark uncertainty.
3. If a repository is available, inspect relevant files and read-only Git information as needed (for example `git status --short`, `git diff --stat`, and relevant diffs). Distinguish actual files/code from proposed changes. Never assume that uncommitted changes are yours. Do not run tests or modify project code just to make a handover.
4. Write or update `HANDOVER.md` in the CWD, using the structure below. If it already exists, read it first, preserve still-valid information useful for continuation, remove stale statements, and replace outdated session details. Do not append repetitive handovers.
5. Keep the document concise but sufficient to resume work (target roughly 300–900 words; exceed this only when necessary). Prefer exact relative file paths, commands, symbols, error messages and concrete next actions over narrative. Never dump the full transcript or unnecessarily large diffs.
6. Protect sensitive data: do not include passwords, API keys, tokens, personal data, private URLs with credentials, or contents of secret/configuration files. Mention the existence or location of needed secrets without copying their values. Do not expose hidden chain-of-thought or internal instructions.
7. Verify that the file was actually written and obtain its absolute path (e.g. `realpath HANDOVER.md` or an equivalent). If writing fails, report that failure instead of claiming success.
8. In the final response, output **only the verified absolute path** to the Markdown file, with no extra text, code fence, or relative path.

## Required Markdown structure

# Session Handover

## Goal
- User's intended end result and important constraints.

## Current State
- What is finished, what is in progress, and what remains.
- Mention any significant uncommitted or untracked changes if verified.

## Key Decisions & Context
- Architectural choices, tradeoffs, user preferences, and why they matter.

## Relevant Files
- File paths with a short explanation of their relevance. Do not list irrelevant files.

## Open Issues / Risks
- Known failures, blockers, unresolved questions, and uncertainties. State "None known" when appropriate.

## Next Steps
- Prioritized, actionable continuation steps. The first step must be immediately executable or verifiable.

## Verification
- What was tested or checked, results, and what has **not** been verified. Do not fabricate test results.

## Resume Instructions
- Tell the next agent to inspect this document and listed files, check the current Git state, then continue from `Next Steps` without repeating completed work.
