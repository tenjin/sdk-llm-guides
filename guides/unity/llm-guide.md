# Tenjin Unity SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin Unity SDK into a Unity project without requiring external documentation lookups.
>
> **Requirements:** Unity (iOS and Android supported)
>
> **Sources:**
> - Repository: [github.com/tenjin/tenjin-unity-sdk](https://github.com/tenjin/tenjin-unity-sdk)
> - Full README: [README.md](https://github.com/tenjin/tenjin-unity-sdk/blob/master/README.md)
>
> **Important:** Always check the [latest release](https://github.com/tenjin/tenjin-unity-sdk/releases) before integrating. Do not use hardcoded version numbers from this document.

---

## Before You Begin

### Check the Latest SDK Version

Before writing any integration code:

1. **Fetch the latest version** from [GitHub Releases](https://github.com/tenjin/tenjin-unity-sdk/releases).
2. **Do not hardcode** version numbers from this document — they may be outdated.

### Get the SDK Key

**Ask the developer for their Tenjin SDK key.** Every code example in this document uses `<SDK_KEY>` as a placeholder. Before writing any integration code, prompt the user:

> "What is your Tenjin SDK key? You can find it in the [Tenjin dashboard](https://www.tenjin.io/dashboard/organizations) on your app's page. Each app has up to 3 unique keys. If you don't have it handy, I can use a placeholder and you can fill it in later — just search your project for `TENJIN_SDK_KEY_PLACEHOLDER` to find it."

---

## 1. Installation

### Option A: Unity Package Manager (UPM) - Recommended

- Open `Packages/manifest.json`
- Locate the `"dependencies"` object
- Add the following entry if not there already:

```json
"com.tenjin.unity-sdk": "https://github.com/tenjin/tenjin-unity-sdk.git#1.16.3"
```

### Option B: Manual Installation

1. Download the latest `TenjinUnityPackage.unitypackage` from the [releases page](https://github.com/tenjin/tenjin-unity-sdk/releases).
2. Import it into your project: `Assets -> Import Package -> Custom Package`.

---

## 2. Platform Setup

### Android

If you distribute your app on the Google Play Store, add these dependencies. (If using External Dependency Manager, run `Assets > External Dependency Manager > Android Resolver > Force Resolve`).

**Permissions required in AndroidManifest.xml:**
```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
<!-- Required for API 32 (Android 13) and above -->
<uses-permission android:name="com.google.android.gms.permission.AD_ID"/>
```

**Gradle dependencies:**
```gradle
dependencies {
  implementation 'com.google.android.gms:play-services-ads-identifier:{version}'
  implementation 'com.android.installreferrer:installreferrer:{version}'
}
```

### iOS

Run `pod install` if you are exporting an iOS project. If using older Tenjin versions, ensure to remove `libTenjinSDK.a` before running pod install.

---

## 3. Core Initialization

Initialize and connect the SDK in a script that runs on startup (e.g., attached to a persistent GameObject).

```csharp
using UnityEngine;
using System;

public class TenjinManager : MonoBehaviour
{
    void Start()
    {
        BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");

        // Set App Store Type (googleplay, amazon, other, unspecified)
        #if UNITY_ANDROID
        instance.SetAppStoreType(AppStoreType.googleplay);
        #endif

        // Connect sends install/session data
#if UNITY_IOS
        if (new Version(UnityEngine.iOS.Device.systemVersion).CompareTo(new Version("14.0")) >= 0) {
            // Tenjin wrapper for requestTrackingAuthorization
            instance.RequestTrackingAuthorizationWithCompletionHandler((status) => {
                Debug.Log("App Tracking Transparency Authorization Status: " + status);
                instance.Connect();
            });
        } else {
            instance.Connect();
        }
#else
        instance.Connect();
#endif
    }
}
```

> **Critical:** `Connect()` must run on **every** app launch, not just the first launch.

---

## 4. GDPR & Privacy Compliance

You can automatically opt in or opt out based on CMP consents or granular parameters.

### Full Opt-In / Opt-Out

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");
instance.OptIn();
// OR
instance.OptOut();
instance.Connect();
```

### Granular Parameter Control

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");
// Only send specific parameters
List<string> optInParams = new List<string> {"ip_address", "advertising_id", "developer_device_id", "limit_ad_tracking", "referrer", "iad"};
instance.OptInParams(optInParams);
instance.Connect();
```

---

## 5. Purchase Event Tracking

Tenjin tracks in-app purchases using the `Transaction` method. You must pass receipt validation data for iOS/Android.

### Basic Purchase Event

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");
// Android (Google Play)
instance.Transaction(ProductId, CurrencyCode, Quantity, UnitPrice, null, Receipt, Signature);

// iOS
instance.Transaction(ProductId, CurrencyCode, Quantity, UnitPrice, TransactionId, Receipt, null);
```

---

## 6. Custom Events

> **Prerequisite:** `Connect()` must have been called before sending any custom events.
> **Limits:** Event names < 80 characters, maximum 500 unique names.

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");

// Event without value
instance.SendEvent("level_complete");

// Event with string value (must be an integer represented as a string)
instance.SendEvent("coins_spent", "50");
```

---

## 7. User Profile & Metrics

The SDK tracks user session metrics.

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");
Dictionary<string, string> profile = instance.GetUserProfileDictionary();

if (profile != null && profile.Count > 0)
{
    Debug.Log("Session Count: " + profile["session_count"]);
    Debug.Log("Total Session Time (ms): " + profile["total_session_time"]);
}
```

---

## 8. Customer User ID

```csharp
BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");
instance.SetCustomerUserId("user_123");
string userId = instance.GetCustomerUserId();
```