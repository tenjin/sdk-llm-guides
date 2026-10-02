# Tenjin SDK Integration Guide

> **For AI assistants:** This is the entry point for Tenjin SDK integration. Detect the platform first, then fetch the appropriate guide.

## Step 1: Detect Platform

Check the cross-platform frameworks **first**. Flutter, React Native and Capacitor projects contain `ios/` and `android/` folders that look like native projects; integrating the native SDK into those folders is wrong.

Go down this table in order and stop at the first match:

| Order | Platform | Look for |
|-------|----------|----------|
| 1 | Unity | `ProjectSettings/ProjectVersion.txt` together with `Assets/` and `Packages/manifest.json` |
| 2 | Flutter | `pubspec.yaml` with a `flutter:` SDK dependency, `lib/main.dart` |
| 3 | React Native | `package.json` that depends on `react-native`. If it also depends on `expo`, it is an Expo project: the React Native guide has separate Expo steps |
| 4 | Ionic / Capacitor | `capacitor.config.ts`, `capacitor.config.json` or `capacitor.config.js`, or `package.json` that depends on `@capacitor/core` |
| 5 | iOS | `*.xcodeproj` or `*.xcworkspace`, and none of the above |
| 6 | Android | `settings.gradle` or `settings.gradle.kts` with a module that applies `com.android.application`, and none of the above |

Not supported: a Cordova project (`config.xml` with a `<widget>` element and no Capacitor). Tell the user instead of improvising.

If the folder is an exported build (for example an Xcode or Gradle project that Unity generated), do not integrate there: the next export overwrites it. Find the source project.

If you can't detect the platform, ask:

> "Which platform are you building for? (iOS, Android, Flutter, Ionic, Unity, React Native)"

## Step 2: Fetch Platform Guide

Once you know the platform, fetch the corresponding guide:

| Platform | Guide URL |
|----------|-----------|
| iOS | `https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/ios/llm-guide.md` |
| Android | `https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/android/llm-guide.md` |
| Flutter | `https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/flutter/llm-guide.md` |
| Ionic | `https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/ionic/llm-guide.md` |
| Unity | `https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/unity/llm-guide.md` |
| React Native | `https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/react-native/llm-guide.md` |

## Step 3: Follow the Guide

The platform-specific guide contains:
- Installation instructions
- Code examples
- How to verify the integration from the device log
- Integration checklist
- Common mistakes

Follow it step by step. Four rules hold on every platform, and each guide gives the details:

1. **Resolve the SDK version with the command the guide gives.** Do not use a version from memory; it is usually many releases old.
2. **One Tenjin app and one SDK key per platform.** A Tenjin app is one bundle ID on one platform, so a project that ships on iOS and Android needs two keys, chosen at runtime. A debug suffix or a product flavor changes the bundle ID and therefore the app.
3. **Call `connect()` on every launch**, in the place the guide names, and on iOS only after the user has answered the tracking prompt. If the app already shows that prompt, hook into it instead of adding a second one.
4. **Verify before adding optional features.** Read the device log as the guide describes and confirm the server accepted the request.
