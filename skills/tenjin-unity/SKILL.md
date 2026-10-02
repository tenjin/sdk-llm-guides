---
name: tenjin-unity
description: Integrate the Tenjin SDK (mobile attribution and analytics) into a Unity game or app (C#). Use when the user asks to add, install, update, or debug the Tenjin SDK in this kind of project.
---

# Tenjin SDK integration (unity)

Fetch the authoritative integration guide and follow it:

https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/unity/llm-guide.md

The guide is self-contained: installation, initialization, verification, event tracking, an integration checklist, and common mistakes. Key rules it enforces:

- Resolve the SDK version with the command in the guide's "Resolve the SDK Version" section. Never use a version from memory.
- A Tenjin SDK key belongs to one app: one bundle ID on one platform. A project that builds for iOS and Android needs two keys, selected per platform. Ask the user for each; if unavailable, use the literal placeholders `TENJIN_SDK_KEY_PLACEHOLDER_IOS` and `TENJIN_SDK_KEY_PLACEHOLDER_ANDROID`.
- Call `Connect()` on every launch and every resume, where the guide says to put it.
- Verify the integration from the device log on each platform as the guide describes before adding optional features.

If you cannot fetch the URL (no network access), tell the user and ask them to paste the guide contents.
