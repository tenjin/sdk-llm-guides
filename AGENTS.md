# AGENTS.md

Instructions for AI coding agents working on this repository.

## What this repo is

Integration guides for the Tenjin SDK, written to be consumed by LLMs and AI coding assistants. The guides in `guides/` are the source of truth. `guides/llm-guide.md` is the entry point: it detects the target platform and routes to the platform-specific guide at `guides/{platform}/llm-guide.md`.

## Conventions

- **Never hardcode SDK version numbers** in guide content. Guides must instruct the reader to fetch the latest version from GitHub Releases or the relevant package registry.
- **Keep guides self-contained.** A guide must be usable on its own, without fetching other pages, except for version lookups.
- **Use `<SDK_KEY>` as the placeholder** in code examples, and instruct integrators to use the literal string `TENJIN_SDK_KEY_PLACEHOLDER` in generated code when the real key is not available.
- Every platform guide must include: installation, initialization, event tracking, an integration checklist, and a common-mistakes section.
- Reference Tenjin domains as `tenjin.com` (not `tenjin.io`).

## Adding a new platform guide

1. Create `guides/{platform}/llm-guide.md`.
2. Add platform detection hints to `guides/llm-guide.md`.
3. Add the platform to the table in `README.md`.
4. Add the raw-URL entry to `llms.txt`.
5. Add a skill wrapper at `skills/tenjin-{platform}/SKILL.md` (see existing skills for the pattern).

Keep `README.md`, `guides/llm-guide.md`, `llms.txt`, and `skills/` in sync whenever guides are added, removed, or renamed.

## Pull requests

- Follow `.github/pull_request_template.md`: link the Jira ticket (`https://adromance.atlassian.net/browse/TENJIN-…`), describe proposed changes, and provide testing steps.
- Commit messages use the `docs:`/`chore:` prefix style with the Jira ticket in brackets, e.g. `docs: add Unity LLM guide [TENJIN-27226]`.
