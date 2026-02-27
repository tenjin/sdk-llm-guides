# Tenjin React Native SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin React Native SDK into a React Native project without requiring external documentation lookups.
>
> **Requirements:** React Native >= 0.60 | iOS 14.0+ | Android API 21+
>
> **Sources:**
> - Repository: [github.com/tenjin/react-native-tenjin](https://github.com/tenjin/react-native-tenjin)
> - Full README: [README.md](https://github.com/tenjin/react-native-tenjin/blob/master/README.md)
> - npm: [react-native-tenjin](https://www.npmjs.com/package/react-native-tenjin)
>
> **Important:** Always check the [latest release](https://www.npmjs.com/package/react-native-tenjin) before integrating. Do not use hardcoded version numbers from this document — fetch the current version from npm.

---

## Before You Begin

### Check the Latest SDK Version

Before writing any integration code:

1. **Fetch the latest version** from [npm](https://www.npmjs.com/package/react-native-tenjin)
2. **Use that version** in your `package.json` declaration
3. **Do not hardcode** version numbers from this document — they may be outdated

### Get the SDK Key

**Ask the developer for their Tenjin SDK key.** Every code example in this document uses `<SDK_KEY>` as a placeholder. Before writing any integration code, prompt the user:

> "What is your Tenjin SDK key? You can find it in the [Tenjin dashboard](https://www.tenjin.io/dashboard/organizations) on your app's page. Each app has up to 3 unique keys. If you don't have it handy, I can use a placeholder and you can fill it in later — just search your project for `TENJIN_SDK_KEY_PLACEHOLDER` to find it."

If the developer provides their key, substitute it directly in all generated code. If they prefer to add it later, use the literal string `TENJIN_SDK_KEY_PLACEHOLDER` so it is easy to find with a project-wide search.

## Integration Workflow

Follow this two-step approach:

1. **First, integrate the basics.** Complete sections 1–4 (Installation, iOS Setup, Android Setup, Core Initialization). This gives the developer install tracking, session tracking, and ATT support — the foundation every Tenjin integration needs.

2. **Then, ask what else they need.** After the basic integration is working, prompt the user:

> "Tenjin basic integration is done (install tracking + ATT). Would you like to add any of these features?"
> - **Purchase tracking** — track in-app purchases (Section 5)
> - **Custom events** — track in-app actions like level completions or signups (Section 6)
> - **SKAdNetwork conversion values** — for SKAN attribution on iOS (Section 7)
> - **GDPR / consent management** — opt-in/out, granular parameter control (Section 8)
> - **Deep linking** — handle attribution deep links (Section 9)
> - **Ad revenue (ILRD)** — impression-level revenue from ad networks (Section 10, paid feature)
> - **User identity** — customer user IDs (Section 11)

Only implement the sections the developer requests. Do not add features they didn't ask for.

---

## Quick Context

Tenjin is a mobile attribution and analytics platform. The SDK tracks app installs, sessions, in-app purchases, ad revenue, and custom events. It integrates with Apple's ATT framework and SKAdNetwork for privacy-compliant attribution on iOS, and supports Google Play, Amazon, and other stores on Android.

---

## 1. Installation

Add the dependency to your `package.json`:

```bash
npm install react-native-tenjin --save
```

If you are using a React Native version older than 0.60, you may need to link it:

```bash
react-native link react-native-tenjin
```

---

## 2. iOS Platform Setup

### Info.plist Configuration

Add the `NSUserTrackingUsageDescription` key to `ios/YourAppName/Info.plist`. This is required for the ATT prompt on iOS 14+.

```xml
<key>NSUserTrackingUsageDescription</key>
<string>We use this data to provide a better and personalized ad experience.</string>
```

### Pod Installation

After adding the package, run:

```bash
cd ios && pod install
```

---

## 3. Android Platform Setup

### Gradle Dependencies

In your `android/app/build.gradle`, add the following dependencies. These are required for attribution (Install Referrer) and device identifiers (AAID).

```gradle
dependencies {
    // Required for Google Play Install Referrer
    implementation "com.android.installreferrer:installreferrer:2.2"
    
    // Required for Advertising ID (AAID)
    implementation "com.google.android.gms:play-services-ads-identifier:18.0.1"
}
```

### AndroidManifest.xml Configuration

Ensure you have the following permissions and meta-data in `android/app/src/main/AndroidManifest.xml`:

```xml
<manifest ...>
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    
    <!-- Required for Android 13+ (API 33) -->
    <uses-permission android:name="com.google.android.gms.permission.AD_ID" />

    <application ...>
        <!-- Specify target app store (googleplay, amazon, or other) -->
        <meta-data android:name="TENJIN_APP_STORE" android:value="googleplay" />
        ...
    </application>
</manifest>
```

### ProGuard Rules

If using code obfuscation, add these rules to `android/app/proguard-rules.pro`:

```
-keep class com.tenjin.** { *; }
-keep public class com.google.android.gms.ads.identifier.** { *; }
-keep public class com.google.android.gms.common.** { *; }
-keep public class com.android.installreferrer.** { *; }
-keepattributes *Annotation*
```

---

## 4. Core Initialization

### Best Practice: Request ATT Then Connect

On iOS 14+, Apple requires the ATT prompt before accessing the IDFA. The **recommended** pattern is to request tracking authorization first (e.g., using `react-native-permissions`), then call `initialize()` and `connect()`.

> **Critical:** `connect()` must run on **every** app launch, not just the first launch.

### Recommended Implementation

```javascript
import { Platform } from 'react-native';
import Tenjin from 'react-native-tenjin';
import { request, PERMISSIONS } from 'react-native-permissions';

const initializeTenjin = async () => {
  // 1. Initialize with API key
  Tenjin.initialize('<SDK_KEY>');

  // 2. Set App Store type for Android if not set via Manifest (defaults to googleplay)
  if (Platform.OS === 'android') {
    Tenjin.setAppStore('googleplay'); // googleplay, amazon, other
  }

  // 3. Connect (sends install/session data)
  Tenjin.connect();
};

const setupTenjin = async () => {
  if (Platform.OS === 'ios') {
    // Request tracking authorization first for higher attribution quality
    await request(PERMISSIONS.IOS.APP_TRACKING_TRANSPARENCY);
  }
  await initializeTenjin();
};
```

### Using in Your App

Call the setup early in your app lifecycle:

```javascript
import React, { useEffect } from 'react';

const App = () => {
  useEffect(() => {
    setupTenjin();
  }, []);

  return (
    // Your UI
  );
};
```

---

## 5. Purchase Event Tracking

### Register Transaction

Tenjin tracks in-app purchases using the `transaction` method. Note that for native React Native validation, you typically pass the basic product info.

```javascript
Tenjin.transaction(
  'product_identifier', // productName
  'USD',                // currencyCode
  1,                    // quantity
  9.99                  // unitPrice (Number)
);
```

---

## 6. Custom Events

> **Prerequisite:** `connect()` must have been called before sending any custom events.

```javascript
// Event without value
Tenjin.eventWithName('level_complete');

// Event with name and value
// Note: value must be a string representing the value/count
Tenjin.eventWithNameAndValue('coins_spent', '50');
```

**Limits:**
- Event names must be under **80 characters**
- Maximum **500 unique** event names per app

---

## 7. SKAdNetwork Conversion Values (iOS Only)

Tenjin supports updating SKAN conversion values with support for coarse values and locking windows (iOS 16.1+ / SKAN 4.0).

```javascript
import Tenjin from 'react-native-tenjin';

// Basic conversion value (0-63)
Tenjin.updatePostbackConversionValue(5);

// With coarse value (low, medium, high)
Tenjin.updatePostbackConversionValue(5, 'medium');

// With coarse value and lock window
Tenjin.updatePostbackConversionValue(5, 'high', true);
```

---

## 8. GDPR & Privacy Compliance

### Full Opt-In / Opt-Out

```javascript
// Completely opt-in or out
Tenjin.optIn();
Tenjin.optOut();
```

### Granular Parameter Control

```javascript
// Only send these specific parameters
Tenjin.optIn([
  'ip_address',
  'advertising_id',
  'developer_device_id',
]);

// Or send everything EXCEPT these parameters
Tenjin.optOut([
  'locale',
  'timezone',
]);
```

---

## 9. Deep Linking

Retrieve deferred deep link data through the attribution info. This allows you to handle campaigns that deep link the user into specific app content.

```javascript
Tenjin.getAttributionInfo(
  (attributionInfo) => {
    if (attributionInfo && attributionInfo['clicked_tenjin_link'] === true) {
      const campaign = attributionInfo['campaign_name'];
      const adset = attributionInfo['adset_name'];
      // Handle deep link logic here
    }
  },
  () => {
    console.error('Attribution info failed');
  }
);
```

> **Note:** `getAttributionInfo()` is a paid feature. Contact your Tenjin account manager for access.

---

## 10. Impression Level Ad Revenue (ILRD)

> **Note:** ILRD is a paid feature. Contact your Tenjin account manager before implementing.

Pass the JSON object directly from the ad network's callback. The SDK will handle the parsing.

```javascript
// AppLovin MAX
Tenjin.eventAdImpressionAppLovin(adInfoJson);

// AdMob
Tenjin.eventAdImpressionAdMob(adValueJson);

// Unity LevelPlay (IronSource)
Tenjin.eventAdImpressionIronSource(impressionDataJson);

// HyperBid
Tenjin.eventAdImpressionHyperBid(impressionDataJson);

// TopOn
Tenjin.eventAdImpressionTopOn(impressionDataJson);
```

---

## 11. User Identity

### Customer User ID

Useful for cross-referencing Tenjin data with your own backend user IDs.

```javascript
// Set custom user identifier
Tenjin.setCustomerUserId('user_123');

// Retrieve stored user ID via callback
Tenjin.getCustomerUserId((userId) => {
  console.log('Current Tenjin Customer User ID:', userId);
});
```

---

## 12. Additional Configuration

### A/B Testing with App Subversion

Allows you to track different versions or variants of your app within the same Tenjin app ID.

```javascript
Tenjin.appendAppSubversion(8888); // Reports as e.g. "1.0.1.8888"
```

---

## 13. Integration Checklist

When integrating Tenjin into a React Native project, verify these items:

- [ ] **SDK version** is the latest from [npm](https://www.npmjs.com/package/react-native-tenjin)
- [ ] **iOS Info.plist** has `NSUserTrackingUsageDescription` with a user-facing message
- [ ] **Pod install** was run successfully in the `ios` directory
- [ ] **Android build.gradle** includes `installreferrer` and `play-services-ads-identifier`
- [ ] **Android Manifest** has `AD_ID` permission for Android 13+
- [ ] **ATT prompt** is requested (if using IDFA) before calling `connect()` on iOS 14+
- [ ] **`connect()`** is called on **every** app launch, not just the first
- [ ] **Custom events** are only sent after `connect()` has been called
- [ ] **`<SDK_KEY>`** placeholder is replaced with the actual key from the Tenjin dashboard
- [ ] **ProGuard rules** are added if using Android code obfuscation
- [ ] Integration is verified using the [Live Test Device Data Tool](https://www.tenjin.io/dashboard/sdk_diagnostics)

---

## 14. Common Mistakes to Avoid

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Calling `connect()` only on first launch | Tenjin needs session data on every launch; accounts may be suspended | Call `connect()` in your app initialization on every launch |
| Missing `AD_ID` permission on Android | Cannot access AAID on Android 13+, degrades attribution quality | Add the permission to AndroidManifest.xml |
| Forgetting `installreferrer` dependency | No Google Play install attribution | Add `installreferrer` to Android build.gradle |
| Sending events before `connect()` | Events will not be processed | Always call `connect()` first |
| Event names over 80 characters | Will be rejected | Keep event names concise |
| Exceeding 500 unique event names | Additional events will be dropped | Reuse event names with different values |

---

## 15. Full API Reference

### Core

| Method | Purpose |
|--------|---------|
| `initialize(apiKey)` | Initialize SDK with API key |
| `connect()` | Send install/session data |
| `setAppStore(type)` | Set Android store (googleplay, amazon, other) |

### Events & Revenue

| Method | Purpose |
|--------|---------|
| `eventWithName(name)` | Custom event (name only) |
| `eventWithNameAndValue(name, value)` | Custom event with string value |
| `transaction(product, currency, qty, price)` | Revenue tracking |

### SKAdNetwork (iOS)

| Method | Purpose |
|--------|---------|
| `updatePostbackConversionValue(val, [coarse], [lock])` | Update SKAN conversion value |

### Privacy & Identity

| Method | Purpose |
|--------|---------|
| `optIn()` / `optOut()` | GDPR full opt-in/out |
| `optIn(params)` / `optOut(params)` | Granular parameter control |
| `setCustomerUserId(userId)` | Set custom user identifier |
| `getCustomerUserId(callback)` | Retrieve stored user ID |
| `getAttributionInfo(success, error)` | Get attribution data (paid feature) |

---

## 16. How to Use This Document

**With any LLM:**

```
Add Tenjin to my React Native app using this guide:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/react-native/llm-guide.md
```
