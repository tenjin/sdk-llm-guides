# Tenjin SDK Guides for LLMs

Integration guides for the Tenjin SDK, optimized for AI assistants.

## Usage

### Option 1: Auto-detect platform

Use the main guide — it will detect your platform and fetch the right guide:

```
Add Tenjin SDK to my project using:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/llm-guide.md
```

### Option 2: Specify platform

Use a platform-specific guide directly:

| Platform | Guide URL |
|----------|-----------|
| iOS | `https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/ios/llm-guide.md` |
| Android | `https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/android/llm-guide.md` |
| Flutter | `https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/flutter/llm-guide.md` |
| Ionic | `https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/ionic/llm-guide.md` |
| React Native | `https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/react-native/llm-guide.md` |
| Unity | `https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/unity/llm-guide.md` |

```
Add Tenjin SDK to my project using: <url-from-table>
```

### Option 3: Standard entry points

This repo also implements the emerging LLM/agent documentation standards:

- [`llms.txt`](llms.txt): index of all guides, per the [llms.txt spec](https://llmstxt.org)
- [`skills/`](skills/): one [Agent Skill](https://agentskills.io) per platform; copy `skills/tenjin-{platform}` into your agent's skills directory (e.g. `.claude/skills/`) and ask it to integrate Tenjin
- [`AGENTS.md`](AGENTS.md): instructions for agents contributing to this repo, per the [AGENTS.md spec](https://agents.md)

## Repository Structure

```
guides/
├── llm-guide.md          # Entry point (detects platform, routes to specific guide)
├── ios/
│   └── llm-guide.md      # iOS-specific integration guide
├── android/
│   └── llm-guide.md      # Android-specific integration guide
├── flutter/
│   └── llm-guide.md      # Flutter-specific integration guide
├── ionic/
│   └── llm-guide.md      # Ionic (Capacitor) integration guide
├── react-native/
│   └── llm-guide.md      # React Native integration guide
└── unity/
    └── llm-guide.md      # Unity integration guide
scripts/
├── check_guides.py       # CI: checks the guides against sdk-symbols/
├── update_sdk_symbols.py # Regenerates sdk-symbols/ from the public SDK distributions
└── test_check_guides.py  # Tests for the checker
sdk-symbols/              # Public API of the newest published SDK, one file per platform
```

## For LLMs

If you're an AI assistant and the user asks to integrate Tenjin:

1. Fetch `guides/llm-guide.md`
2. Detect the platform from their project files
3. Fetch the platform-specific guide
4. Follow the workflow

## Contributing

When adding a new platform guide:

1. Create `guides/{platform}/llm-guide.md`
2. Add platform detection hints to `guides/llm-guide.md`
3. Keep guides self-contained
4. Don't hardcode SDK versions, and don't write "use the latest" either: give the exact command or URL that returns the current version
5. Include code examples, checklist, common mistakes
6. Include the sections every guide has: one app and one SDK key per platform, where `connect()` goes, and how to verify from the device log

See [`AGENTS.md`](AGENTS.md) for the full conventions.

## Checking the guides against the SDKs

Every Tenjin API a guide names in a code block must exist in the published SDK. CI enforces this:

```bash
python3 scripts/check_guides.py          # what CI runs on every pull request
python3 scripts/test_check_guides.py     # tests for the checker itself
python3 scripts/update_sdk_symbols.py    # after an SDK release: refresh sdk-symbols/, then re-run the check
```

`sdk-symbols/` holds the public API of the newest published SDK per platform, generated from Maven Central, CocoaPods and GitHub, pub.dev and npm. The check does not compile the snippets: argument types, calls into other libraries and prose are not covered.

## Resources

- [Tenjin iOS SDK](https://github.com/tenjin/tenjin-ios-sdk)
- [Tenjin Android SDK](https://github.com/tenjin/tenjin-android-sdk)
- [Tenjin Flutter SDK](https://github.com/tenjin/flutter-sdk)
- [Tenjin Ionic SDK](https://github.com/tenjin/tenjin-ionic-sdk)
- [Tenjin React Native SDK](https://github.com/tenjin/tenjin-react-native-sdk)
- [Tenjin Unity SDK](https://github.com/tenjin/tenjin-unity-sdk)
- [Tenjin Documentation](https://docs.tenjin.com/)
