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
| Unity | Coming soon |
| React Native | Coming soon |
| Ionic | Coming soon |

```
Add Tenjin SDK to my project using: <url-from-table>
```

## Repository Structure

```
guides/
├── llm-guide.md          # Entry point (detects platform, routes to specific guide)
├── ios/
│   └── llm-guide.md      # iOS-specific integration guide
├── android/
│   └── llm-guide.md      # Android-specific integration guide
└── flutter/
    └── llm-guide.md      # Flutter-specific integration guide
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
4. Don't hardcode SDK versions — check latest release
5. Include code examples, checklist, common mistakes

## Resources

- [Tenjin iOS SDK](https://github.com/tenjin/tenjin-ios-sdk)
- [Tenjin Android SDK](https://github.com/tenjin/tenjin-android-sdk)
- [Tenjin Flutter SDK](https://github.com/tenjin/flutter-sdk)
- [Tenjin Documentation](https://docs.tenjin.com/)
