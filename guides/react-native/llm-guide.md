# Tenjin React Native SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin React Native SDK into a React Native project (bare or Expo) without requiring external documentation lookups, except for the version lookup below.
>
> **Requirements:** iOS 12.0+ and Android API 21+, or higher if your React Native version requires it. Not usable in Expo Go: Expo projects need a development build.
>
> **Sources:**
> - Repository: [github.com/tenjin/tenjin-react-native-sdk](https://github.com/tenjin/tenjin-react-native-sdk)
> - Full README: [README.md](https://github.com/tenjin/tenjin-react-native-sdk/blob/master/README.md)
> - Subscriptions: [SUBSCRIPTIONS_TRACKING.md](https://github.com/tenjin/tenjin-react-native-sdk/blob/master/SUBSCRIPTIONS_TRACKING.md)
> - npm: [react-native-tenjin](https://www.npmjs.com/package/react-native-tenjin)

---

## Before You Begin

### Resolve the SDK Version

This document contains no SDK version number on purpose. **Do not use a version you remember**: versions recalled from training data are usually many releases old, and do not write a version into `package.json` by hand.

The install commands in Section 1 resolve the current version from npm. To see it:

```bash
npm view react-native-tenjin version
```

If you cannot run commands, fetch `https://registry.npmjs.org/react-native-tenjin/latest` and read `version`. If you can do neither, stop and ask the developer for the current version. Never guess.

The Google libraries Tenjin needs on Android are resolved from Google's Maven repository. Use the output wherever a snippet says `<ADS_IDENTIFIER_VERSION>` or `<APPSET_VERSION>`:

```bash
for a in com/google/android/gms/play-services-ads-identifier com/google/android/gms/play-services-appset; do
  printf '%s ' "$a"
  curl -s "https://dl.google.com/dl/android/maven2/$a/maven-metadata.xml" | sed -n 's:.*<release>\(.*\)</release>.*:\1:p'
done
```

If the project already declares one of these libraries (ad SDKs usually bring `play-services-ads-identifier`), keep the version the project has.

### One App and One SDK Key per Platform

A Tenjin app is **one bundle ID / application ID on one platform**. A React Native project that ships on iOS and Android is therefore **two Tenjin apps with two SDK keys**, and the code must pick the right one at runtime:

- Tenjin's servers look the app up by the platform and the bundle ID the request carries, then check that the SDK key belongs to that app. The iOS key is refused on Android and the Android key is refused on iOS.
- Anything that changes the bundle ID changes the Tenjin app: an Android `applicationIdSuffix ".debug"`, a product flavor, or an iOS configuration with its own `PRODUCT_BUNDLE_IDENTIFIER`. Either register that ID as its own app in the Tenjin dashboard and use its key in those builds, or expect those builds to be rejected (see [Verify from the Device Log](#5-verify-from-the-device-log)).

Before writing code, find the IDs the project produces and tell the developer:

- Bare React Native: `applicationId` (and suffixes/flavors) in `android/app/build.gradle`, `PRODUCT_BUNDLE_IDENTIFIER` in `ios/<App>.xcodeproj/project.pbxproj`.
- Expo: `android.package` and `ios.bundleIdentifier` in `app.json` / `app.config.js`.

### Get the SDK Keys

**Ask the developer for one Tenjin SDK key per platform the project builds for.** Code examples use `<IOS_SDK_KEY>` and `<ANDROID_SDK_KEY>` as placeholders (`<SDK_KEY>` where the platform does not matter). Before writing any integration code, prompt the user:

> "Tenjin needs one SDK key per platform. What is the SDK key of your iOS app (bundle ID `<the iOS bundle ID you found>`) and of your Android app (application ID `<the Android ID you found>`)? You can find each in the [Tenjin dashboard](https://www.tenjin.com/dashboard/organizations) on that app's page. If you don't have them handy, I can use placeholders and you can fill them in later — just search your project for `TENJIN_SDK_KEY_PLACEHOLDER` to find them."

If the developer provides the keys, substitute them directly in all generated code. If they prefer to add them later, use the literal strings `TENJIN_SDK_KEY_PLACEHOLDER_IOS` and `TENJIN_SDK_KEY_PLACEHOLDER_ANDROID` so they are easy to find with a project-wide search. If the project builds for one platform only, ask for that key only. Never copy a key from a sample project or from another app.

## Integration Workflow

Follow this two-step approach:

1. **First, integrate the basics.** Complete sections 1–5 (Installation, iOS Setup, Android Setup, Core Initialization, Verify from the Device Log). This gives the developer install tracking, session tracking, and ATT support — the foundation every Tenjin integration needs.

2. **Then, ask what else they need.** After the basic integration is working, prompt the user:

> "Tenjin basic integration is done (install tracking + ATT). Would you like to add any of these features?"
> - **Purchase tracking** — in-app purchases and subscriptions (Section 6)
> - **Custom events** — track in-app actions like level completions or signups (Section 7)
> - **SKAdNetwork conversion values** — for SKAN attribution on iOS (Section 8)
> - **GDPR / consent management** — opt-in/out, CMP, Google DMA (Section 9)
> - **Attribution info & deep links** — LiveOps attribution data, re-engagement deep links (Section 10)
> - **Ad revenue (ILRD)** — impression-level revenue from ad networks (Section 11, paid feature)
> - **User identity & analytics** — customer user IDs, analytics IDs, user profile (Section 12)
> - **Google Ads conversion measurement (ICM / ODM)** — iOS only, for apps that run Google Ads campaigns (Section 14)

Only implement the sections the developer requests. Do not add features they didn't ask for.

---

## Quick Context

Tenjin is a mobile attribution and analytics platform. The SDK tracks app installs, sessions, in-app purchases, ad revenue, and custom events. It integrates with Apple's ATT framework and SKAdNetwork for privacy-compliant attribution on iOS, and supports Google Play, Amazon, and other stores on Android.

`react-native-tenjin` is a native module that wraps the Tenjin iOS and Android SDKs. It has a single default export, `Tenjin`. It has **no** App Tracking Transparency call of its own and **no** Expo config plugin.

---

## 1. Installation

First decide which kind of project this is: if `package.json` depends on `expo` and there is no committed `android/` or `ios/` folder, it is an Expo project using prebuild; follow the Expo steps. Otherwise follow the bare steps.

### Bare React Native

```bash
npm install react-native-tenjin@latest
cd ios && pod install
```

(or `yarn add react-native-tenjin@latest`). The package autolinks; do not run `react-native link`.

### Expo

`react-native-tenjin` contains native code, so it does **not** work in Expo Go. Use a development build:

```bash
npx expo install react-native-tenjin
npx expo install expo-tracking-transparency expo-build-properties
npx expo prebuild
npx expo run:ios      # or: npx expo run:android, or an EAS development build
```

With Expo, do **not** edit `android/` or `ios/` by hand: they are regenerated. All native configuration goes through `app.json` / `app.config.js` as shown in Sections 2 and 3.

The import is the same in both cases:

```javascript
import Tenjin from 'react-native-tenjin';
```

---

## 2. iOS Platform Setup

Two `Info.plist` keys are needed:

- `NSUserTrackingUsageDescription`: the text of the ATT prompt (iOS 14+). The app crashes on the ATT request if it is missing.
- `NSAdvertisingAttributionReportEndpoint`: set to `https://tenjin-skan.com` so SKAdNetwork postbacks reach Tenjin (iOS 15+).

### Bare React Native

Add to `ios/<YourApp>/Info.plist`:

```xml
<key>NSUserTrackingUsageDescription</key>
<string>We use this data to provide a better and personalized ad experience.</string>

<key>NSAdvertisingAttributionReportEndpoint</key>
<string>https://tenjin-skan.com</string>
```

Then run `cd ios && pod install`.

### Expo

Add to `app.json`:

```json
{
  "expo": {
    "ios": {
      "bundleIdentifier": "com.example.app",
      "infoPlist": {
        "NSAdvertisingAttributionReportEndpoint": "https://tenjin-skan.com"
      }
    },
    "plugins": [
      [
        "expo-tracking-transparency",
        {
          "userTrackingPermission": "We use this data to provide a better and personalized ad experience."
        }
      ]
    ]
  }
}
```

---

## 3. Android Platform Setup

The package depends on the Tenjin Android SDK but **not** on the Google libraries that SDK reads the device identifiers from. The app must add them. If they are missing the build still succeeds, but requests go out without an advertising ID and are rejected with `invalid device identifier`.

### Bare React Native

In `android/app/build.gradle`:

```gradle
dependencies {
    // Required for the Advertising ID (AAID)
    implementation "com.google.android.gms:play-services-ads-identifier:<ADS_IDENTIFIER_VERSION>"

    // Required for the App Set ID
    implementation "com.google.android.gms:play-services-appset:<APPSET_VERSION>"
}
```

The Google Play Install Referrer library comes with the Tenjin Android SDK and does not need to be declared.

In `android/app/src/main/AndroidManifest.xml`:

```xml
<manifest>
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <!-- Required to read the Advertising ID on Android 13+ (API 33) -->
    <uses-permission android:name="com.google.android.gms.permission.AD_ID" />
</manifest>
```

The app's `minSdkVersion` must be 21 or higher.

If the release build is minified, add these rules to `android/app/proguard-rules.pro`:

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

### Expo

Permissions go in `app.json`:

```json
{
  "expo": {
    "android": {
      "package": "com.example.app",
      "permissions": [
        "android.permission.INTERNET",
        "android.permission.ACCESS_NETWORK_STATE",
        "com.google.android.gms.permission.AD_ID"
      ]
    },
    "plugins": ["./plugins/withTenjin"]
  }
}
```

The Gradle dependencies need a small local config plugin, because `android/app/build.gradle` is generated. Create `plugins/withTenjin.js`:

```javascript
const { withAppBuildGradle } = require('expo/config-plugins');

const DEPENDENCIES = [
  "implementation 'com.google.android.gms:play-services-ads-identifier:<ADS_IDENTIFIER_VERSION>'",
  "implementation 'com.google.android.gms:play-services-appset:<APPSET_VERSION>'",
];

module.exports = function withTenjin(config) {
  return withAppBuildGradle(config, (gradleConfig) => {
    for (const line of DEPENDENCIES) {
      if (!gradleConfig.modResults.contents.includes(line)) {
        gradleConfig.modResults.contents = gradleConfig.modResults.contents.replace(
          /dependencies\s*\{/,
          (match) => `${match}\n    ${line}`
        );
      }
    }
    return gradleConfig;
  });
};
```

Keep both plugin entries (`expo-tracking-transparency` from Section 2 and `./plugins/withTenjin`) in the same `plugins` array. For a minified release build, pass the ProGuard rules above through the `expo-build-properties` plugin (`android.extraProguardRules`). Run `npx expo prebuild` again after changing `app.json` or the plugin.

---

## 4. Core Initialization

### Where connect() Goes

- **On every launch and every return to the foreground**, not only on first open. Tenjin needs the session data, and accounts that only connect on first open may be suspended.
- **On iOS, after the user has answered the tracking prompt.** Calling `connect()` before the ATT answer sends a zeroed IDFA and degrades attribution.
- **Request ATT only when the app is active.** iOS shows the prompt only while the app is in the foreground and active.
- **If the app already has a tracking prompt, hook into it. Do not add a second one.** Search the project for `APP_TRACKING_TRANSPARENCY`, `requestTrackingPermissionsAsync` and `requestTrackingAuthorization`. If the app already asks, call `Tenjin.connect()` after that existing request resolves and leave out the request below.

Calling `connect()` on every return to the foreground is safe: the native SDKs skip a `connect()` that comes within 30 seconds of the previous one.

### Recommended Implementation (Bare React Native)

`react-native-tenjin` has no ATT call. This example uses `react-native-permissions`, which must be installed and set up according to its own README (it needs the `AppTrackingTransparency` permission enabled in the Podfile). Any other ATT library works the same way: await its request, then call `Tenjin.connect()`.

```javascript
import { useEffect } from 'react';
import { AppState, Platform } from 'react-native';
import Tenjin from 'react-native-tenjin';
import { request, PERMISSIONS } from 'react-native-permissions';

// One key per platform: an iOS app and an Android app are two Tenjin apps.
const TENJIN_SDK_KEY = Platform.OS === 'android' ? '<ANDROID_SDK_KEY>' : '<IOS_SDK_KEY>';

let initialized = false;
let connecting = false;

async function connectTenjin() {
  if (connecting) return;
  connecting = true;
  try {
    if (!initialized) {
      Tenjin.initialize(TENJIN_SDK_KEY);
      if (Platform.OS === 'android') {
        Tenjin.setAppStore('googleplay'); // googleplay, amazon, other
      }
      initialized = true;
    }

    if (Platform.OS === 'ios') {
      // Shows the ATT prompt the first time; resolves at once afterwards.
      await request(PERMISSIONS.IOS.APP_TRACKING_TRANSPARENCY);
    }

    Tenjin.connect();
  } finally {
    connecting = false;
  }
}

export function useTenjin() {
  useEffect(() => {
    if (AppState.currentState === 'active') {
      connectTenjin();
    }
    const subscription = AppState.addEventListener('change', (state) => {
      if (state === 'active') {
        connectTenjin();
      }
    });
    return () => subscription.remove();
  }, []);
}
```

### Expo

Identical, except for the ATT request:

```javascript
import { requestTrackingPermissionsAsync } from 'expo-tracking-transparency';

// inside connectTenjin(), instead of the react-native-permissions call:
if (Platform.OS === 'ios') {
  await requestTrackingPermissionsAsync();
}
```

### Using in Your App

Call the hook once, in the root component:

```javascript
import React from 'react';

const App = () => {
  useTenjin();

  return (
    // Your UI
    null
  );
};

export default App;
```

---

## 5. Verify from the Device Log

Do this before adding any optional feature, **once per platform**: the two platforms use different keys and different Tenjin apps, so one passing does not prove the other.

The JavaScript API has no debug-log call. The log lines come from the native SDKs, not from the Metro console.

### Android

Run on a device or emulator with Google Play services. The native SDK logs every request under the Logcat tag **`HttpConnection`** (not `TenjinSDK`), and labels every request `Tenjin::connect` regardless of its type:

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

The native iOS SDK prints requests and responses only after its `debugLogs()` method has been called. In a development build, call it natively at the start of `application(_:didFinishLaunchingWithOptions:)` in the app's `AppDelegate`:

```swift
import TenjinSDK

#if DEBUG
TenjinSDK.debugLogs()
#endif
```

In an Objective-C `AppDelegate`, use `#import "TenjinSDK.h"` and `[TenjinSDK debugLogs];`. If the import does not resolve in the app target, or the project is an Expo project whose `ios/` folder is generated, skip this and verify iOS with the dashboard tool below instead. With debug logs on, the Xcode console shows:

```text
[Tenjin] - LOG: Connect request
[Tenjin] - LOG: Got http response 200
[Tenjin] - DEBUG: Response body {"code":200,"success":true}
```

On iOS the line that decides is `Got http response <status>`. The iOS SDK prints no error for a rejected request, so read the status code.

### What the Response Means

| Response contains | HTTP status | Meaning | What to do |
|-------------------|-------------|---------|------------|
| `"success":true` | 200 | Accepted | Nothing. The integration works on this platform |
| `unauthorized` | 401 | The SDK key is unknown, or it is not the key of this app | Check the runtime key selection: the iOS key on iOS, the Android key on Android, each from that app's page in the dashboard |
| `no such app` | 404 | There is no Tenjin app for this bundle ID on this platform | Create the app in the dashboard with exactly this ID, or fix the ID (check debug suffixes and flavors) |
| `invalid device identifier` | 202 | The request carried no advertising ID | Android: add the `AD_ID` permission and `play-services-ads-identifier`; test on a device with Google Play services |
| `not logged` | 202 | The SDK key is disabled | Enable the key in the dashboard or use another key of the same app |
| `ignored` | 202 | The request was filtered by an app-version rule configured for the app | Check the app's version rules in the dashboard |

A 202 is **not** success: the request was received and dropped.

### No Request at All

A `connect()` within 30 seconds of the previous one is skipped by the native SDK and sends nothing. The timestamp is stored on the device, so it survives an app restart and a JavaScript reload.

- Android logs `Connect deduped by persisted timestamp` under the tag `TenjinSDK`. Wait 30 seconds or clear the app's data (`adb shell pm clear <applicationId>`).
- iOS logs `Connect sent ...s ago (interval: 30.0s), ignoring duplicate ping` with debug logs on. Wait 30 seconds or reinstall the app.
- An error that says the package "doesn't seem to be linked" means the native module is missing: run `pod install`, rebuild the app, and do not use Expo Go.

### In the Dashboard

After a 200 response, the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics) shows events for devices registered as test devices.

---

## 6. Purchase Event Tracking

### Manual Revenue (No Validation)

```javascript
Tenjin.transaction(
  'product_identifier', // productName
  'USD',                // currencyCode
  1,                    // quantity
  9.99                  // unitPrice (Number)
);
```

### Validated Purchases

The method differs per platform:

```javascript
import { Platform } from 'react-native';

if (Platform.OS === 'ios') {
  Tenjin.transactionWithReceipt(
    productName,    // string
    currencyCode,   // string
    quantity,       // number
    unitPrice,      // number
    transactionId,  // string
    receipt         // string, base64
  );
} else {
  Tenjin.transactionWithDataSignature(
    productName,    // string
    currencyCode,   // string
    quantity,       // number
    unitPrice,      // number
    purchaseData,   // string, the purchase's original JSON
    dataSignature   // string
  );
}
```

For validation, add the App-Specific Shared Secret (iOS app) and the Base64-encoded RSA public key (Android app) in the Tenjin dashboard.

### Subscription Tracking

Subscriptions are **not** captured by `connect()`. One of the methods below must be called from the purchase-handling code. Android support requires `react-native-tenjin` **1.4.0 or newer**. Pass the iOS parameters on iOS and the Android parameters on Android.

```javascript
Tenjin.subscription({
  productId: 'com.example.monthly',  // Required
  currencyCode: 'USD',               // Required
  unitPrice: 9.99,                   // Required
  // iOS parameters
  iosTransactionId: '...',
  iosOriginalTransactionId: '...',
  iosReceipt: '...',                 // JWS signed transaction
  iosSKTransaction: '...',           // StoreKit 2 transaction JSON
  // Android parameters
  androidPurchaseToken: '...',       // Google Play purchase token
  androidPurchaseData: '...',        // original JSON from the purchase object
  androidDataSignature: '...',       // signature for purchase verification
});

// iOS only (iOS 15+): let the SDK fetch the StoreKit 2 transaction itself.
// Recommended for IAP libraries that don't expose StoreKit 2 data (e.g. RevenueCat).
// On Android it calls the error callback.
Tenjin.subscriptionWithStoreKit(
  'com.example.monthly', 'USD', 9.99,
  () => {},                       // success
  (error) => console.error(error) // error
);
```

With `react-native-iap`, read the Android fields from the purchase object (`purchaseTokenAndroid`, `dataAndroid`, `signatureAndroid`). See the SDK's [SUBSCRIPTIONS_TRACKING.md](https://github.com/tenjin/tenjin-react-native-sdk/blob/master/SUBSCRIPTIONS_TRACKING.md) for full `react-native-iap` examples.

**Notes:**
- **iOS:** add the app's **App-Specific Shared Secret** in the Tenjin dashboard. Send one transaction per billing interval (first charge and each renewal), and none during a free trial.
- **Android:** subscriptions are verified through the **Google Play Developer API**, so the Android app needs Google Play Developer API access configured in the Tenjin dashboard (a different credential from the RSA public key used for one-time purchases). Send **once per subscription**, not once per renewal: Tenjin resolves renewals, trials and cancellations from the purchase token.

---

## 7. Custom Events

> **Prerequisite:** `connect()` must have been called before sending any custom events.

```javascript
// Event without value
Tenjin.eventWithName('level_complete');

// Event with an integer value. Pass a number; passing a string is deprecated.
Tenjin.eventWithNameAndValue('coins_spent', 50);
```

**Limits:**
- Event names must be under **80 characters**
- Maximum **500 unique** event names per app

---

## 8. SKAdNetwork Conversion Values (iOS Only)

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

## 9. GDPR & Privacy Compliance

Call these after `initialize()` and before `connect()`.

### Full Opt-In / Opt-Out

```javascript
if (userConsented) {
  Tenjin.optIn();
} else {
  Tenjin.optOut(); // No API requests will be sent
}
```

### Granular Parameter Control

The methods that take a parameter list are `optInParams` and `optOutParams`. `optIn()` and `optOut()` take no arguments.

```javascript
// Only send these specific parameters
Tenjin.optInParams([
  'ip_address',
  'advertising_id',
  'developer_device_id',
  'limit_ad_tracking',
  'referrer',
  'iad',
]);

// Or send everything EXCEPT these parameters
Tenjin.optOutParams([
  'locale',
  'timezone',
  'build_id',
]);
```

### CMP-Based Consent

Automatically opt in/out based on CMP consent (TCF purpose 1):

```javascript
Tenjin.optInOutUsingCMP();
```

### Google DMA Parameters

```javascript
// Manual control
Tenjin.setGoogleDMAParameters(true, true); // (adPersonalization, adUserData)

// Toggle collection
Tenjin.optInGoogleDMA();  // default
Tenjin.optOutGoogleDMA();
```

---

## 10. Attribution Info & Deep Links

### Attribution Info (LiveOps Campaigns)

> **Note:** `getAttributionInfo()` is a paid feature. Contact your Tenjin account manager for access.

```javascript
Tenjin.getAttributionInfo(
  (info) => {
    const adNetwork = info.ad_network;
    const campaignId = info.campaign_id;
    const campaignName = info.campaign_name;
  },
  (error) => {
    console.error('Attribution info failed', error);
  }
);
```

Values are returned only when available. Other keys: `advertising_id`, `tenjin_parameter_0` … `tenjin_parameter_5`.

### Re-engagement Deep Links

Requires `react-native-tenjin` **1.6.0 or newer**. Report the URL the app was opened with, so re-engagement clicks can be attributed. Forward both the launch link and links received while the app is running:

```javascript
import { Linking } from 'react-native';

Linking.getInitialURL().then((url) => url && Tenjin.handleOpenUrl(url));
Linking.addEventListener('url', ({ url }) => Tenjin.handleOpenUrl(url));
```

On Android, opens that start or recreate the Activity are captured automatically, so this is only needed for links delivered to an Activity that is already running.

---

## 11. Impression Level Ad Revenue (ILRD)

> **Note:** ILRD is a paid feature. Contact your Tenjin account manager before implementing.

Pass the impression data from the ad network's callback as a plain object.

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

// TradPlus
Tenjin.eventAdImpressionTradPlus(impressionDataJson);

// CloudX
Tenjin.eventAdImpressionCloudX(impressionDataJson);
```

### AdMob value units

> **Important:** despite its name, `value_micros` is **not** in micros on iOS. The iOS SDK reads it as
> currency units (e.g. `0.012245` USD); the Android SDK reads it as micros (e.g. `12245`).
> AdMob reports micros on both platforms, so divide by 1,000,000 on iOS only.
> Sending raw micros on iOS inflates ad revenue 1,000,000x; dividing on Android reports 1,000,000x too little.

```javascript
import { Platform } from 'react-native';

// valueMicros: the paid-event value in micros, as your AdMob library reports it.
// Check your library's docs: some expose it already converted to currency units.
const sendAdMobImpression = ({ adUnitId, valueMicros, currencyCode, precisionType }) => {
  Tenjin.eventAdImpressionAdMob({
    ad_unit_id: adUnitId,
    value_micros: Platform.OS === 'ios' ? valueMicros / 1000000 : valueMicros,
    currency_code: currencyCode,
    precision_type: precisionType,
  });
};
```

---

## 12. User Identity & Analytics

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

### Analytics Installation ID

A locally generated persistent identifier (useful when IDFA/AAID is unavailable):

```javascript
Tenjin.getAnalyticsInstallationId((id) => {
  console.log('Tenjin analytics installation ID:', id);
});
```

### User Profile Data

```javascript
Tenjin.getUserProfileDictionary((profile) => {
  console.log('Session count:', profile.session_count);
  console.log('Total session time (ms):', profile.total_session_time);
  console.log('IAP transaction count:', profile.iap_transaction_count);
  console.log('Total ad revenue (USD):', profile.total_ilrd_revenue_usd);
});

// Reset all profile data
Tenjin.resetUserProfile();
```

---

## 13. Additional Configuration

### A/B Testing with App Subversion

Call before `connect()`:

```javascript
Tenjin.appendAppSubversion(8888); // Reports as e.g. "1.0.1.8888"
```

### Event Caching (Offline Support)

```javascript
Tenjin.setCacheEventSetting(true);
```

The setting is stored on the device. Removing the call in a later release does not turn caching off; call `setCacheEventSetting(false)` to disable it.

---

## 14. Google Ads On-Device Conversion Measurement (ICM / ODM, iOS Only)

> **Only for apps that run Google Ads campaigns for this iOS app.** Before adding anything, ask the developer:
>
> "Do you run Google Ads (App campaigns) for your iOS app?"
>
> Ad spend cannot be seen in the project, so do not guess. If the answer is no, or they are not sure, skip this section: do not add Google's SDK and do not add the connect delay.

Google calls this Integrated Conversion Measurement (ICM). It relies on Google's on-device conversion measurement (ODM) SDK, `GoogleAdsOnDeviceConversion`, and is iOS only.

The Tenjin iOS SDK (1.14.8 or newer) uses it by itself once Google's SDK is in the app: when the Tenjin SDK is initialized it asks Google's SDK for the install's conversion data, stores it, and sends it with its requests. There is no Tenjin method to call. `react-native-tenjin` uses the native iOS SDK, so this works without any JavaScript call. Two things are needed:

1. Google's SDK in the iOS app.
2. A short delay before the first `connect()`, so Google's SDK has time to produce the data.

### Add Google's SDK

**Check first whether it is already there.** Firebase Analytics depends on Google's SDK, so apps that use `@react-native-firebase/analytics` already have it. Look for `GoogleAdsOnDeviceConversion` in `ios/Podfile.lock`. If it is listed, do not add it again (a second, different version can break `pod install`); go straight to the delay below. If you add it to a project that also has Firebase Analytics, use the version Google pairs with that Firebase version: see the [version mapping table](https://github.com/googleads/google-ads-on-device-conversion-ios-sdk#version-mapping-with-ga4f-sdk).

Resolve the version of Google's SDK the same way as Tenjin's, and use it wherever a snippet says `<GOOGLE_ODM_VERSION>`:

```bash
curl -s https://trunk.cocoapods.org/api/v1/pods/GoogleAdsOnDeviceConversion | grep -o '"name":"[0-9.]*"' | cut -d'"' -f4 | sort -V | tail -1
```

**Bare React Native:** in `ios/Podfile`, inside the app's `target '<YourApp>' do` block, add the pod, then run `cd ios && pod install`:

```ruby
pod 'GoogleAdsOnDeviceConversion', '~> <GOOGLE_ODM_VERSION>'
```

**Expo:** the Podfile is generated, so add the pod through the `expo-build-properties` plugin in `app.json` (merge it into the existing entry if the project already has one), then run `npx expo prebuild` again:

```json
{
  "expo": {
    "plugins": [
      [
        "expo-build-properties",
        {
          "ios": {
            "extraPods": [
              { "name": "GoogleAdsOnDeviceConversion", "version": "~> <GOOGLE_ODM_VERSION>" }
            ]
          }
        }
      ]
    ]
  }
}
```

### Delay the First connect()

Google's SDK starts working when the Tenjin SDK is initialized and usually needs under a second. Make the **first** `connect()` of each app run happen at least 3 seconds after initialization; later connects (returns to the foreground) need no delay. Waiting for the tracking prompt often provides this already, but not when the user answered it on an earlier launch or tracking is disabled on the device, so add the delay explicitly. Do it on iOS only.

In the `connectTenjin()` function from Section 4, record when the SDK was initialized and wait before the first connect:

```javascript
let initializedAt = 0;
let connectedOnce = false;

// The first connect() of each app run on iOS waits until 3 seconds after
// initialize(), so Google's on-device conversion SDK can produce its data.
async function waitForGoogleOnDeviceConversion() {
  if (Platform.OS !== 'ios' || connectedOnce) return;
  connectedOnce = true;
  const remaining = 3000 - (Date.now() - initializedAt);
  if (remaining > 0) {
    await new Promise((resolve) => setTimeout(resolve, remaining));
  }
}
```

Set `initializedAt = Date.now();` right after `Tenjin.initialize(TENJIN_SDK_KEY);`, and call the helper just before connecting:

```javascript
await waitForGoogleOnDeviceConversion();
Tenjin.connect();
```

**Verify.** Confirm `GoogleAdsOnDeviceConversion` appears in `ios/Podfile.lock` after installing. When Google's SDK returns data, the first `connect()` of a fresh install carries it as `omd_info`: with iOS debug logs on (Section 5), the `request body` line contains `omd_info=`. The data is fetched once per install, so reinstall the app to test again.

---

## 15. Integration Checklist

When integrating Tenjin into a React Native project, verify these items:

- [ ] **SDK version** was resolved by `npm install react-native-tenjin@latest` (or `npx expo install`), not written by hand
- [ ] **Expo projects** use a development build, not Expo Go, and configure native settings through `app.json`
- [ ] **Two SDK keys**, selected with `Platform.OS`, each belonging to the Tenjin app with that platform's bundle ID; placeholders are replaced
- [ ] **iOS Info.plist** has `NSUserTrackingUsageDescription` with a user-facing message
- [ ] **iOS Info.plist** has `NSAdvertisingAttributionReportEndpoint` set to `https://tenjin-skan.com`
- [ ] **Pod install** was run successfully in the `ios` directory (bare projects)
- [ ] **Android** declares `play-services-ads-identifier` and `play-services-appset`
- [ ] **Android Manifest** has `INTERNET`, `ACCESS_NETWORK_STATE` and `AD_ID` permissions
- [ ] **The ATT prompt** is requested once, when the app is active, before `connect()` on iOS
- [ ] **`connect()`** is called on every launch and every return to the foreground
- [ ] **Custom events** are only sent after `connect()` has been called
- [ ] **ProGuard rules** are added if the Android release build is minified
- [ ] **Both platforms** show a 200 / `"success":true` response in the device log
- [ ] **Google ICM / ODM** (only if the app runs Google Ads campaigns on iOS): `GoogleAdsOnDeviceConversion` is in the app once, and the first `connect()` of each run comes at least 3 seconds after initialization
- [ ] Integration is verified using the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics)

---

## 16. Common Mistakes to Avoid

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Writing a version into `package.json` from memory | It is usually many releases old and lacks the APIs in this guide | `npm install react-native-tenjin@latest` |
| One SDK key for both platforms | Each platform is a separate Tenjin app; the wrong key gets `unauthorized` | Select the key with `Platform.OS` |
| Verifying on one platform only | The other platform uses a different key and app | Check the device log on iOS and on Android |
| Calling `Tenjin.optIn([...])` or `Tenjin.optOut([...])` with a list | Those methods take no arguments; the list is not applied | Use `optInParams([...])` / `optOutParams([...])` |
| Running in Expo Go | The native module is not there; every call throws a linking error | Use a development build |
| Editing `android/` or `ios/` in an Expo prebuild project | The folders are regenerated | Use `app.json` and a config plugin |
| Missing `play-services-ads-identifier` on Android | No advertising ID: requests are rejected with `invalid device identifier` | Add it and `play-services-appset` |
| Missing `AD_ID` permission on Android | Cannot access the advertising ID on Android 13+ | Add the permission |
| Missing `NSAdvertisingAttributionReportEndpoint` | SKAdNetwork postbacks do not reach Tenjin | Add the key with `https://tenjin-skan.com` |
| Adding a second ATT prompt | The app already asks elsewhere | Call `connect()` after the existing request |
| Calling `connect()` only on first launch | Tenjin needs session data on every launch; accounts may be suspended | Call `connect()` on every launch and foreground |
| Passing a string to `eventWithNameAndValue` | Deprecated; logs a warning | Pass a number |
| Sending events before `connect()` | Events will not be processed | Always call `connect()` first |
| Event names over 80 characters | Will be rejected | Keep event names concise |
| Exceeding 500 unique event names | Additional events will be dropped | Reuse event names with different values |
| Sending AdMob `value_micros` without platform branching | iOS reads it as currency units, Android as micros; revenue is off by 1,000,000x | Divide the micros value by 1,000,000 on iOS only |
| Relaunching within 30 seconds while testing | The native SDK skips the second `connect()` and sends nothing | Wait 30 seconds, or clear app data / reinstall |
| Adding Google's on-device conversion SDK to an app that does not run Google Ads | An unneeded dependency and a delayed first connect for nothing | Ask the developer first; skip the section if they do not run Google Ads on iOS |
| Adding `GoogleAdsOnDeviceConversion` when Firebase Analytics already brings it | Two version requirements for one pod; `pod install` can fail | Check the lockfile first; if adding it next to Firebase, use Google's version mapping |
| First `connect()` right after initialization in an app with Google's ODM SDK | Google's data is not ready yet, so the first open is sent without it | Make the first `connect()` of each run at least 3 seconds after initialization (iOS only) |

---

## 17. Full API Reference

All methods are on the default export `Tenjin`.

### Core

| Method | Purpose |
|--------|---------|
| `initialize(apiKey)` | Initialize SDK with the SDK key |
| `connect()` | Send install/session data |
| `setAppStore(type)` | Set Android store (googleplay, amazon, other) |
| `appendAppSubversion(subversion)` | A/B test variant tracking |

### Events & Revenue

| Method | Purpose |
|--------|---------|
| `eventWithName(name)` | Custom event (name only) |
| `eventWithNameAndValue(name, value)` | Custom event with integer value |
| `transaction(productName, currencyCode, quantity, unitPrice)` | Revenue without validation |
| `transactionWithReceipt(productName, currencyCode, quantity, unitPrice, transactionId, receipt)` | Validated purchase (iOS) |
| `transactionWithDataSignature(productName, currencyCode, quantity, unitPrice, purchaseData, dataSignature)` | Validated purchase (Android) |
| `subscription(params)` | Subscription tracking (iOS + Android) |
| `subscriptionWithStoreKit(productId, currencyCode, unitPrice, successCallback, errorCallback)` | iOS-only native StoreKit 2 subscription fetch |

### SKAdNetwork (iOS)

| Method | Purpose |
|--------|---------|
| `updatePostbackConversionValue(conversionValue, coarseValue, lockWindow)` | Update SKAN conversion value; the last two arguments are optional |

### Privacy & Consent

| Method | Purpose |
|--------|---------|
| `optIn()` / `optOut()` | GDPR full opt-in/out |
| `optInParams(params)` / `optOutParams(params)` | Granular parameter control |
| `optInOutUsingCMP()` | Automatic CMP-based consent |
| `optInGoogleDMA()` / `optOutGoogleDMA()` | Google DMA parameter control |
| `setGoogleDMAParameters(adPersonalization, adUserData)` | Set Google DMA consent flags |

### Ad Revenue (ILRD)

| Method | Purpose |
|--------|---------|
| `eventAdImpressionAppLovin(json)` | AppLovin impression |
| `eventAdImpressionAdMob(json)` | AdMob impression |
| `eventAdImpressionIronSource(json)` | Unity LevelPlay impression |
| `eventAdImpressionHyperBid(json)` | HyperBid impression |
| `eventAdImpressionTopOn(json)` | TopOn impression |
| `eventAdImpressionTradPlus(json)` | TradPlus impression |
| `eventAdImpressionCloudX(json)` | CloudX impression |

### Identity & Analytics

| Method | Purpose |
|--------|---------|
| `setCustomerUserId(userId)` | Set custom user identifier |
| `getCustomerUserId(callback)` | Retrieve stored user ID |
| `getAnalyticsInstallationId(callback)` | Get persistent local analytics ID |
| `getAttributionInfo(successCallback, errorCallback)` | Get attribution data (paid feature) |
| `handleOpenUrl(url)` | Report an app-open deep link |
| `getUserProfileDictionary(callback)` | Get user metrics as an object |
| `resetUserProfile()` | Clear all local profile data |

### Configuration

| Method | Purpose |
|--------|---------|
| `setCacheEventSetting(setting)` | Enable offline event caching |
| `setEncryptRequestsSetting(setting)` | Enable request encryption |

---

## 18. How to Use This Document

**With any LLM:**

```
Add Tenjin to my React Native app using this guide:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/react-native/llm-guide.md
```

**Keeping this document up to date:**

This guide is derived from the official [README.md](https://github.com/tenjin/tenjin-react-native-sdk/blob/master/README.md) and the TypeScript interface in [src/index.tsx](https://github.com/tenjin/tenjin-react-native-sdk/blob/master/src/index.tsx). When the SDK is updated, review those sources and update this file accordingly.
