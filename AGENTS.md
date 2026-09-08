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

## Standards and specifications

This repo follows three open standards for LLM/agent-facing documentation. When editing the corresponding files, conform to the spec:

- **llms.txt** (`llms.txt`): [specification](https://llmstxt.org) | [GitHub](https://github.com/AnswerDotAI/llms-txt). Required format: one H1 title, a blockquote summary, optional prose, then H2 sections containing markdown link lists (`- [name](url): description`). An `## Optional` section marks links that can be skipped when context is short.
- **Agent Skills** (`skills/*/SKILL.md`): [specification](https://agentskills.io/specification) | [GitHub](https://github.com/agentskills/agentskills). Required YAML frontmatter: `name` (lowercase alphanumerics and hyphens, max 64 chars, must match the parent directory name) and `description` (max 1024 chars, must say what the skill does and when to use it). Keep `SKILL.md` under 500 lines. Skills can be validated with the [`skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref) reference tool: `skills-ref validate ./skills/tenjin-ios`.
- **AGENTS.md** (this file): [specification](https://agents.md) | [GitHub](https://github.com/agentsmd/agents.md). Intentionally minimal: plain markdown at the repo root, no required structure.

## Pull requests

- Follow `.github/pull_request_template.md`: link the Jira ticket (`https://adromance.atlassian.net/browse/TENJIN-…`), describe proposed changes, and provide testing steps.
- Commit messages use the `docs:`/`chore:` prefix style with the Jira ticket in brackets, e.g. `docs: add Unity LLM guide [TENJIN-27226]`.
