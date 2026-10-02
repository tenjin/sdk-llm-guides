# AGENTS.md

Instructions for AI coding agents working on this repository.

## What this repo is

Integration guides for the Tenjin SDK, written to be consumed by LLMs and AI coding assistants. The guides in `guides/` are the source of truth. `guides/llm-guide.md` is the entry point: it detects the target platform and routes to the platform-specific guide at `guides/{platform}/llm-guide.md`.

## Conventions

- **Never hardcode SDK version numbers** in guide content, and **never write "use the latest" on its own**. A reader told only to use the latest version fills in a version from memory, which is usually many releases old. Each guide has a "Resolve the SDK Version" section with the exact command (and the URL, for readers that cannot run commands) that returns the current version from the registry for that platform. Install snippets use the placeholder `<TENJIN_SDK_VERSION>`, or an install command that resolves the version itself. Minimum versions for a feature ("requires 1.22.0 or newer") are facts, not pins, and are fine.
- **Keep guides self-contained.** A guide must be usable on its own, without fetching other pages, except for version lookups.
- **Every Tenjin API in a code block must exist in the published SDK.** `scripts/check_guides.py` checks this against `sdk-symbols/` and runs in CI. Write snippets from the SDK's public header, source or type definitions, not from memory. Do not document APIs that are not in a published release yet.
- **SDK key placeholders.** Use `<SDK_KEY>` in code examples, and `<IOS_SDK_KEY>` / `<ANDROID_SDK_KEY>` where a cross-platform project selects the key per platform. Instruct integrators to use the literal string `TENJIN_SDK_KEY_PLACEHOLDER` (or `TENJIN_SDK_KEY_PLACEHOLDER_IOS` / `TENJIN_SDK_KEY_PLACEHOLDER_ANDROID`) in generated code when the real key is not available. Never put a real key in a guide, not even one from a sample app.
- Every platform guide must include: the version lookup, the one-app-and-one-key-per-platform rule, installation, initialization with a "Where connect() Goes" section, a "Verify from the Device Log" section, event tracking, an integration checklist, and a common-mistakes section.
- Code examples cover the forms a project may use: Swift and Objective-C on iOS; Kotlin and Java, and Groovy, Kotlin DSL and version-catalog Gradle files on Android; bare and Expo projects for React Native.
- Reference Tenjin domains as `tenjin.com` (not `tenjin.io`).

## Checking guides against the SDKs

```bash
python3 scripts/check_guides.py          # run before committing; CI runs it on every pull request
python3 scripts/test_check_guides.py     # tests for the checker
python3 scripts/update_sdk_symbols.py    # regenerate sdk-symbols/ from the public SDK distributions
```

- `sdk-symbols/{platform}.json` is generated, never edited by hand. It lists the public API of the newest published SDK, taken from Maven Central (Android), CocoaPods and the public GitHub repository (iOS), pub.dev (Flutter), npm (React Native, Ionic) and GitHub release tags (Unity).
- When an SDK releases, run `update_sdk_symbols.py`, then `check_guides.py`, and fix whatever the new release broke. A scheduled workflow fails when `sdk-symbols/` is behind the registries.
- In code blocks, call the SDK through a recognisable receiver so the checker sees the call: `instance` or `TenjinSDK` (Android), `TenjinSDK` (iOS), `TenjinSDK.instance` (Flutter), `Tenjin` (React Native, Ionic), `instance` or `Tenjin` (Unity), or a variable assigned from one of those in the same guide.
- The checker does not compile anything. It does not check argument types, calls into other libraries, XML or Gradle contents, or prose. Read those against the SDK source yourself.

## Adding a new platform guide

1. Create `guides/{platform}/llm-guide.md`.
2. Add platform detection hints to `guides/llm-guide.md`.
3. Add the platform to the table in `README.md`.
4. Add the raw-URL entry to `llms.txt`.
5. Add a skill wrapper at `skills/tenjin-{platform}/SKILL.md` (see existing skills for the pattern).
6. Add the platform to `scripts/update_sdk_symbols.py` and `scripts/check_guides.py`, and generate its `sdk-symbols/{platform}.json`.

Keep `README.md`, `guides/llm-guide.md`, `llms.txt`, and `skills/` in sync whenever guides are added, removed, or renamed.

## Standards and specifications

This repo follows three open standards for LLM/agent-facing documentation. When editing the corresponding files, conform to the spec:

- **llms.txt** (`llms.txt`): [specification](https://llmstxt.org) | [GitHub](https://github.com/AnswerDotAI/llms-txt). Required format: one H1 title, a blockquote summary, optional prose, then H2 sections containing markdown link lists (`- [name](url): description`). An `## Optional` section marks links that can be skipped when context is short.
- **Agent Skills** (`skills/*/SKILL.md`): [specification](https://agentskills.io/specification) | [GitHub](https://github.com/agentskills/agentskills). Required YAML frontmatter: `name` (lowercase alphanumerics and hyphens, max 64 chars, must match the parent directory name) and `description` (max 1024 chars, must say what the skill does and when to use it). Keep `SKILL.md` under 500 lines. Skills can be validated with the [`skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref) reference tool: `skills-ref validate ./skills/tenjin-ios`.
- **AGENTS.md** (this file): [specification](https://agents.md) | [GitHub](https://github.com/agentsmd/agents.md). Intentionally minimal: plain markdown at the repo root, no required structure.

## Pull requests

- Follow `.github/pull_request_template.md`: link the Jira ticket (`https://adromance.atlassian.net/browse/TENJIN-…`), describe proposed changes, and provide testing steps.
- Commit messages use the `docs:`/`chore:` prefix style with the Jira ticket in brackets, e.g. `docs: add Unity LLM guide [TENJIN-27226]`.
