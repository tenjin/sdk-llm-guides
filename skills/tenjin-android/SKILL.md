---
name: tenjin-android
description: Integrate the Tenjin SDK (mobile attribution and analytics) into an Android app (Kotlin or Java, Gradle project). Use when the user asks to add, install, update, or debug the Tenjin SDK in this kind of project.
---

# Tenjin SDK integration (android)

Fetch the authoritative integration guide and follow it:

https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/android/llm-guide.md

The guide is self-contained: installation, initialization, verification, event tracking, an integration checklist, and common mistakes. Key rules it enforces:

- Resolve the SDK version with the command in the guide's "Resolve the SDK Version" section. Never use a version from memory.
- A Tenjin SDK key belongs to one app: one bundle ID on one platform. Ask the user for the key of the app that matches this project; if unavailable, use the literal placeholder `TENJIN_SDK_KEY_PLACEHOLDER`.
- Call `connect()` on every launch, where the guide says to put it.
- Verify the integration from the device log as the guide describes before adding optional features.

If you cannot fetch the URL (no network access), tell the user and ask them to paste the guide contents.
