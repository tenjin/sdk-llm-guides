# Tenjin Godot SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin Godot SDK into a Godot 4 project without requiring external documentation lookups, except for the version lookup below.
>
> **Requirements:** Godot 4.3 or newer, exporting to Android and/or iOS. GDScript. The addon does nothing on desktop or Web: every call is a no-op there.
>
> **Sources:**
> - Repository: [github.com/tenjin/tenjin-godot-sdk](https://github.com/tenjin/tenjin-godot-sdk)
> - Full README: [README.md](https://github.com/tenjin/tenjin-godot-sdk/blob/main/README.md)
> - Public API: [addons/tenjin/tenjin.gd](https://github.com/tenjin/tenjin-godot-sdk/blob/main/addons/tenjin/tenjin.gd)
> - Releases: [github.com/tenjin/tenjin-godot-sdk/releases](https://github.com/tenjin/tenjin-godot-sdk/releases)

---

## Before You Begin

### Resolve the SDK Version

This document contains no SDK version number on purpose. **Do not use a version you remember**: versions recalled from training data are usually many releases old.

The addon is distributed as a zip attached to each GitHub release. Find the latest one:

```bash
gh release view --repo tenjin/tenjin-godot-sdk --json tagName,assets --jq '.tagName, .assets[].name'
```

If you cannot run `gh`, fetch `https://api.github.com/repos/tenjin/tenjin-godot-sdk/releases/latest` and read `tag_name` and `assets[].browser_download_url`. If you can do neither, stop and ask the developer to download the latest release. Never guess.

Do **not** copy `addons/tenjin` from a clone of the repository: the repository has no native binaries, only the release zip does.

### One App and One SDK Key per Platform

A Tenjin app is **one bundle ID / application ID on one platform**. A Godot project that exports to iOS and Android is therefore **two Tenjin apps with two SDK keys**, and the code must pick the right one at runtime:

- Tenjin's servers look the app up by the platform and the bundle ID the request carries, then check that the SDK key belongs to that app. The iOS key is refused on Android and the Android key is refused on iOS.
- Anything that changes the bundle ID changes the Tenjin app, for example a separate export preset with its own package name for debug builds. Either register that ID as its own app in the Tenjin dashboard and use its key in those builds, or expect those builds to be rejected (see [Verify from the Device Log](#5-verify-from-the-device-log)).

Before writing code, find the IDs the project produces and tell the developer. They are in `export_presets.cfg`, in each preset's `[preset.N.options]` section:

- Android: `package/unique_name`
- iOS: `application/bundle_identifier`

### Get the SDK Keys

**Ask the developer for one Tenjin SDK key per platform the project exports to.** Code examples use `<IOS_SDK_KEY>` and `<ANDROID_SDK_KEY>` as placeholders. Before writing any integration code, prompt the user:

> "Tenjin needs one SDK key per platform. What is the SDK key of your iOS app (bundle ID `<the iOS bundle ID you found>`) and of your Android app (package name `<the Android package you found>`)? You can find each in the [Tenjin dashboard](https://www.tenjin.com/dashboard/organizations) on that app's page. If you don't have them handy, I can use placeholders and you can fill them in later — just search your project for `TENJIN_SDK_KEY_PLACEHOLDER` to find them."

If the developer provides the keys, substitute them directly in all generated code. If they prefer to add them later, use the literal strings `TENJIN_SDK_KEY_PLACEHOLDER_IOS` and `TENJIN_SDK_KEY_PLACEHOLDER_ANDROID`. If the project exports to one platform only, ask for that key only. Never copy a key from the addon's sample project or from another app.

## Integration Workflow

Follow this two-step approach:

1. **First, integrate the basics.** Complete sections 1–5 (Installation, iOS Setup, Android Setup, Core Initialization, Verify from the Device Log). This gives the developer install tracking, session tracking, and ATT support — the foundation every Tenjin integration needs.

2. **Then, ask what else they need.** After the basic integration is working, prompt the user:

> "Tenjin basic integration is done (install tracking + ATT). Would you like to add any of these features?"
> - **Purchase tracking** — in-app purchases and subscriptions (Section 6)
> - **Custom events** — track in-app actions like level completions or signups (Section 7)
> - **SKAdNetwork conversion values** — for SKAN attribution on iOS (Section 8)
> - **GDPR / consent management** — opt-in/out, CMP, Google DMA (Section 9)
> - **Attribution info & deep links** — LiveOps attribution data, deferred deep links (Section 10)
> - **Ad revenue (ILRD)** — impression-level revenue from ad networks (Section 11, paid feature)
> - **User identity & analytics** — customer user IDs, analytics IDs, user profile (Section 12)

Only implement the sections the developer requests. Do not add features they didn't ask for.

---

## Quick Context

Tenjin is a mobile attribution and analytics platform. The SDK tracks app installs, sessions, in-app purchases, ad revenue, and custom events. It integrates with Apple's ATT framework and SKAdNetwork for privacy-compliant attribution on iOS, and supports Google Play, Amazon, and other stores on Android.

The Tenjin Godot SDK is an editor plugin in `addons/tenjin`. Enabling it registers an autoload named **`Tenjin`** (the script `addons/tenjin/tenjin.gd`), which is the whole public API. It forwards to the native Tenjin Android SDK (through a Godot Android plugin) and the native Tenjin iOS SDK (through a GDExtension).

- Method names are `snake_case`. The connect method is **`connect_sdk()`**, not `connect()`: `connect()` is Godot's own `Object.connect` for signals, and calling `Tenjin.connect()` without arguments is an error.
- Async results (ATT answer, attribution info, deep links) arrive as **signals**, always on the main thread.
- In the editor, on desktop and on Web there is no native SDK and every call does nothing. Game code needs no platform checks, and `Tenjin.is_available()` tells whether the native SDK is loaded.

---

## 1. Installation

1. Download `tenjin-godot-sdk-<version>.zip` from the latest release (see [Resolve the SDK Version](#resolve-the-sdk-version)).
2. Copy its `addons/tenjin` folder into the project's `addons/` folder, so the project has `addons/tenjin/plugin.cfg`. If `addons/tenjin` already exists (an older version), replace the whole folder.
3. Enable the plugin. In the editor: **Project → Project Settings → Plugins**, enable **Tenjin SDK**. Without the editor, add it to `project.godot`:

```ini
[autoload]

Tenjin="*res://addons/tenjin/tenjin.gd"

[editor_plugins]

enabled=PackedStringArray("res://addons/tenjin/plugin.cfg")
```

If `[editor_plugins]` already lists other plugins, add the path to the existing array instead of replacing it. Do not create a second autoload that also loads `tenjin.gd`, and do not name any other autoload `Tenjin`.

---

## 2. iOS Platform Setup

The addon's export plugin does most of the work on every iOS export:

- Embeds `TenjinSDK.xcframework` in the Xcode project.
- Adds `NSUserTrackingUsageDescription` (the ATT prompt text) to `Info.plist`.
- Adds Tenjin's `SKAdNetworkItems` to `Info.plist`.

Both are controlled by project settings that the plugin registers (visible in **Project Settings → Tenjin → iOS** with *Advanced Settings* on), stored in `project.godot`:

```ini
[tenjin]

ios/tracking_usage_description="We use this data to provide a better and personalized ad experience."
ios/add_skadnetwork_ids=true
```

Change the description to the text the developer wants on the prompt. Set `add_skadnetwork_ids=false` only if another plugin (usually an ad network SDK) already writes `SKAdNetworkItems`; two writers produce a duplicate key.

One key must be added by hand: **`NSAdvertisingAttributionReportEndpoint`**, so SKAdNetwork postbacks reach Tenjin (iOS 15+). Godot regenerates the Xcode project on every export, so **do not edit `Info.plist` in Xcode**: the change is lost on the next export. Add it to the iOS export preset instead, under **Application → Additional Plist Content**. In `export_presets.cfg`, inside the iOS preset's `[preset.N.options]` section:

```ini
application/additional_plist_content="<key>NSAdvertisingAttributionReportEndpoint</key><string>https://tenjin-skan.com</string>"
```

If the option already has content, append the key and string to it.

---

## 3. Android Platform Setup

The Android export must use a **Gradle build**, because the Tenjin Android SDK is added as a Maven dependency. In the Android export preset, enable **Gradle Build → Use Gradle Build**, and install the Android build template when Godot asks (**Project → Install Android Build Template**). In `export_presets.cfg`:

```ini
gradle_build/use_gradle_build=true
```

Without it the export fails, or the app ships without the Tenjin SDK.

Nothing else is needed. On every Android export the addon adds:

- The Tenjin Android SDK (`com.tenjin:android-sdk`) and the Godot bridge.
- `play-services-ads-identifier` and `play-services-appset`, which the SDK needs to read the advertising ID and App Set ID.
- The `INTERNET`, `ACCESS_NETWORK_STATE` and `AD_ID` permissions, and the ProGuard rules the bridge needs.

Do not add these to `android/build/` by hand. If the project already has another plugin that declares `play-services-ads-identifier` (ad SDKs usually do), Gradle resolves the two to one version.

---

## 4. Core Initialization

### Where connect_sdk() Goes

- **On every launch and every return to the foreground**, not only on first open. Tenjin needs the session data, and accounts that only connect on first open may be suspended. In Godot, the return to the foreground is `NOTIFICATION_APPLICATION_RESUMED`.
- **On iOS, after the user has answered the tracking prompt.** Calling `connect_sdk()` before the ATT answer sends a zeroed IDFA and degrades attribution.
- **Everything that changes the first request goes between `initialize()` and the first `connect_sdk()`:** `set_app_store()`, consent calls (Section 9), `set_cache_event_setting()`, `append_app_subversion()` and `register_deep_link_handler()`.
- **If the game already has a tracking prompt, hook into it. Do not add a second one.** Search the project for `requestTrackingAuthorization`, `AppTrackingTransparency`, `tracking_authorization` and `att`. If the game already asks through another plugin, call `Tenjin.connect_sdk()` after that plugin reports the answer and leave out `request_tracking_authorization()` below.

Calling `connect_sdk()` on every return to the foreground is safe: the native SDKs skip a connect that comes within 30 seconds of the previous one.

### The ATT Prompt

`Tenjin.request_tracking_authorization()` shows the iOS App Tracking Transparency prompt and emits `tracking_authorization_received(status: int)` with the answer, a `Tenjin.TrackingStatus` value (`NOT_DETERMINED`, `RESTRICTED`, `DENIED`, `AUTHORIZED`). iOS shows the prompt once per install; later calls emit the stored answer without asking. On Android and desktop there is no prompt and the signal is emitted right away with `AUTHORIZED`, so the same code works on every platform.

### Recommended Implementation

Create a new autoload, so Tenjin starts once and receives the resume notification whatever scene is active. Save as `res://tenjin_setup.gd`:

```gdscript
extends Node
## Starts Tenjin and connects on every launch and every return to the foreground.

# One key per platform: an iOS app and an Android app are two Tenjin apps.
const IOS_SDK_KEY := "<IOS_SDK_KEY>"
const ANDROID_SDK_KEY := "<ANDROID_SDK_KEY>"

var _connecting := false


func _ready() -> void:
	Tenjin.initialize(IOS_SDK_KEY if OS.get_name() == "iOS" else ANDROID_SDK_KEY)
	Tenjin.set_app_store(Tenjin.AppStore.GOOGLE_PLAY)  # Android only; GOOGLE_PLAY, AMAZON or OTHER
	_connect_tenjin()


func _notification(what: int) -> void:
	if what == NOTIFICATION_APPLICATION_RESUMED:
		_connect_tenjin()


func _connect_tenjin() -> void:
	if _connecting:
		return
	_connecting = true
	# Shows the ATT prompt the first time on iOS; answers at once afterwards
	# and on other platforms.
	Tenjin.request_tracking_authorization()
	await Tenjin.tracking_authorization_received
	Tenjin.connect_sdk()
	_connecting = false
```

Register it **after** `Tenjin` in `project.godot`, so the `Tenjin` autoload exists when it runs:

```ini
[autoload]

Tenjin="*res://addons/tenjin/tenjin.gd"
TenjinSetup="*res://tenjin_setup.gd"
```

If the game already has a boot autoload or a main scene script that runs once at startup, the same code can go there instead of a new autoload, as long as it also handles `NOTIFICATION_APPLICATION_RESUMED`.

---

## 5. Verify from the Device Log

Do this before adding any optional feature, **once per platform**: the two platforms use different keys and different Tenjin apps, so one passing does not prove the other. The editor and desktop runs prove nothing, because there is no native SDK there: export to a device or emulator.

The GDScript API has no debug-log call. The log lines come from the native SDKs, not from Godot's output panel.

### Android

Run on a device or emulator with Google Play services. The native SDK logs every request under the Logcat tag **`HttpConnection`**, and labels every request `Tenjin::connect` regardless of its type:

```bash
adb logcat -s HttpConnection:D TenjinSDK:D
```

A working integration prints, on launch:

```text
D/TenjinSDK: Connecting...
D/HttpConnection: Tenjin request URL: https://track.tenjin.com/v0/event
D/HttpConnection: Tenjin::connect params: {...}
D/HttpConnection: Tenjin::connect response: {"code":200,"success":true}
```

The Android SDK logs the response body, not the HTTP status. Match on the text in the table below. The request parameters include `plugin=godot`.

At startup Godot also logs three `USER ERROR` lines about `tenjin.gdextension` (`Error loading GDExtension configuration file`, `Failed loading resource`, `Error loading extension`). They are expected on Android and harmless: that file is the iOS bridge.

### iOS

The native iOS SDK prints requests only with its debug logs on, and the Godot addon has no call for that. Verify iOS with the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics) (see [In the Dashboard](#in-the-dashboard)). Godot's own output in the Xcode console shows whether `Tenjin.is_available()` is `true`, if the game prints it.

### What the Response Means

| Response contains | HTTP status | Meaning | What to do |
|-------------------|-------------|---------|------------|
| `"success":true` | 200 | Accepted | Nothing. The integration works on this platform |
| `unauthorized` | 401 | The SDK key is unknown, or it is not the key of this app | Check the runtime key selection: the iOS key on iOS, the Android key on Android, each from that app's page in the dashboard |
| `no such app` | 404 | There is no Tenjin app for this bundle ID on this platform | Create the app in the dashboard with exactly this ID, or fix the ID in the export preset |
| `invalid device identifier` | 202 | The request carried no advertising ID | Test on a device or emulator with Google Play services; check that the export used the Gradle build |
| `not logged` | 202 | The SDK key is disabled | Enable the key in the dashboard or use another key of the same app |
| `ignored` | 202 | The request was filtered by an app-version rule configured for the app | Check the app's version rules in the dashboard |

A 202 is **not** success: the request was received and dropped.

### No Request at All

- `Tenjin.is_available()` returns `false`: the native SDK did not load. On Android, check that the export used the Gradle build and the plugin is enabled. On iOS, check that `addons/tenjin/bin/` came from the release zip.
- A `connect_sdk()` within 30 seconds of the previous one is skipped by the native SDK and sends nothing. The timestamp is stored on the device, so it survives an app restart. Android logs `Connect deduped by persisted timestamp` under the tag `TenjinSDK`. Wait 30 seconds, clear the app's data (`adb shell pm clear <package>`), or reinstall.

### In the Dashboard

Register the device's advertising ID (GAID or IDFA) under **Support → [Test Devices](https://www.tenjin.com/dashboard/debug_app_users)**. On iOS, accept the ATT prompt first, or the IDFA is all zeros. Then the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics) shows events from that device as they arrive.

---

## 6. Purchase Event Tracking

Godot has no built-in store API. Purchases come from a billing plugin (for example the Google Play Billing plugin on Android, or a StoreKit plugin on iOS). Call Tenjin from that plugin's purchase-success handler.

### Manual Revenue (No Validation)

```gdscript
Tenjin.transaction("product_identifier", "USD", 1, 9.99)  # product, currency, quantity, unit price
```

### Validated Purchases

The method differs per platform; each one does nothing on the other platform:

```gdscript
# iOS
Tenjin.transaction_with_receipt(product_name, currency_code, quantity, unit_price, transaction_id, base64_receipt)

# Android: purchase_data is the purchase's original JSON
Tenjin.transaction_with_data_signature(product_name, currency_code, quantity, unit_price, purchase_data, data_signature)
```

For validation, add the App-Specific Shared Secret (iOS app) and the Base64-encoded RSA public key (Android app) in the Tenjin dashboard.

### Subscription Tracking

Subscriptions are **not** captured by `connect_sdk()`. Call one of these from the purchase-handling code. Fill the fields for the platform the game is running on; the others are ignored.

```gdscript
Tenjin.subscription(
	"com.example.monthly", "USD", 9.99,
	# iOS
	ios_transaction_id, ios_original_transaction_id,
	ios_receipt,          # JWS signed transaction
	ios_sk_transaction,   # StoreKit 2 transaction JSON
	# Android
	android_purchase_token, android_purchase_data, android_data_signature)

# iOS 16+ only: the SDK fetches the latest StoreKit 2 transaction itself.
# Use it when the billing plugin doesn't expose StoreKit 2 data.
var error := Tenjin.subscription_with_storekit("com.example.monthly", "USD", 9.99)
if not error.is_empty():
	push_warning(error)
```

**Notes:**
- **iOS:** add the app's **App-Specific Shared Secret** in the Tenjin dashboard. Send one transaction per billing interval (first charge and each renewal), and none during a free trial.
- **Android:** subscriptions are verified through the **Google Play Developer API**, so the Android app needs Google Play Developer API access configured in the Tenjin dashboard (a different credential from the RSA public key used for one-time purchases). Send **once per subscription**, not once per renewal: Tenjin resolves renewals, trials and cancellations from the purchase token.

---

## 7. Custom Events

> **Prerequisite:** `connect_sdk()` must have been called before sending any custom events.

```gdscript
# Event without value
Tenjin.event_with_name("level_complete")

# Event with an integer value
Tenjin.event_with_name_and_value("coins_spent", 50)
```

**Limits:**
- Event names must be under **80 characters**
- Maximum **500 unique** event names per app

---

## 8. SKAdNetwork Conversion Values (iOS Only)

Does nothing on Android.

```gdscript
# Basic conversion value (0-63)
Tenjin.update_postback_conversion_value(5)

# With coarse value ("low", "medium", "high"), iOS 16.1+ / SKAN 4.0
Tenjin.update_postback_conversion_value(5, "medium")

# With coarse value and lock window
Tenjin.update_postback_conversion_value(5, "high", true)
```

---

## 9. GDPR & Privacy Compliance

Call these after `initialize()` and before `connect_sdk()`, so the first request already respects the user's choice.

### Full Opt-In / Opt-Out

```gdscript
if user_consented:
	Tenjin.opt_in()
else:
	Tenjin.opt_out()  # No API requests will be sent
```

### Granular Parameter Control

The methods that take a parameter list are `opt_in_params` and `opt_out_params`, and they take a `PackedStringArray`. `opt_in()` and `opt_out()` take no arguments.

```gdscript
# Only send these specific parameters
Tenjin.opt_in_params(PackedStringArray([
	"ip_address", "advertising_id", "developer_device_id", "limit_ad_tracking", "referrer",
]))

# Or send everything EXCEPT these parameters
Tenjin.opt_out_params(PackedStringArray(["locale", "timezone", "build_id"]))
```

Tenjin needs `advertising_id` on Android and `developer_device_id` on iOS. Requests without them are not recorded.

### CMP-Based Consent

Automatically opt in/out based on CMP consent (TCF purpose 1):

```gdscript
Tenjin.opt_in_out_using_cmp()
```

### Google DMA Parameters

With a CMP integrated, the SDK collects these on its own. To set them yourself:

```gdscript
# Manual control
Tenjin.set_google_dma_parameters(true, true)  # (ad_personalization, ad_user_data)

# Toggle collection
Tenjin.opt_in_google_dma()  # default
Tenjin.opt_out_google_dma()
```

---

## 10. Attribution Info & Deep Links

### Attribution Info (LiveOps Campaigns)

> **Note:** attribution info is a paid feature. Contact your Tenjin account manager for access.

```gdscript
Tenjin.attribution_info_received.connect(func(info: Dictionary) -> void:
	var ad_network: String = info.get("ad_network", "")
	var campaign_id: String = info.get("campaign_id", "")
	var campaign_name: String = info.get("campaign_name", ""))
Tenjin.attribution_info_failed.connect(func(error: String) -> void: push_warning(error))
Tenjin.get_attribution_info()
```

Values are returned only when available. Other keys: `advertising_id`, `tenjin_parameter_0` … `tenjin_parameter_5`.

On Android, `attribution_info_failed` is only emitted when Tenjin is not initialized: the Android SDK reports success only, so a failed request emits nothing. Do not wait on `attribution_info_failed` to unblock game logic.

### Deferred Deep Links

`deep_link_received` carries Tenjin **deferred** deep links: the parameters of the Tenjin campaign link that led to the install. Register the handler after `initialize()` and before `connect_sdk()`:

```gdscript
Tenjin.deep_link_received.connect(func(params: Dictionary) -> void:
	print(params))  # on Android it also has clicked_tenjin_link and is_first_session
Tenjin.register_deep_link_handler()
```

It does **not** report links that open the app through a URL scheme or universal link. Godot has no built-in handler for those; do not try to route them through `deep_link_received`.

If a third-party service gives the game a deep link, pass it instead of the plain connect, so Tenjin attributes it:

```gdscript
Tenjin.connect_sdk_with_deferred_deeplink("myapp://campaign?id=123")
```

---

## 11. Impression Level Ad Revenue (ILRD)

> **Note:** ILRD is a paid feature. Contact your Tenjin account manager before implementing.

Pass the impression data from the ad network's callback, as a `Dictionary` or a JSON string:

```gdscript
Tenjin.event_ad_impression_applovin(ad_info)   # AppLovin MAX
Tenjin.event_ad_impression_admob(ad_value)     # AdMob
Tenjin.event_ad_impression_ironsource(data)    # Unity LevelPlay
Tenjin.event_ad_impression_hyperbid(data)
Tenjin.event_ad_impression_topon(data)
Tenjin.event_ad_impression_tradplus(data)
Tenjin.event_ad_impression_cas(data)
Tenjin.event_ad_impression_cloudx(data)
```

### AdMob value units

> **Important:** despite its name, `value_micros` is **not** in micros on iOS. The iOS SDK reads it as
> currency units (e.g. `0.012245` USD); the Android SDK reads it as micros (e.g. `12245`).
> AdMob reports micros on both platforms, so divide by 1,000,000 on iOS only.
> Sending raw micros on iOS inflates ad revenue 1,000,000x; dividing on Android reports 1,000,000x too little.

```gdscript
# value_micros: the paid-event value in micros, as your AdMob plugin reports it.
# Check the plugin's docs: some expose it already converted to currency units.
func send_admob_impression(ad_unit_id: String, value_micros: int, currency_code: String, precision_type: int) -> void:
	Tenjin.event_ad_impression_admob({
		"ad_unit_id": ad_unit_id,
		"value_micros": value_micros / 1000000.0 if OS.get_name() == "iOS" else value_micros,
		"currency_code": currency_code,
		"precision_type": precision_type,
	})
```

---

## 12. User Identity & Analytics

These return values directly; there are no callbacks.

### Customer User ID

```gdscript
Tenjin.set_customer_user_id("user_123")
var user_id := Tenjin.get_customer_user_id()
```

### Analytics Installation ID

A locally generated persistent identifier (useful when IDFA/AAID is unavailable):

```gdscript
var installation_id := Tenjin.get_analytics_installation_id()
```

### User Profile Data

```gdscript
var profile := Tenjin.get_user_profile_dictionary()
print("Session count: ", profile.get("session_count"))
print("Total session time (ms): ", profile.get("total_session_time"))
print("IAP transaction count: ", profile.get("iap_transaction_count"))
print("Total ad revenue (USD): ", profile.get("total_ilrd_revenue_usd"))

# Reset all profile data
Tenjin.reset_user_profile()
```

---

## 13. Additional Configuration

Call these after `initialize()` and before `connect_sdk()`.

### A/B Testing with App Subversion (requires DataVault)

```gdscript
Tenjin.append_app_subversion(8888)  # Reports as e.g. "1.0.1.8888"
```

### Event Caching (Offline Support)

```gdscript
Tenjin.set_cache_event_setting(true)
```

The setting is stored on the device. Removing the call in a later release does not turn caching off; call `set_cache_event_setting(false)` to disable it.

### Google Ads On-Device Conversion Measurement (ICM / ODM)

Not covered for Godot: the iOS export has no CocoaPods step to add Google's `GoogleAdsOnDeviceConversion` SDK. If the developer runs Google Ads campaigns for the iOS app and asks for it, tell them to contact Tenjin support. Do not add it otherwise.

---

## 14. Integration Checklist

When integrating Tenjin into a Godot project, verify these items:

- [ ] **The addon** comes from the latest release zip, not from a clone of the repository or a remembered version
- [ ] **The plugin is enabled**, and `project.godot` has the `Tenjin` autoload exactly once
- [ ] **Two SDK keys**, selected with `OS.get_name()`, each belonging to the Tenjin app with that platform's bundle ID; placeholders are replaced
- [ ] **Android export preset** has `gradle_build/use_gradle_build=true`
- [ ] **iOS tracking description** (`tenjin/ios/tracking_usage_description`) is a user-facing message
- [ ] **iOS export preset** has `NSAdvertisingAttributionReportEndpoint` set to `https://tenjin-skan.com` in **Additional Plist Content**, not in Xcode
- [ ] **The ATT prompt** is requested once, before `connect_sdk()`, and not a second time if the game already asks
- [ ] **`connect_sdk()`** is called on every launch and on `NOTIFICATION_APPLICATION_RESUMED`
- [ ] **Consent, app store and settings calls** come before the first `connect_sdk()`
- [ ] **Custom events** are only sent after `connect_sdk()` has been called
- [ ] **Both platforms** were tested on a device or emulator: a 200 / `"success":true` response in the Android log, and events in the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics) for iOS

---

## 15. Common Mistakes to Avoid

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Copying `addons/tenjin` from a clone of the repository | It has no native binaries; the native SDK never loads | Use the release zip |
| Calling `Tenjin.connect()` | That is Godot's `Object.connect` for signals; it errors and sends nothing | Call `Tenjin.connect_sdk()` |
| One SDK key for both platforms | Each platform is a separate Tenjin app; the wrong key gets `unauthorized` | Select the key with `OS.get_name()` |
| Testing in the editor or on desktop | There is no native SDK there; every call is a no-op | Export to a device or emulator |
| Verifying on one platform only | The other platform uses a different key and app | Check Android and iOS separately |
| Android export without Gradle build | The Tenjin SDK is a Maven dependency and is left out | Enable **Use Gradle Build** |
| Editing `Info.plist` in the exported Xcode project | Godot regenerates the project on every export | Use the iOS preset's **Additional Plist Content** and the Tenjin project settings |
| Missing `NSAdvertisingAttributionReportEndpoint` | SKAdNetwork postbacks do not reach Tenjin | Add it to **Additional Plist Content** |
| `add_skadnetwork_ids` on while an ad SDK also writes `SKAdNetworkItems` | Duplicate `Info.plist` key | Turn the setting off and keep Tenjin's IDs in the other list |
| Calling `connect_sdk()` before the ATT answer on iOS | The first request has a zeroed IDFA | Connect after `tracking_authorization_received` |
| Adding a second ATT prompt | The game already asks elsewhere | Call `connect_sdk()` after the existing request |
| Calling `connect_sdk()` only on first launch | Tenjin needs session data on every launch; accounts may be suspended | Also connect on `NOTIFICATION_APPLICATION_RESUMED` |
| Passing an `Array` or a list to `opt_in()` / `opt_out()` | Those methods take no arguments | Use `opt_in_params()` / `opt_out_params()` with a `PackedStringArray` |
| Expecting URL-scheme links in `deep_link_received` | It only carries Tenjin deferred deep links | Handle URL-scheme links separately |
| Waiting on `attribution_info_failed` on Android | Android never emits it for a failed request | Don't block game logic on it |
| Sending events before `connect_sdk()` | Events will not be processed | Always call `connect_sdk()` first |
| Event names over 80 characters | Will be rejected | Keep event names concise |
| Exceeding 500 unique event names | Additional events will be dropped | Reuse event names with different values |
| Sending AdMob `value_micros` without platform branching | iOS reads it as currency units, Android as micros; revenue is off by 1,000,000x | Divide the micros value by 1,000,000 on iOS only |
| Relaunching within 30 seconds while testing | The native SDK skips the second connect and sends nothing | Wait 30 seconds, or clear app data / reinstall |

---

## 16. Full API Reference

All methods and signals are on the `Tenjin` autoload. Platform-only methods do nothing on the other platform.

### Signals

| Signal | Emitted when |
|--------|--------------|
| `tracking_authorization_received(status: int)` | After `request_tracking_authorization()`; `status` is a `Tenjin.TrackingStatus` |
| `attribution_info_received(info: Dictionary)` | After `get_attribution_info()` succeeds |
| `attribution_info_failed(error: String)` | After `get_attribution_info()` fails (iOS), or Tenjin is not initialized |
| `deep_link_received(params: Dictionary)` | A Tenjin deferred deep link, after `register_deep_link_handler()` |

### Core

| Method | Purpose |
|--------|---------|
| `initialize(sdk_key)` | Initialize SDK with the SDK key |
| `connect_sdk()` | Send install/session data |
| `connect_sdk_with_deferred_deeplink(url)` | Connect and report a deep link from a third-party service |
| `request_tracking_authorization()` | Show the iOS ATT prompt; emits `tracking_authorization_received` |
| `set_app_store(store)` | Android store: `Tenjin.AppStore.GOOGLE_PLAY`, `AMAZON` or `OTHER` |
| `is_available()` | Whether the native SDK is loaded |
| `append_app_subversion(subversion)` | A/B test variant tracking |

### Events & Revenue

| Method | Purpose |
|--------|---------|
| `event_with_name(name)` | Custom event (name only) |
| `event_with_name_and_value(name, value)` | Custom event with integer value |
| `transaction(product_name, currency_code, quantity, unit_price)` | Revenue without validation |
| `transaction_with_receipt(product_name, currency_code, quantity, unit_price, transaction_id, base64_receipt)` | Validated purchase (iOS) |
| `transaction_with_data_signature(product_name, currency_code, quantity, unit_price, purchase_data, data_signature)` | Validated purchase (Android) |
| `subscription(product_id, currency_code, unit_price, ios_…, android_…)` | Subscription tracking (iOS + Android) |
| `subscription_with_storekit(product_id, currency_code, unit_price)` | iOS 16+ StoreKit 2 subscription fetch; returns `""` on success or an error |

### SKAdNetwork (iOS)

| Method | Purpose |
|--------|---------|
| `update_postback_conversion_value(conversion_value, coarse_value = "", lock_window = false)` | Update SKAN conversion value |

### Privacy & Consent

| Method | Purpose |
|--------|---------|
| `opt_in()` / `opt_out()` | GDPR full opt-in/out |
| `opt_in_params(params)` / `opt_out_params(params)` | Granular parameter control (`PackedStringArray`) |
| `opt_in_out_using_cmp()` | Automatic CMP-based consent |
| `opt_in_google_dma()` / `opt_out_google_dma()` | Google DMA parameter control |
| `set_google_dma_parameters(ad_personalization, ad_user_data)` | Set Google DMA consent flags |

### Ad Revenue (ILRD)

| Method | Purpose |
|--------|---------|
| `event_ad_impression_applovin(impression)` | AppLovin impression |
| `event_ad_impression_admob(impression)` | AdMob impression |
| `event_ad_impression_ironsource(impression)` | Unity LevelPlay impression |
| `event_ad_impression_hyperbid(impression)` | HyperBid impression |
| `event_ad_impression_topon(impression)` | TopOn impression |
| `event_ad_impression_tradplus(impression)` | TradPlus impression |
| `event_ad_impression_cas(impression)` | CAS impression |
| `event_ad_impression_cloudx(impression)` | CloudX impression |

### Identity & Analytics

| Method | Purpose |
|--------|---------|
| `set_customer_user_id(user_id)` | Set custom user identifier |
| `get_customer_user_id()` | Get the stored user ID |
| `get_analytics_installation_id()` | Get persistent local analytics ID |
| `get_attribution_info()` | Request attribution data (paid feature); result via signals |
| `register_deep_link_handler()` | Listen for deferred deep links |
| `get_user_profile_dictionary()` | Get user metrics as a `Dictionary` |
| `reset_user_profile()` | Clear all local profile data |

### Configuration

| Method | Purpose |
|--------|---------|
| `set_cache_event_setting(enabled)` | Enable offline event caching |
| `set_encrypt_requests_setting(enabled)` | Enable request encryption |

---

## 17. How to Use This Document

**With any LLM:**

```
Add Tenjin to my Godot game using this guide:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/godot/llm-guide.md
```

**Keeping this document up to date:**

This guide is derived from the official [README.md](https://github.com/tenjin/tenjin-godot-sdk/blob/main/README.md) and the public API in [addons/tenjin/tenjin.gd](https://github.com/tenjin/tenjin-godot-sdk/blob/main/addons/tenjin/tenjin.gd). When the SDK is updated, review those sources and update this file accordingly.
