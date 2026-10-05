# Tenjin Unity SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin Unity SDK into a Unity project without requiring external documentation lookups, except for the version lookup below.
>
> **Requirements:** Unity 2020.3 or newer | iOS and Android builds | External Dependency Manager for Unity (EDM4U) for Android
>
> **Sources:**
> - Repository: [github.com/tenjin/tenjin-unity-sdk](https://github.com/tenjin/tenjin-unity-sdk)
> - Full README: [README.md](https://github.com/tenjin/tenjin-unity-sdk/blob/master/README.md)
> - Subscriptions: [SUBSCRIPTIONS_TRACKING.md](https://github.com/tenjin/tenjin-unity-sdk/blob/master/SUBSCRIPTIONS_TRACKING.md)
> - Releases: [github.com/tenjin/tenjin-unity-sdk/releases](https://github.com/tenjin/tenjin-unity-sdk/releases)

---

## Before You Begin

### Resolve the SDK Version

This document contains no SDK version number on purpose. The Unity package is installed from a Git tag, so a tag must be written into `Packages/manifest.json`. **Do not use a tag you remember**: versions recalled from training data are usually many releases old. Run this command and use its output wherever a snippet says `<TENJIN_SDK_VERSION>`:

```bash
curl -s https://api.github.com/repos/tenjin/tenjin-unity-sdk/releases/latest | sed -n 's/.*"tag_name": *"\([^"]*\)".*/\1/p'
```

Or, without the GitHub API:

```bash
git ls-remote --tags --refs https://github.com/tenjin/tenjin-unity-sdk.git | sed 's:.*refs/tags/::' | grep -E '^[0-9]+\.[0-9]+\.[0-9]+$' | sort -V | tail -1
```

If you cannot run commands, fetch `https://api.github.com/repos/tenjin/tenjin-unity-sdk/releases/latest` and read `tag_name`. If you can do neither, stop and ask the developer for the current version. Never leave `<TENJIN_SDK_VERSION>` in `manifest.json` and never guess.

### One App and One SDK Key per Platform

A Tenjin app is **one bundle ID / application ID on one platform**. A Unity project that builds for iOS and Android is therefore **two Tenjin apps with two SDK keys**, and the code must pick the right one per platform:

- Tenjin's servers look the app up by the platform and the bundle ID the request carries, then check that the SDK key belongs to that app. The iOS key is refused on Android and the Android key is refused on iOS.
- Anything that changes the bundle ID changes the Tenjin app: a separate identifier for development builds, or a different identifier per platform. Either register that ID as its own app in the Tenjin dashboard and use its key in those builds, or expect those builds to be rejected (see [Verify from the Device Log](#4-verify-from-the-device-log)).

Before writing code, read `applicationIdentifier` in `ProjectSettings/ProjectSettings.asset` (it can hold a different value per platform) and tell the developer which IDs the project produces.

### Get the SDK Keys

**Ask the developer for one Tenjin SDK key per platform the project builds for.** Code examples use `<IOS_SDK_KEY>` and `<ANDROID_SDK_KEY>` as placeholders (`<SDK_KEY>` where the platform does not matter). Before writing any integration code, prompt the user:

> "Tenjin needs one SDK key per platform. What is the SDK key of your iOS app (bundle ID `<the iOS bundle ID you found>`) and of your Android app (application ID `<the Android ID you found>`)? You can find each in the [Tenjin dashboard](https://www.tenjin.com/dashboard/organizations) on that app's page. If you don't have them handy, I can use placeholders and you can fill them in later — just search your project for `TENJIN_SDK_KEY_PLACEHOLDER` to find them."

If the developer provides the keys, substitute them directly in all generated code. If they prefer to add them later, use the literal strings `TENJIN_SDK_KEY_PLACEHOLDER_IOS` and `TENJIN_SDK_KEY_PLACEHOLDER_ANDROID` so they are easy to find with a project-wide search. If the project builds for one platform only, ask for that key only. Never copy a key from a sample project or from another app.

## Integration Workflow

Follow this two-step approach:

1. **First, integrate the basics.** Complete sections 1–4 (Installation, Platform Setup, Core Initialization, Verify from the Device Log). This gives the developer install tracking, session tracking, and ATT support — the foundation every Tenjin integration needs.

2. **Then, ask what else they need.** After the basic integration is working, prompt the user:

> "Tenjin basic integration is done (install tracking + ATT). Would you like to add any of these features?"
> - **Purchase tracking** — in-app purchases and subscriptions (Section 5)
> - **Custom events** — track in-app actions like level completions or signups (Section 6)
> - **SKAdNetwork conversion values** — for SKAN attribution on iOS (Section 7)
> - **GDPR / consent management** — opt-in/out, CMP, Google DMA (Section 8)
> - **Attribution info & deep links** — LiveOps attribution data, re-engagement deep links (Section 9)
> - **Ad revenue (ILRD)** — impression-level revenue from ad networks (Section 10, paid feature)
> - **User identity & analytics** — customer user IDs, user profile data (Section 11)

Only implement the sections the developer requests. Do not add features they didn't ask for.

---

## Quick Context

Tenjin is a mobile attribution and analytics platform. The SDK tracks app installs, sessions, in-app purchases, ad revenue, and custom events.

The Unity package wraps the native Tenjin iOS and Android SDKs. All calls go through a `BaseTenjin` instance returned by `Tenjin.getInstance(sdkKey)`. **In the Unity Editor the instance is a stub that only writes to the Console; nothing is sent to Tenjin.** The integration can only be verified in a build running on a device.

---

## 1. Installation

### Option A: Unity Package Manager (UPM) — Recommended

Open `Packages/manifest.json` and add this entry to the `"dependencies"` object. The package name is `com.tenjin.sdk`:

```json
"com.tenjin.sdk": "https://github.com/tenjin/tenjin-unity-sdk.git#<TENJIN_SDK_VERSION>"
```

Replace `<TENJIN_SDK_VERSION>` with the tag from [Resolve the SDK Version](#resolve-the-sdk-version). If a `com.tenjin.sdk` entry with an older tag is already there, update the tag instead of adding a second entry.

### Option B: Manual Installation

1. Download `TenjinUnityPackage.unitypackage` from the [releases page](https://github.com/tenjin/tenjin-unity-sdk/releases).
2. Import it into the project: `Assets -> Import Package -> Custom Package`.

### External Dependency Manager (Android)

On Android the package does not contain the native libraries. It declares them (the Tenjin Android SDK, `play-services-ads-identifier` and `play-services-appset`) in an `Editor/Dependencies.xml` file that the **External Dependency Manager for Unity (EDM4U)** resolves into the Gradle build. Without EDM4U the Android build has no Tenjin SDK in it.

- Check whether EDM4U is already installed: look for `Assets/ExternalDependencyManager/` or a `com.google.external-dependency-manager` entry in `Packages/manifest.json`. Most ad SDKs install it.
- If it is missing, ask the developer to install it (it is distributed by Google at [github.com/googlesamples/unity-jar-resolver](https://github.com/googlesamples/unity-jar-resolver)).
- After installing or updating the Tenjin package, run `Assets > External Dependency Manager > Android Resolver > Force Resolve` in the Editor so the Gradle dependencies match the package.

---

## 2. Platform Setup

### Android

**Permissions.** Make sure these are in the custom main manifest at `Assets/Plugins/Android/AndroidManifest.xml` (enable "Custom Main Manifest" in Player Settings > Publishing Settings if the file does not exist):

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<!-- Required to read the Advertising ID on Android 13+ (API 33) -->
<uses-permission android:name="com.google.android.gms.permission.AD_ID" />
```

**App store.** Set it in code with `SetAppStoreType` (Section 3). Without it the store is reported as `unspecified`.

**ProGuard / R8.** If minification is enabled (Player Settings > Publishing Settings > Minify), add these rules to the custom ProGuard file `Assets/Plugins/Android/proguard-user.txt`:

```
-keep class com.tenjin.** { *; }
-keep public class com.google.android.gms.ads.identifier.** { *; }
-keep public class com.google.android.gms.common.** { *; }
-keep public class com.google.android.gms.appset.** { *; }
-keep public class com.android.installreferrer.** { *; }
-keep class * extends java.util.ListResourceBundle {
    protected java.lang.Object[][] getContents();
}

# Keep the signatures that Gson/TypeToken rely on
-keepattributes Signature
-keepattributes *Annotation*

# General Gson/TypeToken protection
-keep class com.google.gson.reflect.TypeToken { *; }
-keep class * extends com.google.gson.reflect.TypeToken
```

### iOS

When Unity exports the Xcode project, the package's build post-processor embeds the Tenjin framework, links the system frameworks it needs, adds the `-ObjC` linker flag, and writes a default `NSUserTrackingUsageDescription` (the ATT prompt text) into `Info.plist`. No `pod install` is needed for Tenjin. If an older integration left `libTenjinSDK.a` or `libTenjinSDKUniversal.a` in the project, delete them.

Two things are left to you:

- **`NSAdvertisingAttributionReportEndpoint`** must be set to `https://tenjin-skan.com` so SKAdNetwork postbacks reach Tenjin. The package does not add it.
- **The ATT prompt text**, if the developer wants their own wording instead of the default.

Both are best set from an Editor script so they survive every export. Create `Assets/Editor/TenjinPlistPostProcessor.cs`:

```csharp
#if UNITY_IOS
using System.IO;
using UnityEditor;
using UnityEditor.Callbacks;
using UnityEditor.iOS.Xcode;

public static class TenjinPlistPostProcessor
{
    // Runs after the Tenjin package's own post-processor.
    [PostProcessBuild(1000)]
    public static void OnPostProcessBuild(BuildTarget target, string path)
    {
        if (target != BuildTarget.iOS)
        {
            return;
        }

        string plistPath = Path.Combine(path, "Info.plist");
        PlistDocument plist = new PlistDocument();
        plist.ReadFromFile(plistPath);

        plist.root.SetString("NSAdvertisingAttributionReportEndpoint", "https://tenjin-skan.com");
        plist.root.SetString("NSUserTrackingUsageDescription",
            "We use this data to provide a better and personalized ad experience.");

        File.WriteAllText(plistPath, plist.WriteToString());
    }
}
#endif
```

> If the project uses AppLovin MAX, its Unity plugin overwrites `NSAdvertisingAttributionReportEndpoint` with its own URL during the build. Either set the key back in Xcode after exporting, or ask the AppLovin account manager to forward postbacks to Tenjin.

---

## 3. Core Initialization

### Where Connect() Goes

- **On every launch and every return to the foreground**, not only on first open: in `Start()` of an object in the first scene and again in `OnApplicationPause(false)`. Tenjin needs the session data, and accounts that only connect on first open may be suspended.
- **On iOS, after the user has answered the tracking prompt.** Calling `Connect()` before the ATT answer sends a zeroed IDFA and degrades attribution.
- **If the game already has a tracking prompt, hook into it. Do not add a second one.** Search the project for `RequestAuthorizationTracking`, `RequestTrackingAuthorization` and `ATTrackingStatusBinding`. If the game already asks (for example through Unity's iOS 14 Advertising Support package or a consent SDK), call `instance.Connect()` after that existing request completes and leave out the Tenjin request below.

Calling `Connect()` on every resume is safe: the native SDKs skip a `Connect()` that comes within 30 seconds of the previous one.

### Recommended Implementation

Create `Assets/Scripts/TenjinManager.cs`:

```csharp
using System;
using UnityEngine;

public class TenjinManager : MonoBehaviour
{
    // One key per platform: an iOS app and an Android app are two Tenjin apps.
#if UNITY_IOS
    private const string SdkKey = "<IOS_SDK_KEY>";
#else
    private const string SdkKey = "<ANDROID_SDK_KEY>";
#endif

    private void Start()
    {
        DontDestroyOnLoad(gameObject);
        TenjinConnect();
    }

    private void OnApplicationPause(bool pauseStatus)
    {
        if (!pauseStatus)
        {
            TenjinConnect();
        }
    }

    private void TenjinConnect()
    {
        BaseTenjin instance = Tenjin.getInstance(SdkKey);

#if UNITY_ANDROID
        // googleplay, amazon or other
        instance.SetAppStoreType(AppStoreType.googleplay);
#endif

#if UNITY_IOS && !UNITY_EDITOR
        if (new Version(UnityEngine.iOS.Device.systemVersion).CompareTo(new Version("14.0")) >= 0)
        {
            // Shows the ATT prompt the first time; calls back at once afterwards.
            instance.RequestTrackingAuthorizationWithCompletionHandler((status) =>
            {
                instance.Connect();
            });
        }
        else
        {
            instance.Connect();
        }
#else
        instance.Connect();
#endif
    }
}
```

Attach `TenjinManager` to a GameObject in the **first scene** that loads.

If you cannot edit the scene file safely, let the script create its own object instead. Add this method to the class, and then do **not** also add the component to a scene:

```csharp
    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    private static void Bootstrap()
    {
        GameObject tenjinObject = new GameObject("TenjinManager");
        tenjinObject.AddComponent<TenjinManager>();
    }
```

To use the instance elsewhere (events, purchases), call `Tenjin.getInstance(...)` again with the **same key**; it returns the same instance.

### The TenjinObject Component

From package version 1.20.0 the SDK also ships a no-code component, `TenjinObject` (prefab at `Runtime/Prefabs/TenjinObject.prefab`). Dropped into the first scene, it initializes and connects on `Awake`, requests ATT on iOS, and exposes the SDK key, app store type, opt-in and debug-log settings in the Inspector.

It has **one** SDK key field, so it only fits a project that builds for a single platform. For a project that builds for both iOS and Android, use the script above.

---

## 4. Verify from the Device Log

Do this before adding any optional feature, **once per platform**: the two platforms use different keys and different Tenjin apps, so one passing does not prove the other.

**Play mode in the Editor proves nothing.** There the SDK is a stub that prints `Connecting ...` to the Console and sends no request. Build to a device.

### Android

Run on a device with Google Play services. The native SDK logs every request under the Logcat tag **`HttpConnection`** (not `TenjinSDK` and not `Unity`), and labels every request `Tenjin::connect` regardless of its type:

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

The Android SDK logs the response body, not the HTTP status. Match on the text in the table below.

### iOS

The native iOS SDK prints requests and responses only after debug logs are turned on. Call `DebugLogs()` before `Connect()` in development builds:

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");
if (Debug.isDebugBuild)
{
    instance.DebugLogs();
}
```

Run the exported project from Xcode and filter the console for `[Tenjin]`:

```text
[Tenjin] - LOG: Connect request
[Tenjin] - LOG: Got http response 200
[Tenjin] - DEBUG: Response body {"code":200,"success":true}
```

On iOS the line that decides is `Got http response <status>`. The iOS SDK prints no error for a rejected request, so read the status code. (`DebugLogs()` does nothing on Android; the Android lines above are always printed.)

### What the Response Means

| Response contains | HTTP status | Meaning | What to do |
|-------------------|-------------|---------|------------|
| `"success":true` | 200 | Accepted | Nothing. The integration works on this platform |
| `unauthorized` | 401 | The SDK key is unknown, or it is not the key of this app | Check the per-platform key selection: the iOS key on iOS, the Android key on Android, each from that app's page in the dashboard |
| `no such app` | 404 | There is no Tenjin app for this bundle ID on this platform | Create the app in the dashboard with exactly this ID, or fix the ID in Player Settings |
| `invalid device identifier` | 202 | The request carried no advertising ID | Android: add the `AD_ID` permission, run the EDM4U resolver, test on a device with Google Play services |
| `not logged` | 202 | The SDK key is disabled | Enable the key in the dashboard or use another key of the same app |
| `ignored` | 202 | The request was filtered by an app-version rule configured for the app | Check the app's version rules in the dashboard |

A 202 is **not** success: the request was received and dropped.

### No Request at All

A `Connect()` within 30 seconds of the previous one is skipped by the native SDK and sends nothing. The timestamp is stored on the device, so it survives an app restart.

- Android logs `Connect deduped by persisted timestamp` under the tag `TenjinSDK`. Wait 30 seconds or clear the app's data (`adb shell pm clear <applicationId>`).
- iOS logs `Connect sent ...s ago (interval: 30.0s), ignoring duplicate ping` with debug logs on. Wait 30 seconds or reinstall the app.
- On Android, a `ClassNotFoundException` for `com.tenjin.android.TenjinSDK` in Logcat means the native SDK is not in the build: EDM4U is missing or the resolver was not run.

### In the Dashboard

After a 200 response, the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics) shows events for devices registered as test devices.

---

## 5. Purchase Event Tracking

The same `Transaction` method serves iOS and Google Play. It takes seven arguments; pass `null` for the ones that belong to the other platform.

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");

// Android (Google Play): receipt and signature
instance.Transaction(productId, currencyCode, quantity, unitPrice, null, receipt, signature);

// iOS: transaction ID and receipt (the base64 receipt payload from Unity IAP)
instance.Transaction(productId, currencyCode, quantity, unitPrice, transactionId, receipt, null);

// Amazon Appstore
instance.TransactionAmazon(productId, currencyCode, quantity, unitPrice, receiptId, userId);
```

Argument types: `string productId, string currencyCode, int quantity, double unitPrice`, then strings.

**Notes:**
- For validation, add the App-Specific Shared Secret (iOS app), the Base64-encoded RSA public key (Google Play app) or the Amazon Shared Key in the Tenjin dashboard.
- On Google Play, acknowledge the purchase before sending it to Tenjin.
- With Unity IAP 5+, the receipt of a consumable is only available while the order is pending. Send it to Tenjin from the pending-order callback.

### Subscription Tracking

Subscriptions are **not** captured by `Connect()`. One of the methods below must be called from the purchase-handling code. Android support requires package version **1.18.0 or newer**. The same `Subscription` method serves both platforms — pass the iOS arguments on iOS and the Android arguments on Android, leaving the others `null`.

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");

// iOS — pass StoreKit 2 transaction data
instance.Subscription(
    productId, currencyCode, unitPrice,
    transactionId, originalTransactionId, receipt, skTransaction,  // iOS arguments
    null, null, null                                               // Android arguments
);

// iOS — or let the SDK fetch the StoreKit 2 transaction itself (iOS 16+, recommended for RevenueCat)
instance.SubscriptionWithStoreKit(productId, currencyCode, unitPrice);

// Android — pass Google Play purchase data
instance.Subscription(
    productId, currencyCode, unitPrice,
    null, null, null, null,                       // iOS arguments
    purchaseToken, purchaseData, dataSignature    // Android arguments (purchaseData = original JSON)
);
```

On Android, extract `purchaseData` (the original JSON) and `dataSignature` from the Unity IAP Google Play receipt `Payload`, and read `purchaseToken` from the original JSON. `SubscriptionWithStoreKit` is iOS-only and does nothing on Android.

**Notes:**
- **iOS:** add the app's **App-Specific Shared Secret** in the Tenjin dashboard. Send one transaction per billing interval (first charge and each renewal), and none during a free trial.
- **Android:** subscriptions are verified through the **Google Play Developer API**, so the Android app needs Google Play Developer API access configured in the Tenjin dashboard (a different credential from the RSA public key used for one-time purchases). Send **once per subscription**, not once per renewal: Tenjin resolves renewals, trials and cancellations from the purchase token.

---

## 6. Custom Events

> **Prerequisite:** `Connect()` must have been called before sending any custom events.
> **Limits:** Event names under 80 characters, maximum 500 unique names.

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");

// Event without value
instance.SendEvent("level_complete");

// Event with a value: an integer, passed as a string. A non-integer value is dropped.
instance.SendEvent("coins_spent", "50");
```

---

## 7. SKAdNetwork Conversion Values (iOS Only)

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");

#if UNITY_IOS
// Basic conversion value (0-63)
instance.UpdatePostbackConversionValue(5);

// With coarse value (iOS 16.1+ / SKAN 4.0): "low", "medium" or "high"
instance.UpdatePostbackConversionValue(5, "medium");

// With coarse value and lock window
instance.UpdatePostbackConversionValue(5, "high", true);
#endif
```

---

## 8. GDPR & Privacy Compliance

Call these after `Tenjin.getInstance(...)` and before `Connect()`.

### Full Opt-In / Opt-Out

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");

if (userConsented)
{
    instance.OptIn();
}
else
{
    instance.OptOut(); // No API requests will be sent
}

instance.Connect();
```

### Granular Parameter Control

```csharp
using System.Collections.Generic;

BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");

// Only send specific parameters
List<string> optInParams = new List<string> { "ip_address", "advertising_id", "developer_device_id", "limit_ad_tracking", "referrer", "iad" };
instance.OptInParams(optInParams);

// Or send everything EXCEPT these parameters
List<string> optOutParams = new List<string> { "locale", "timezone", "build_id" };
instance.OptOutParams(optOutParams);

instance.Connect();
```

### CMP-Based Consent

Opt in or out based on the CMP consent already stored on the device (TCF purpose 1). Returns `true` if opted in:

```csharp
bool optedIn = instance.OptInOutUsingCMP();
```

### Google DMA Parameters

```csharp
// Manual control
instance.SetGoogleDMAParameters(true, true); // (adPersonalization, adUserData)

// Toggle collection
instance.OptInGoogleDMA();  // default
instance.OptOutGoogleDMA();
```

---

## 9. Attribution Info & Deep Links

### Attribution Info (LiveOps Campaigns)

> **Note:** This is a paid feature. Contact your Tenjin account manager for access.

```csharp
using System.Collections.Generic;

BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");
instance.GetAttributionInfo((Dictionary<string, string> attributionInfoData) =>
{
    if (attributionInfoData.ContainsKey("ad_network"))
    {
        Debug.Log("Ad network: " + attributionInfoData["ad_network"]);
    }
    if (attributionInfoData.ContainsKey("campaign_name"))
    {
        Debug.Log("Campaign: " + attributionInfoData["campaign_name"]);
    }
});
```

Values are returned only when available. Other keys: `advertising_id`, `campaign_id`, `tenjin_parameter_0` … `tenjin_parameter_5`.

### Re-engagement Deep Links

Requires package version **1.21.0 or newer**. Report the URL the game was opened with, so re-engagement clicks can be attributed:

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");

// Link that launched the game
if (!string.IsNullOrEmpty(Application.absoluteURL))
{
    instance.HandleOpenUrl(Application.absoluteURL);
}

// Links received while the game is running
Application.deepLinkActivated += (url) => instance.HandleOpenUrl(url);
```

---

## 10. Impression Level Ad Revenue (ILRD)

> **Note:** ILRD is a paid feature. Contact your Tenjin account manager before implementing.

Call the subscribe method for your mediation once at startup. Each network also has a `...ImpressionFromJSON(json)` method if you build the payload yourself.

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");

// AppLovin MAX
instance.SubscribeAppLovinImpressions();

// Unity LevelPlay: one call per ad object
instance.SubscribeLevelPlayRewardedAdImpressions(rewardedAd);
instance.SubscribeLevelPlayInterstitialAdImpressions(interstitialAd);
instance.SubscribeLevelPlayBannerAdImpressions(bannerAd);

// AdMob: one call per ad object, with its ad unit ID
instance.SubscribeAdMobBannerViewImpressions(bannerView, adUnitId);
instance.SubscribeAdMobRewardedAdImpressions(rewardedAd, adUnitId);
instance.SubscribeAdMobInterstitialAdImpressions(interstitialAd, adUnitId);
instance.SubscribeAdMobRewardedInterstitialAdImpressions(rewardedInterstitialAd, adUnitId);

// HyperBid
instance.SubscribeHyperBidImpressions();

// TopOn
instance.SubscribeTopOnImpressions();

// CAS
instance.SubscribeCASImpressions(casManager);
instance.SubscribeCASBannerImpressions(bannerView);

// TradPlus
instance.SubscribeTradPlusImpressions();

// CloudX
instance.SubscribeCloudXImpressions();

// Any other mediation: JSON with network_name, currency and revenue_decimal or revenue_cpm
instance.CustomImpressionFromJSON(impressionJson);
```

---

## 11. User Identity & Analytics

### Customer User ID

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");
instance.SetCustomerUserId("user_123");
string userId = instance.GetCustomerUserId();
```

### Analytics Installation ID

A locally generated persistent identifier. It is a method, not a property:

```csharp
string analyticsId = instance.GetAnalyticsInstallationId();
```

### User Profile & Metrics

All values come back as strings (numbers and JSON included). Times are in milliseconds.

```csharp
using System.Collections.Generic;

BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");
Dictionary<string, string> profile = instance.GetUserProfileDictionary();

if (profile != null && profile.Count > 0)
{
    Debug.Log("Session Count: " + profile["session_count"]);
    Debug.Log("Total Session Time (ms): " + profile["total_session_time"]);
    Debug.Log("IAP Transaction Count: " + profile["iap_transaction_count"]);
    Debug.Log("Total ILRD Revenue USD: " + profile["total_ilrd_revenue_usd"]);
}

// Reset all profile data
instance.ResetUserProfile();
```

---

## 12. Additional Configuration

### A/B Testing with App Subversion

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");
instance.AppendAppSubversion(8888); // Reports as e.g. "1.0.1.8888"
instance.Connect();
```

### Event Caching (Offline Support)

```csharp
instance.SetCacheEventSetting(true);
```

The setting is stored on the device. Removing the call in a later release does not turn caching off; call `SetCacheEventSetting(false)` to disable it.

### Request Encryption

```csharp
instance.SetEncryptRequestsSetting(true);
```

---

## 13. Integration Checklist

When integrating Tenjin into a Unity project, verify these items:

- [ ] **SDK version** tag was resolved with the command in this guide, not from memory; no `<TENJIN_SDK_VERSION>` placeholder is left in `manifest.json`
- [ ] **The manifest key** is `com.tenjin.sdk`
- [ ] **EDM4U** is installed and the Android Resolver has been run
- [ ] **Two SDK keys**, selected with `#if UNITY_IOS` / `#else`, each belonging to the Tenjin app with that platform's bundle ID; placeholders are replaced
- [ ] **Android manifest** has `ACCESS_NETWORK_STATE` and `AD_ID` permissions
- [ ] **`SetAppStoreType`** is called on Android
- [ ] **iOS Info.plist** gets `NSAdvertisingAttributionReportEndpoint` set to `https://tenjin-skan.com` on export
- [ ] **The ATT prompt** is requested once, before `Connect()` on iOS
- [ ] **`Connect()`** is called in `Start()` and again in `OnApplicationPause(false)`
- [ ] **Custom events** are only sent after `Connect()` has been called
- [ ] **A device build on each platform** shows a 200 / `"success":true` response in the device log (the Editor sends nothing)
- [ ] Integration is verified using the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics)

---

## 14. Common Mistakes to Avoid

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Manifest key `com.tenjin.unity-sdk` | The package is named `com.tenjin.sdk`; Unity rejects a key that does not match | Use `"com.tenjin.sdk"` |
| Using a Git tag from memory | It is usually many releases old and lacks the APIs in this guide | Run the command in [Resolve the SDK Version](#resolve-the-sdk-version) |
| One SDK key for both platforms | Each platform is a separate Tenjin app; the wrong key gets `unauthorized` | Select the key with `#if UNITY_IOS` |
| Testing in the Editor | The Editor instance is a stub; nothing is sent | Build to a device and read the device log |
| No EDM4U, or resolver not run | The Android build has no Tenjin SDK and no Play services libraries | Install EDM4U and run Force Resolve |
| Missing `AD_ID` permission | No advertising ID: requests are rejected with `invalid device identifier` | Add it to the custom main manifest |
| Missing `NSAdvertisingAttributionReportEndpoint` | SKAdNetwork postbacks do not reach Tenjin | Set it from a post-process build script |
| Adding a second ATT prompt | The game already asks elsewhere | Call `Connect()` after the existing request |
| Calling `Connect()` only on first launch | Tenjin needs session data on every launch; accounts may be suspended | Call it in `Start()` and `OnApplicationPause(false)` |
| Calling `Tenjin.getInstance` with different keys in different scripts | Each key creates its own instance | Keep the key in one place |
| Passing a non-integer string to `SendEvent(name, value)` | The value is dropped | Pass an integer as a string, e.g. `"50"` |
| `instance.updatePostbackConversionValue(...)` | C# method names start with a capital letter | `UpdatePostbackConversionValue` |
| Sending events before `Connect()` | Events will not be processed | Always call `Connect()` first |
| Relaunching within 30 seconds while testing | The native SDK skips the second `Connect()` and sends nothing | Wait 30 seconds, or clear app data / reinstall |

---

## 15. Full API Reference

`Tenjin.getInstance(string sdkKey)` returns a `BaseTenjin`. All methods below are on that instance.

### Initialization

| Method | Purpose |
|--------|---------|
| `Connect()` | Send install/session data to Tenjin |
| `SetAppStoreType(AppStoreType)` | Android store: `googleplay`, `amazon`, `other` |
| `RequestTrackingAuthorizationWithCompletionHandler(Action<int>)` | Request ATT permission (iOS) |
| `DebugLogs()` | Turn on native debug logs (iOS) |
| `AppendAppSubversion(int)` | A/B test variant tracking |

### Events & Revenue

| Method | Purpose |
|--------|---------|
| `SendEvent(string)` | Custom event (name only) |
| `SendEvent(string, string)` | Custom event with an integer value as a string |
| `Transaction(string, string, int, double, string, string, string)` | Purchase with validation (iOS and Google Play) |
| `TransactionAmazon(string, string, int, double, string, string)` | Amazon purchase |
| `Subscription(...)` | Subscription tracking (ten arguments, iOS and Android) |
| `SubscriptionWithStoreKit(string, string, double)` | iOS-only native StoreKit 2 subscription fetch |

### SKAdNetwork (iOS)

| Method | Purpose |
|--------|---------|
| `UpdatePostbackConversionValue(int)` | Set basic conversion value (0-63) |
| `UpdatePostbackConversionValue(int, string)` | Set with coarse value |
| `UpdatePostbackConversionValue(int, string, bool)` | Set with coarse value and lock window |

### Privacy & Consent

| Method | Purpose |
|--------|---------|
| `OptIn()` / `OptOut()` | GDPR full opt-in/out |
| `OptInParams(List<string>)` / `OptOutParams(List<string>)` | Granular parameter control |
| `OptInOutUsingCMP()` | Automatic CMP-based consent |
| `OptInGoogleDMA()` / `OptOutGoogleDMA()` | Google DMA parameter control |
| `SetGoogleDMAParameters(bool, bool)` | Set Google DMA consent flags |

### Attribution & Deep Links

| Method | Purpose |
|--------|---------|
| `GetAttributionInfo(Tenjin.AttributionInfoDelegate)` | Attribution data (paid feature) |
| `GetDeeplink(Tenjin.DeferredDeeplinkDelegate)` | Deferred deep link data (paid feature) |
| `HandleOpenUrl(string)` | Report an app-open deep link |

### Ad Revenue (ILRD)

| Method | Purpose |
|--------|---------|
| `SubscribeAppLovinImpressions()` | AppLovin MAX |
| `SubscribeLevelPlayRewardedAdImpressions(object)` | Unity LevelPlay (also `...InterstitialAd...`, `...BannerAd...`) |
| `SubscribeAdMobBannerViewImpressions(object, string)` | AdMob (also `...RewardedAd...`, `...InterstitialAd...`, `...RewardedInterstitialAd...`) |
| `SubscribeHyperBidImpressions()` | HyperBid |
| `SubscribeTopOnImpressions()` | TopOn |
| `SubscribeCASImpressions(object)` | CAS |
| `SubscribeTradPlusImpressions()` | TradPlus |
| `SubscribeCloudXImpressions()` | CloudX |
| `CustomImpressionFromJSON(string)` | Any other mediation |

### Identity & Analytics

| Method | Purpose |
|--------|---------|
| `SetCustomerUserId(string)` | Set custom user identifier |
| `GetCustomerUserId()` | Retrieve stored user ID |
| `GetAnalyticsInstallationId()` | Get persistent local analytics ID |
| `GetUserProfileDictionary()` | Get user metrics as `Dictionary<string, string>` |
| `ResetUserProfile()` | Clear all local profile data |

### Configuration

| Method | Purpose |
|--------|---------|
| `SetCacheEventSetting(bool)` | Enable offline event caching |
| `SetEncryptRequestsSetting(bool)` | Enable request encryption |

---

## 16. How to Use This Document

**With any LLM:**

```
Add Tenjin to my Unity project using this guide:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/unity/llm-guide.md
```

**Keeping this document up to date:**

This guide is derived from the official [README.md](https://github.com/tenjin/tenjin-unity-sdk/blob/master/README.md) and the public API in [BaseTenjin.cs](https://github.com/tenjin/tenjin-unity-sdk/blob/master/Runtime/BaseTenjin.cs). When the SDK is updated, review those sources and update this file accordingly.
