# Tenjin SDK Integration Guide

> **For AI assistants:** This is the entry point for Tenjin SDK integration. Detect the platform first, then fetch the appropriate guide.

## Step 1: Detect Platform

Check the user's project for these indicators:

| Platform | Look for |
|----------|----------|
| iOS | `*.xcodeproj`, `*.xcworkspace`, `Podfile`, `Package.swift`, `AppDelegate.swift`, `Info.plist` (without cross-platform markers) |
| Android | `build.gradle`, `AndroidManifest.xml`, `MainActivity.kt`, `*.java` in android structure (without cross-platform markers) |
| Flutter | `pubspec.yaml`, `lib/main.dart`, `android/` + `ios/` folders, `.dart` files |
| Ionic | `ionic.config.json`, `capacitor.config.ts`, `package.json` with `@ionic` or `@capacitor`, `angular.json` or `ionic` in dependencies |
| Unity | `Assets/`, `ProjectSettings/`, `*.unity`, `*.cs` scripts |
| React Native | `package.json` with `react-native`, `App.js` or `App.tsx`, `android/` + `ios/` folders |

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
- Integration checklist
- Common mistakes

Follow it step by step.
