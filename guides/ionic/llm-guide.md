# Tenjin Ionic SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin Ionic SDK (Capacitor plugin) into an Ionic or plain Capacitor project without requiring external documentation lookups, except for the version lookup below.
>
> **Requirements:** Capacitor >= 6.0.0 | iOS 14.0+ | Android API 22+
>
> **Sources:**
> - Repository: [github.com/tenjin/tenjin-ionic-sdk](https://github.com/tenjin/tenjin-ionic-sdk)
> - Full README: [README.md](https://github.com/tenjin/tenjin-ionic-sdk/blob/master/README.md)
> - TypeScript definitions: [definitions.ts](https://github.com/tenjin/tenjin-ionic-sdk/blob/master/src/definitions.ts)
> - npm: [ionic-capacitor-tenjin](https://www.npmjs.com/package/ionic-capacitor-tenjin)

---

## Before You Begin

### Resolve the SDK Version

This document contains no SDK version number on purpose. **Do not use a version you remember**: versions recalled from training data are usually many releases old, and do not write a version into `package.json` by hand.

The install command in Section 1 resolves the current version from npm. To see it:

```bash
npm view ionic-capacitor-tenjin version
```

If you cannot run commands, fetch `https://registry.npmjs.org/ionic-capacitor-tenjin/latest` and read `version`. If you can do neither, stop and ask the developer for the current version. Never guess.

The Google libraries Tenjin needs on Android are resolved from Google's Maven repository. Use the output wherever a snippet says `<ADS_IDENTIFIER_VERSION>` or `<APPSET_VERSION>`:

```bash
for a in com/google/android/gms/play-services-ads-identifier com/google/android/gms/play-services-appset; do
  printf '%s ' "$a"
  curl -s "https://dl.google.com/dl/android/maven2/$a/maven-metadata.xml" | sed -n 's:.*<release>\(.*\)</release>.*:\1:p'
done
```

If the project already declares one of these libraries (ad SDKs usually bring `play-services-ads-identifier`), keep the version the project has.

### One App and One SDK Key per Platform

A Tenjin app is **one bundle ID / application ID on one platform**. A Capacitor project that ships on iOS and Android is therefore **two Tenjin apps with two SDK keys**, and the code must pick the right one at runtime:

- Tenjin's servers look the app up by the platform and the bundle ID the request carries, then check that the SDK key belongs to that app. The iOS key is refused on Android and the Android key is refused on iOS.
- Anything that changes the bundle ID changes the Tenjin app: an Android `applicationIdSuffix ".debug"`, a product flavor, or an iOS configuration with its own `PRODUCT_BUNDLE_IDENTIFIER`. Either register that ID as its own app in the Tenjin dashboard and use its key in those builds, or expect those builds to be rejected (see [Verify from the Device Log](#5-verify-from-the-device-log)).

Before writing code, find the IDs the project produces and tell the developer. `appId` in `capacitor.config.ts` is only the value the native projects were created with; the IDs that count are `applicationId` in `android/app/build.gradle` and `PRODUCT_BUNDLE_IDENTIFIER` in `ios/App/App.xcodeproj/project.pbxproj`.

### Get the SDK Keys

**Ask the developer for one Tenjin SDK key per platform the project builds for.** Code examples use `<IOS_SDK_KEY>` and `<ANDROID_SDK_KEY>` as placeholders (`<SDK_KEY>` where the platform does not matter). Before writing any integration code, prompt the user:

> "Tenjin needs one SDK key per platform. What is the SDK key of your iOS app (bundle ID `<the iOS bundle ID you found>`) and of your Android app (application ID `<the Android ID you found>`)? You can find each in the [Tenjin dashboard](https://www.tenjin.com/dashboard/organizations) on that app's page. If you don't have them handy, I can use placeholders and you can fill them in later — just search your project for `TENJIN_SDK_KEY_PLACEHOLDER` to find them."

If the developer provides the keys, substitute them directly in all generated code. If they prefer to add them later, use the literal strings `TENJIN_SDK_KEY_PLACEHOLDER_IOS` and `TENJIN_SDK_KEY_PLACEHOLDER_ANDROID` so they are easy to find with a project-wide search. If the project builds for one platform only, ask for that key only. Never copy a key from a sample project or from another app.

## Integration Workflow

Follow this two-step approach:

1. **First, integrate the basics.** Complete sections 1–5 (Installation, iOS Setup, Android Setup, Core Initialization, Verify from the Device Log). This gives the developer install tracking, session tracking and ATT support — the foundation every Tenjin integration needs.

2. **Then, ask what else they need.** After the basic integration is working, prompt the user:

> "Tenjin basic integration is done (install tracking + ATT). Would you like to add any of these features?"
> - **Purchase tracking** — track in-app purchase revenue (Section 6)
> - **Custom events** — track in-app actions like level completions or signups (Section 7)
> - **SKAdNetwork conversion values** — for SKAN attribution on iOS (Section 8)
> - **GDPR / consent management** — opt-in/out, CMP, Google DMA (Section 9)
> - **Ad revenue (ILRD)** — impression-level revenue from ad networks (Section 10, paid feature)
> - **User identity, attribution & deep links** — customer user IDs, analytics IDs, user profiles, re-engagement deep links (Section 11)
> - **Google Ads conversion measurement (ICM / ODM)** — iOS only, for apps that run Google Ads campaigns (Section 13)

Only implement the sections the developer requests. Do not add features they didn't ask for.

---

## Quick Context

Tenjin is a mobile attribution and analytics platform. The SDK tracks app installs, sessions, in-app purchases, ad revenue, and custom events. This Ionic SDK is a **Capacitor plugin** that bridges to the native Tenjin SDKs on iOS and Android.

- It is a Capacitor plugin, not a Cordova plugin. It requires Capacitor 6.0.0 or higher. Cordova projects are not supported.
- It has no web implementation: calls made in a browser reject. Guard them with `Capacitor.getPlatform()`.
- Every method takes a single options object and returns a `Promise`.
- It has **no** App Tracking Transparency call of its own.

---

## 1. Installation

Install the package and sync with Capacitor:

```bash
npm install ionic-capacitor-tenjin@latest
npx cap sync
```

The import is a **named** export:

```typescript
import { Tenjin } from 'ionic-capacitor-tenjin';
```

---

## 2. iOS Platform Setup

### Info.plist Configuration

Add these keys to `ios/App/App/Info.plist`:

```xml
<!-- Required for the ATT prompt (iOS 14+). The app crashes on the ATT request if this is missing. -->
<key>NSUserTrackingUsageDescription</key>
<string>We use this data to provide a better and personalized ad experience.</string>

<!-- Required for SKAdNetwork postbacks (iOS 15+) -->
<key>NSAdvertisingAttributionReportEndpoint</key>
<string>https://tenjin-skan.com</string>
```

### Minimum iOS Version

The plugin requires iOS 14.0 or higher. If the project uses CocoaPods, make sure `ios/App/Podfile` does not set a lower platform:

```ruby
platform :ios, '14.0'
```

Then run:

```bash
npx cap sync ios
```

---

## 3. Android Platform Setup

The plugin depends on the Tenjin Android SDK but **not** on the Google libraries that SDK reads the device identifiers from. The app must add them. If they are missing the build still succeeds, but requests go out without an advertising ID and are rejected with `invalid device identifier`.

### Gradle Dependencies

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

### Minimum SDK Version

The plugin requires Android API 22+. Ensure `android/variables.gradle` has:

```gradle
ext {
    minSdkVersion = 22
    // ...
}
```

Leave the value alone if it is already 22 or higher.

### AndroidManifest.xml

In `android/app/src/main/AndroidManifest.xml`:

```xml
<manifest>
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

    <!-- Required to read the Advertising ID on Android 13+ (API 33) -->
    <uses-permission android:name="com.google.android.gms.permission.AD_ID" />

    <application>
        <!-- Possible values: googleplay, amazon, other -->
        <meta-data android:name="TENJIN_APP_STORE" android:value="googleplay" />
    </application>
</manifest>
```

The plugin has no call to set the app store, so the `TENJIN_APP_STORE` meta-data is the only way to set it. Without it the store is reported as `unspecified`.

### ProGuard / R8 Rules

If the release build is minified, add these to `android/app/proguard-rules.pro`:

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

Run `npx cap sync android` after changing native files.

---

## 4. Core Initialization

### Where connect() Goes

- **On every launch and every return to the foreground**, not only on first open. Tenjin needs the session data, and accounts that only connect on first open may be suspended.
- **On iOS, after the user has answered the tracking prompt.** Calling `connect()` before the ATT answer sends a zeroed IDFA and degrades attribution.
- **Request ATT only when the app is active.** iOS shows the prompt only while the app is in the foreground and active.
- **If the app already has a tracking prompt, hook into it. Do not add a second one.** Search the project for `AppTrackingTransparency`, `requestPermission` and `requestTrackingAuthorization`. If the app already asks, call `Tenjin.connect()` after that existing request resolves and leave out the request below.

Calling `connect()` on every return to the foreground is safe: the native SDKs skip a `connect()` that comes within 30 seconds of the previous one.

### Recommended Implementation

`ionic-capacitor-tenjin` has no ATT call. This example uses the community plugin `capacitor-plugin-app-tracking-transparency` (`npm install capacitor-plugin-app-tracking-transparency && npx cap sync`) and `@capacitor/app` for the foreground event. Any other ATT plugin works the same way: await its request, then call `Tenjin.connect()`.

Create `src/app/services/tenjin.ts` (or the equivalent in a React or Vue project; nothing here depends on Angular):

```typescript
import { App } from '@capacitor/app';
import { Capacitor } from '@capacitor/core';
import { AppTrackingTransparency } from 'capacitor-plugin-app-tracking-transparency';
import { Tenjin } from 'ionic-capacitor-tenjin';

let initialized = false;
let connecting = false;

async function connectTenjin(): Promise<void> {
  const platform = Capacitor.getPlatform();
  if (platform !== 'ios' && platform !== 'android') {
    return; // The plugin has no web implementation
  }
  if (connecting) {
    return;
  }
  connecting = true;
  try {
    if (!initialized) {
      // One key per platform: an iOS app and an Android app are two Tenjin apps.
      const sdkKey = platform === 'android' ? '<ANDROID_SDK_KEY>' : '<IOS_SDK_KEY>';
      await Tenjin.initialize({ sdkKey });
      initialized = true;
    }

    if (platform === 'ios') {
      // Shows the ATT prompt the first time; resolves at once afterwards.
      await AppTrackingTransparency.requestPermission();
    }

    await Tenjin.connect();
  } finally {
    connecting = false;
  }
}

/** Call once when the app starts. */
export async function startTenjin(): Promise<void> {
  await connectTenjin();
  await App.addListener('appStateChange', ({ isActive }) => {
    if (isActive) {
      void connectTenjin();
    }
  });
}
```

### Using in Your App

Call `startTenjin()` once, early in the app lifecycle. In an Angular app:

```typescript
import { Component } from '@angular/core';
import { Platform } from '@ionic/angular';
import { startTenjin } from './services/tenjin';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html'
})
export class AppComponent {

  constructor(private platform: Platform) {
    this.platform.ready().then(() => startTenjin());
  }
}
```

In React or Vue, call `startTenjin()` from the root component's mount hook.

---

## 5. Verify from the Device Log

Do this before adding any optional feature, **once per platform**: the two platforms use different keys and different Tenjin apps, so one passing does not prove the other.

The plugin has no debug-log call. The log lines come from the native SDKs, not from the web view console.

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

The native iOS SDK prints requests and responses only after its `debugLogs()` method has been called. In a development build, call it natively at the start of `application(_:didFinishLaunchingWithOptions:)` in `ios/App/App/AppDelegate.swift`:

```swift
import TenjinSDK

#if DEBUG
TenjinSDK.debugLogs()
#endif
```

If `import TenjinSDK` does not resolve in the App target, skip this and verify iOS with the dashboard tool below instead. With debug logs on, the Xcode console shows:

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

A `connect()` within 30 seconds of the previous one is skipped by the native SDK and sends nothing. The timestamp is stored on the device, so it survives an app restart and a live reload.

- Android logs `Connect deduped by persisted timestamp` under the tag `TenjinSDK`. Wait 30 seconds or clear the app's data (`adb shell pm clear <applicationId>`).
- iOS logs `Connect sent ...s ago (interval: 30.0s), ignoring duplicate ping` with debug logs on. Wait 30 seconds or reinstall the app.
- A rejected promise saying the plugin is not implemented means the code ran in a browser, or `npx cap sync` was not run after installing.

### In the Dashboard

After a 200 response, the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics) shows events for devices registered as test devices.

---

## 6. Purchase Event Tracking

The plugin reports purchase revenue without receipt validation:

```typescript
await Tenjin.transaction({
  productName: 'premium_upgrade',
  currencyCode: 'USD',
  quantity: 1,
  unitPrice: 9.99
});
```

**Notes:**
- The plugin has no receipt-validation method and no subscription method.
- If you report subscription revenue this way, send one transaction per billing interval (first charge and each renewal) and none during a free trial. Tenjin does not de-duplicate transactions.

---

## 7. Custom Events

> **Prerequisite:** `connect()` must have been called before sending any custom events.

```typescript
// Event without value
await Tenjin.eventWithName({ name: 'level_complete' });

// Event with value (an integer, passed as a string)
await Tenjin.eventWithNameAndValue({ name: 'coins_spent', value: '50' });
```

**Limits:**
- Event names must be under **80 characters**
- Maximum **500 unique** event names per app

---

## 8. SKAdNetwork Conversion Values (iOS Only)

These methods only work on iOS. On Android, they log a message and resolve without action.

```typescript
import { Capacitor } from '@capacitor/core';

// Basic conversion value (0-63)
if (Capacitor.getPlatform() === 'ios') {
  await Tenjin.updatePostbackConversionValue({ conversionValue: 5 });
}

// With coarse value (iOS 16.1+ / SKAN 4.0)
if (Capacitor.getPlatform() === 'ios') {
  await Tenjin.updatePostbackConversionValueCoarseValue({
    conversionValue: 5,
    coarseValue: 'medium'
  });
}

// With coarse value and lock window
if (Capacitor.getPlatform() === 'ios') {
  await Tenjin.updatePostbackConversionValueCoarseValueLockWindow({
    conversionValue: 5,
    coarseValue: 'high',
    lockWindow: true
  });
}
```

Valid coarse values: `"low"`, `"medium"`, `"high"`

---

## 9. GDPR & Privacy Compliance

### Full Opt-In / Opt-Out

```typescript
await Tenjin.initialize({ sdkKey: '<SDK_KEY>' });

if (userConsented) {
  await Tenjin.optIn();
} else {
  await Tenjin.optOut();  // No API requests will be sent
}

await Tenjin.connect();
```

### Granular Parameter Control

```typescript
// Only send these specific parameters
await Tenjin.optInParams({
  params: ['ip_address', 'advertising_id', 'developer_device_id', 'limit_ad_tracking']
});

// Or send everything EXCEPT these parameters
await Tenjin.optOutParams({
  params: ['locale', 'timezone', 'build_id']
});
```

> **Required parameters:** `developer_device_id` (iOS) and `advertising_id` (Android) must always be included. Events missing them will not be processed.

### CMP-Based Consent

Automatically opt in/out based on CMP consent (TCF purpose 1):

```typescript
await Tenjin.initialize({ sdkKey: '<SDK_KEY>' });
await Tenjin.optInOutUsingCMP();
await Tenjin.connect();
```

### Google DMA Parameters

```typescript
// Manual control
await Tenjin.setGoogleDMAParameters({
  adPersonalization: true,
  adUserData: true
});

// Toggle collection
await Tenjin.optInGoogleDMA();   // default
await Tenjin.optOutGoogleDMA();
```

---

## 10. Impression Level Ad Revenue (ILRD)

> **Note:** ILRD is a paid feature. Contact your Tenjin account manager before implementing.

### AppLovin

```typescript
await Tenjin.eventAdImpressionAppLovin({
  json: {
    ad_unit_id: 'your_ad_unit_id',
    revenue: 0.01,
    revenue_precision: 'estimated',
    network_placement: 'banner_home',
    format: 'BANNER'
  }
});
```

### AdMob

> **Important:** despite its name, `value_micros` is **not** in micros on iOS. The iOS SDK reads it as
> currency units (e.g. `0.01` USD); the Android SDK reads it as micros (e.g. `10000`).
> AdMob plugins report micros, so divide by 1,000,000 on iOS only.
> Sending raw micros on iOS inflates ad revenue 1,000,000x; dividing on Android reports 1,000,000x too little.

```typescript
import { Capacitor } from '@capacitor/core';

// valueMicros comes from the AdMob paid-event callback, in micros
const valueMicros = 10000;
const isIOS = Capacitor.getPlatform() === 'ios';

await Tenjin.eventAdImpressionAdMob({
  json: {
    ad_unit_id: 'ca-app-pub-xxx/yyy',
    value_micros: isIOS ? valueMicros / 1000000 : valueMicros,
    currency_code: 'USD',
    precision_type: 1
  }
});
```

### IronSource

```typescript
await Tenjin.eventAdImpressionIronSource({
  json: {
    ad_unit: 'rewardedVideo',
    revenue: 0.02,
    ad_network: 'ironSource',
    placement: 'level_complete'
  }
});
```

### Other Supported Networks

```typescript
// TopOn
await Tenjin.eventAdImpressionTopOn({ json: topOnImpressionData });

// HyperBid
await Tenjin.eventAdImpressionHyperBid({ json: hyperBidImpressionData });

// TradPlus
await Tenjin.eventAdImpressionTradPlus({ json: tradPlusImpressionData });

// CAS (Clever Ads Solutions)
await Tenjin.eventAdImpressionCAS({ json: casImpressionData });
```

---

## 11. User Identity, Attribution & Deep Links

### Customer User ID

```typescript
await Tenjin.setCustomerUserId({ userId: 'user_123' });
```

Reading it back needs care. The TypeScript definition declares `getCustomerUserId()` as `Promise<void>`, but the native layer resolves an object `{ userId }`. On iOS the promise **does not resolve at all** when no user ID has been set, so never `await` it on a startup path:

```typescript
Tenjin.getCustomerUserId().then((result) => {
  const userId = (result as unknown as { userId?: string } | undefined)?.userId;
  console.log('Tenjin customer user ID:', userId);
});
```

### Analytics Installation ID

A locally generated persistent identifier (useful when IDFA/AAID is unavailable). The TypeScript definition declares `Promise<string | null>`, but the native layer resolves an object `{ installationId }`. Handle both, and do not `await` it on a startup path (on iOS the promise does not resolve when there is no ID yet):

```typescript
Tenjin.getAnalyticsInstallationId().then((result) => {
  const value = result as unknown as { installationId?: string } | string | null;
  const analyticsId = typeof value === 'string' ? value : value?.installationId ?? null;
  console.log('Tenjin analytics installation ID:', analyticsId);
});
```

### Attribution Info (LiveOps Campaigns)

> **Note:** This is a paid feature.

```typescript
const info = await Tenjin.getAttributionInfo();
const adNetwork = info['ad_network'];
const campaignName = info['campaign_name'];
```

Values are returned only when available. Other keys: `advertising_id`, `campaign_id`, `tenjin_parameter_0` … `tenjin_parameter_5`.

### Re-engagement Deep Links

Report the URL the app was opened with, so re-engagement clicks can be attributed. Forward both the launch link and links received while the app is running:

```typescript
import { App } from '@capacitor/app';

const launch = await App.getLaunchUrl();
if (launch?.url) {
  await Tenjin.handleOpenUrl({ url: launch.url });
}

await App.addListener('appUrlOpen', (event) => {
  void Tenjin.handleOpenUrl({ url: event.url });
});
```

On Android, opens that start or recreate the Activity are captured automatically, so this is only needed for links delivered to an Activity that is already running.

### User Profile Data

The SDK automatically tracks sessions, IAP revenue, and ad revenue. Access the data programmatically:

```typescript
const profile = await Tenjin.getUserProfileDictionary();

// Profile contains:
// - session_count: number
// - total_session_time: number (milliseconds)
// - average_session_length: number (milliseconds)
// - last_session_length: number (milliseconds)
// - iap_transaction_count: number
// - total_ilrd_revenue_usd: number
// - first_session_date: string (ISO8601, optional)
// - last_session_date: string (ISO8601, optional)
// - current_session_length: number (optional)
// - iap_revenue_by_currency: object (optional)
// - purchased_product_ids: array (optional)
// - ilrd_revenue_by_network: object (optional)

// Reset all profile data
await Tenjin.resetUserProfile();
```

---

## 12. Additional Configuration

### A/B Testing with App Subversion

```typescript
await Tenjin.initialize({ sdkKey: '<SDK_KEY>' });
await Tenjin.appendAppSubversion({ version: 8888 });  // Reports as e.g. "1.0.1.8888"
await Tenjin.connect();
```

### Event Caching (Offline Support)

Enable retry/cache for events when the device has no connectivity:

```typescript
await Tenjin.setCacheEventSetting({ setting: true });
```

The setting is stored on the device. Removing the call in a later release does not turn caching off; call it with `setting: false` to disable it.

### Request Encryption

Enable encryption for SDK requests:

```typescript
await Tenjin.setEncryptRequestsSetting({ setting: true });
```

---

## 13. Google Ads On-Device Conversion Measurement (ICM / ODM, iOS Only)

> **Only for apps that run Google Ads campaigns for this iOS app.** Before adding anything, ask the developer:
>
> "Do you run Google Ads (App campaigns) for your iOS app?"
>
> Ad spend cannot be seen in the project, so do not guess. If the answer is no, or they are not sure, skip this section: do not add Google's SDK and do not add the connect delay.

Google calls this Integrated Conversion Measurement (ICM). It relies on Google's on-device conversion measurement (ODM) SDK, `GoogleAdsOnDeviceConversion`, and is iOS only.

The Tenjin iOS SDK (1.14.8 or newer) uses it by itself once Google's SDK is in the app: when the Tenjin SDK is initialized it asks Google's SDK for the install's conversion data, stores it, and sends it with its requests. There is no Tenjin method to call. `ionic-capacitor-tenjin` uses the native iOS SDK, so this works without any TypeScript call. Two things are needed:

1. Google's SDK in the iOS app.
2. A short delay before the first `connect()`, so Google's SDK has time to produce the data.

### Add Google's SDK

**Check first whether it is already there.** Firebase Analytics depends on Google's SDK, so apps that use the Capacitor Firebase Analytics plugin already have it. Look for `GoogleAdsOnDeviceConversion` in `ios/App/Podfile.lock`. If it is listed, do not add it again (a second, different version can break `pod install`); go straight to the delay below. If you add it to a project that also has Firebase Analytics, use the version Google pairs with that Firebase version: see the [version mapping table](https://github.com/googleads/google-ads-on-device-conversion-ios-sdk#version-mapping-with-ga4f-sdk).

Resolve the version of Google's SDK the same way as Tenjin's, and use it wherever a snippet says `<GOOGLE_ODM_VERSION>`:

```bash
curl -s https://trunk.cocoapods.org/api/v1/pods/GoogleAdsOnDeviceConversion | grep -o '"name":"[0-9.]*"' | cut -d'"' -f4 | sort -V | tail -1
```

**CocoaPods** (projects with an `ios/App/Podfile`): in `ios/App/Podfile`, inside the `target 'App' do` block, after `capacitor_pods`, add the pod, then run `npx cap sync ios`:

```ruby
pod 'GoogleAdsOnDeviceConversion', '~> <GOOGLE_ODM_VERSION>'
```

**Swift Package Manager** (projects without a `Podfile`): open `ios/App/App.xcodeproj` in Xcode and add `https://github.com/googleads/google-ads-on-device-conversion-ios-sdk` to the `App` target with "Up to Next Major Version" from `<GOOGLE_ODM_VERSION>`.

### Delay the First connect()

Google's SDK starts working when the Tenjin SDK is initialized and usually needs under a second. Make the **first** `connect()` of each app run happen at least 3 seconds after initialization; later connects (returns to the foreground) need no delay. Waiting for the tracking prompt often provides this already, but not when the user answered it on an earlier launch or tracking is disabled on the device, so add the delay explicitly. Do it on iOS only.

In the `connectTenjin()` function from Section 4, record when the SDK was initialized and wait before the first connect:

```typescript
let initializedAt = 0;
let connectedOnce = false;

// The first connect() of each app run on iOS waits until 3 seconds after
// initialize(), so Google's on-device conversion SDK can produce its data.
async function waitForGoogleOnDeviceConversion(): Promise<void> {
  if (Capacitor.getPlatform() !== 'ios' || connectedOnce) return;
  connectedOnce = true;
  const remaining = 3000 - (Date.now() - initializedAt);
  if (remaining > 0) {
    await new Promise((resolve) => setTimeout(resolve, remaining));
  }
}
```

Set `initializedAt = Date.now();` right after `await Tenjin.initialize({ sdkKey });`, and call the helper just before connecting:

```typescript
await waitForGoogleOnDeviceConversion();
await Tenjin.connect();
```

**Verify.** Confirm `GoogleAdsOnDeviceConversion` appears in `ios/App/Podfile.lock` (or the package list in Xcode) after installing. When Google's SDK returns data, the first `connect()` of a fresh install carries it as `omd_info`: with iOS debug logs on (Section 5), the `request body` line contains `omd_info=`. The data is fetched once per install, so reinstall the app to test again.

---

## 14. Integration Checklist

When integrating Tenjin into an Ionic Capacitor project, verify these items:

- [ ] **SDK version** was resolved by `npm install ionic-capacitor-tenjin@latest`, not written by hand
- [ ] **Capacitor** is version 6.0.0 or higher
- [ ] **`npx cap sync`** was run after installing the plugin
- [ ] **Two SDK keys**, selected with `Capacitor.getPlatform()`, each belonging to the Tenjin app with that platform's bundle ID; placeholders are replaced
- [ ] **iOS Info.plist** has `NSUserTrackingUsageDescription` with a user-facing message
- [ ] **iOS Info.plist** has `NSAdvertisingAttributionReportEndpoint` set to `https://tenjin-skan.com`
- [ ] **iOS minimum version** is 14.0 or higher
- [ ] **Android** declares `play-services-ads-identifier` and `play-services-appset`
- [ ] **Android Manifest** has `INTERNET`, `ACCESS_NETWORK_STATE` and `AD_ID` permissions and the `TENJIN_APP_STORE` meta-data
- [ ] **Android minimum SDK** is 22 or higher
- [ ] **The ATT prompt** is requested once, when the app is active, before `connect()` on iOS
- [ ] **`connect()`** is called on every launch and every return to the foreground
- [ ] **Custom events** are only sent after `connect()` has been called
- [ ] **Both platforms** show a 200 / `"success":true` response in the device log
- [ ] **Google ICM / ODM** (only if the app runs Google Ads campaigns on iOS): `GoogleAdsOnDeviceConversion` is in the app once, and the first `connect()` of each run comes at least 3 seconds after initialization
- [ ] Integration is verified using the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics)

---

## 15. Common Mistakes to Avoid

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Writing a version into `package.json` from memory | It is usually many releases old and lacks the APIs in this guide | `npm install ionic-capacitor-tenjin@latest` |
| One SDK key for both platforms | Each platform is a separate Tenjin app; the wrong key gets `unauthorized` | Select the key with `Capacitor.getPlatform()` |
| Verifying on one platform only | The other platform uses a different key and app | Check the device log on iOS and on Android |
| Using Capacitor 5 or older, or Cordova | The plugin requires Capacitor 6+ | Upgrade Capacitor first |
| `import Tenjin from 'ionic-capacitor-tenjin'` | There is no default export | `import { Tenjin } from 'ionic-capacitor-tenjin'` |
| Passing positional arguments | Every method takes one options object | `Tenjin.eventWithName({ name: '...' })` |
| Forgetting `npx cap sync` | Plugin won't be registered with native platforms | Run `npx cap sync` after installing |
| Missing `play-services-ads-identifier` on Android | No advertising ID: requests are rejected with `invalid device identifier` | Add it and `play-services-appset` |
| Missing `AD_ID` permission on Android 13+ | Cannot access the advertising ID | Add the permission to AndroidManifest.xml |
| Missing `TENJIN_APP_STORE` meta-data | The store is reported as `unspecified` | Add the meta-data to the `<application>` tag |
| Adding a second ATT prompt | The app already asks elsewhere | Call `connect()` after the existing request |
| Calling `connect()` only on first launch | Tenjin needs session data on every launch; accounts may be suspended | Call `connect()` on every launch and foreground |
| Awaiting `getCustomerUserId()` during startup | On iOS the promise never resolves when no ID is set | Use `.then()` off the startup path |
| Sending events before `connect()` | Events will not be processed | Always call `connect()` first |
| Event names over 80 characters | Will be rejected | Keep event names concise |
| Exceeding 500 unique event names | Additional events will be dropped | Reuse event names with different values |
| Sending AdMob `value_micros` without platform branching | iOS reads it as currency units, Android as micros; revenue is off by 1,000,000x | Divide the micros value by 1,000,000 on iOS only |
| Using SKAN methods on Android | They do nothing on Android | Check platform before calling |
| Relaunching within 30 seconds while testing | The native SDK skips the second `connect()` and sends nothing | Wait 30 seconds, or clear app data / reinstall |
| Adding Google's on-device conversion SDK to an app that does not run Google Ads | An unneeded dependency and a delayed first connect for nothing | Ask the developer first; skip the section if they do not run Google Ads on iOS |
| Adding `GoogleAdsOnDeviceConversion` when Firebase Analytics already brings it | Two version requirements for one pod; `pod install` can fail | Check the lockfile first; if adding it next to Firebase, use Google's version mapping |
| First `connect()` right after initialization in an app with Google's ODM SDK | Google's data is not ready yet, so the first open is sent without it | Make the first `connect()` of each run at least 3 seconds after initialization (iOS only) |

---

## 16. Full API Reference

All methods are on the named export `Tenjin` and return a `Promise`.

### Initialization

| Method | Purpose |
|--------|---------|
| `initialize({ sdkKey })` | Initialize SDK with the SDK key |
| `connect()` | Send install/session data to Tenjin |

### Events & Revenue

| Method | Purpose |
|--------|---------|
| `eventWithName({ name })` | Custom event (name only) |
| `eventWithNameAndValue({ name, value })` | Custom event with string value |
| `transaction({ productName, currencyCode, quantity, unitPrice })` | Purchase tracking |

### SKAdNetwork (iOS Only)

| Method | Purpose |
|--------|---------|
| `updatePostbackConversionValue({ conversionValue })` | Set basic conversion value (0-63) |
| `updatePostbackConversionValueCoarseValue({ conversionValue, coarseValue })` | Set with coarse value |
| `updatePostbackConversionValueCoarseValueLockWindow({ conversionValue, coarseValue, lockWindow })` | Set with coarse value and lock |

### Privacy & Consent

| Method | Purpose |
|--------|---------|
| `optIn()` / `optOut()` | GDPR full opt-in/out |
| `optInParams({ params })` / `optOutParams({ params })` | Granular parameter control |
| `optInOutUsingCMP()` | Automatic CMP-based consent |
| `optInGoogleDMA()` / `optOutGoogleDMA()` | Google DMA parameter control |
| `setGoogleDMAParameters({ adPersonalization, adUserData })` | Set Google DMA consent flags |

### Ad Revenue (ILRD)

| Method | Purpose |
|--------|---------|
| `eventAdImpressionAppLovin({ json })` | AppLovin impression |
| `eventAdImpressionAdMob({ json })` | AdMob impression |
| `eventAdImpressionIronSource({ json })` | IronSource impression |
| `eventAdImpressionTopOn({ json })` | TopOn impression |
| `eventAdImpressionHyperBid({ json })` | HyperBid impression |
| `eventAdImpressionTradPlus({ json })` | TradPlus impression |
| `eventAdImpressionCAS({ json })` | CAS impression |

### Identity & Analytics

| Method | Purpose |
|--------|---------|
| `setCustomerUserId({ userId })` | Set custom user identifier |
| `getCustomerUserId()` | Retrieve stored user ID |
| `getAnalyticsInstallationId()` | Get persistent local analytics ID |
| `getAttributionInfo()` | Get attribution data (paid feature) |
| `handleOpenUrl({ url })` | Report an app-open deep link |
| `getUserProfileDictionary()` | Get user metrics as dictionary |
| `resetUserProfile()` | Clear all local profile data |

### Configuration

| Method | Purpose |
|--------|---------|
| `appendAppSubversion({ version })` | A/B test variant tracking |
| `setCacheEventSetting({ setting })` | Enable offline event caching |
| `setEncryptRequestsSetting({ setting })` | Enable request encryption |

---

## 17. How to Use This Document

**With any LLM:**

```
Add Tenjin to my Ionic app using this guide:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/ionic/llm-guide.md
```

**Keeping this document up to date:**

This guide is derived from the official [README.md](https://github.com/tenjin/tenjin-ionic-sdk/blob/master/README.md) and the TypeScript definitions in [definitions.ts](https://github.com/tenjin/tenjin-ionic-sdk/blob/master/src/definitions.ts). When the SDK is updated, review those sources and update this file accordingly.
