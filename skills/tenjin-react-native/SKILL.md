---
name: tenjin-react-native
description: Integrate the Tenjin SDK (mobile attribution and analytics) into a React Native app. Use when the user asks to add, install, update, or debug the Tenjin SDK in this kind of project.
---

# Tenjin SDK integration (react-native)

Fetch the authoritative integration guide and follow it:

https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/react-native/llm-guide.md

The guide is self-contained: installation, initialization, event tracking, an integration checklist, and common mistakes. Key rules it enforces:

- Do not hardcode SDK versions — always check the latest release first.
- Ask the user for their Tenjin SDK key; if unavailable, use the literal placeholder `TENJIN_SDK_KEY_PLACEHOLDER`.

If you cannot fetch the URL (no network access), tell the user and ask them to paste the guide contents.
