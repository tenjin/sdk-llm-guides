# Tenjin Flutter SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin Flutter SDK into a Flutter project without requiring external documentation lookups, except for the version lookup below.
>
> **Requirements:** Flutter >= 3.3.0 | Dart >= 3.0.0 | iOS 12.0+ | Android API 21+
>
> **Sources:**
> - Repository: [github.com/tenjin/flutter-sdk](https://github.com/tenjin/flutter-sdk)
> - Full README: [README.md](https://github.com/tenjin/flutter-sdk/blob/main/README.md)
> - Subscriptions: [SUBSCRIPTIONS_TRACKING.md](https://github.com/tenjin/flutter-sdk/blob/main/SUBSCRIPTIONS_TRACKING.md)
> - pub.dev: [tenjin_plugin](https://pub.dev/packages/tenjin_plugin)

---

## Before You Begin

### Resolve the SDK Version

This document contains no SDK version number on purpose. **Do not use a version you remember**: versions recalled from training data are usually many releases old.

The simplest way is to let `flutter pub add` resolve and write the current version (Section 1). To see the current version, or if you edit `pubspec.yaml` by hand, run this and use its output wherever a snippet says `<TENJIN_SDK_VERSION>`:

```bash
curl -s https://pub.dev/api/packages/tenjin_plugin | sed -n 's/.*"latest":{"version":"\([^"]*\)".*/\1/p'
```

If you cannot run commands, fetch `https://pub.dev/api/packages/tenjin_plugin` and read `latest.version`. If you can do neither, stop and ask the developer for the current version. Never leave `<TENJIN_SDK_VERSION>` in `pubspec.yaml` and never guess.

### One App and One SDK Key per Platform

A Tenjin app is **one bundle ID / application ID on one platform**. A Flutter project that ships on iOS and Android is therefore **two Tenjin apps with two SDK keys**, and the code must pick the right one at runtime:

- Tenjin's servers look the app up by the platform and the bundle ID the request carries, then check that the SDK key belongs to that app. The iOS key is refused on Android and the Android key is refused on iOS.
- Anything that changes the bundle ID changes the Tenjin app: an Android `applicationIdSuffix ".debug"`, a product flavor, or an iOS configuration with its own `PRODUCT_BUNDLE_IDENTIFIER`. Either register that ID as its own app in the Tenjin dashboard and use its key in those builds, or expect those builds to be rejected (see [Verify from the Device Log](#5-verify-from-the-device-log)).

Before writing code, read the Android `applicationId` (and suffixes/flavors) in `android/app/build.gradle(.kts)` and the iOS `PRODUCT_BUNDLE_IDENTIFIER` in `ios/Runner.xcodeproj/project.pbxproj`, and tell the developer which IDs the project produces.

### Get the SDK Keys

**Ask the developer for one Tenjin SDK key per platform the project builds for.** Code examples use `<IOS_SDK_KEY>` and `<ANDROID_SDK_KEY>` as placeholders (`<SDK_KEY>` where the platform does not matter). Before writing any integration code, prompt the user:

> "Tenjin needs one SDK key per platform. What is the SDK key of your iOS app (bundle ID `<the iOS bundle ID you found>`) and of your Android app (application ID `<the Android ID you found>`)? You can find each in the [Tenjin dashboard](https://www.tenjin.com/dashboard/organizations) on that app's page. If you don't have them handy, I can use placeholders and you can fill them in later — just search your project for `TENJIN_SDK_KEY_PLACEHOLDER` to find them."

If the developer provides the keys, substitute them directly in all generated code. If they prefer to add them later, use the literal strings `TENJIN_SDK_KEY_PLACEHOLDER_IOS` and `TENJIN_SDK_KEY_PLACEHOLDER_ANDROID` so they are easy to find with a project-wide search. If the project builds for one platform only, ask for that key only. Never copy a key from a sample project or from another app.

## Integration Workflow

Follow this two-step approach:

1. **First, integrate the basics.** Complete sections 1–5 (Installation, iOS Setup, Android Setup, Core Initialization, Verify from the Device Log). This gives the developer install tracking, session tracking, and ATT support — the foundation every Tenjin integration needs.

2. **Then, ask what else they need.** After the basic integration is working, prompt the user:

> "Tenjin basic integration is done (install tracking + ATT). Would you like to add any of these features?"
> - **Purchase tracking** — track in-app purchases with receipt validation (Section 6)
> - **Subscription tracking** — track subscription IAP with StoreKit 2 or Google Play Billing (Section 7)
> - **Custom events** — track in-app actions like level completions or signups (Section 8)
> - **SKAdNetwork conversion values** — for SKAN attribution on iOS (Section 9)
> - **GDPR / consent management** — opt-in/out, CMP, Google DMA (Section 10)
> - **Attribution info & deep links** — LiveOps attribution data, re-engagement deep links (Section 11)
> - **Ad revenue (ILRD)** — impression-level revenue from ad networks (Section 12, paid feature)
> - **User identity & analytics** — customer user IDs, analytics IDs, user profile (Section 13)

Only implement the sections the developer requests. Do not add features they didn't ask for.

---

## Quick Context

Tenjin is a mobile attribution and analytics platform. The SDK tracks app installs, sessions, in-app purchases, ad revenue, and custom events. It integrates with Apple's ATT framework and SKAdNetwork for privacy-compliant attribution on iOS, and supports Google Play and Amazon stores on Android.

The Flutter plugin is a thin wrapper around the native Tenjin iOS and Android SDKs. Its whole Dart API is the `TenjinSDK` class in `package:tenjin_plugin/tenjin_sdk.dart`.

---

## 1. Installation

Add the dependency with:

```bash
flutter pub add tenjin_plugin
```

This resolves the current version from pub.dev and writes it to `pubspec.yaml`. If you edit `pubspec.yaml` by hand instead, use the version from [Resolve the SDK Version](#resolve-the-sdk-version):

```yaml
dependencies:
  tenjin_plugin: ^<TENJIN_SDK_VERSION>
```

Then run:

```bash
flutter pub get
```

If `tenjin_plugin` is already in `pubspec.yaml` with an older constraint, run `flutter pub upgrade tenjin_plugin` and check that `pubspec.lock` shows the current version.

The import is:

```dart
import 'package:tenjin_plugin/tenjin_sdk.dart';
```

---

## 2. iOS Platform Setup

### Info.plist Configuration

Add these keys to `ios/Runner/Info.plist`:

```xml
<!-- Required for the ATT prompt (iOS 14+). The app crashes on the ATT request if this is missing. -->
<key>NSUserTrackingUsageDescription</key>
<string>We use this data to provide a better and personalized ad experience.</string>

<!-- Required for SKAdNetwork postbacks (iOS 15+) -->
<key>NSAdvertisingAttributionReportEndpoint</key>
<string>https://tenjin-skan.com</string>
```

### Podfile Configuration

The plugin requires iOS 12.0 or higher. Make sure `ios/Podfile` does not set a lower platform:

```ruby
platform :ios, '12.0'
```

After adding the plugin, run:

```bash
cd ios && pod install
```

---

## 3. Android Platform Setup

The plugin already bundles the Google libraries the native SDK needs (Advertising ID, App Set ID, Install Referrer). Do not add them to the app's Gradle file.

### AndroidManifest.xml

Add these to `android/app/src/main/AndroidManifest.xml`:

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

The Dart API has no call to set the app store, so the `TENJIN_APP_STORE` meta-data is the only way to set it. Without it the store is reported as `unspecified`.

### Minimum SDK

The plugin requires `minSdk` 21 or higher. In `android/app/build.gradle`:

```gradle
android {
    defaultConfig {
        minSdkVersion 21
    }
}
```

Or in `android/app/build.gradle.kts`:

```kotlin
android {
    defaultConfig {
        minSdk = 21
    }
}
```

If the file uses `flutter.minSdkVersion`, leave it when it already resolves to 21 or higher.

### ProGuard / R8 Rules

Flutter release builds are minified by default. Add these rules to `android/app/proguard-rules.pro` (create the file and reference it from the `release` build type with `proguardFiles` if the project has none):

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

---

## 4. Core Initialization

### Where connect() Goes

- **On every launch and every return to the foreground**, not only on first open. Tenjin needs the session data, and accounts that only connect on first open may be suspended.
- **On iOS, after the user has answered the tracking prompt.** Calling `connect()` before the ATT answer sends a zeroed IDFA and degrades attribution.
- **Request ATT only when the app is active.** iOS shows the prompt only while the app is in the foreground and active. A request made in `main()` before the first frame may not display. Wait for the first frame or for the `resumed` lifecycle state.
- **If the app already has a tracking prompt, hook into it. Do not add a second one.** Search the project for `requestTrackingAuthorization` and for packages such as `app_tracking_transparency`. If the app already asks, call `TenjinSDK.instance.connect()` after that existing request completes and leave out the Tenjin `requestTrackingAuthorization()` call.

Calling `connect()` on every resume is safe: the native SDKs skip a `connect()` that comes within 30 seconds of the previous one.

### Recommended Implementation

```dart
import 'dart:io' show Platform;

import 'package:flutter/widgets.dart';
import 'package:tenjin_plugin/tenjin_sdk.dart';

class TenjinService with WidgetsBindingObserver {
  TenjinService._();

  static final TenjinService instance = TenjinService._();

  bool _connecting = false;

  /// Call once from main(), after WidgetsFlutterBinding.ensureInitialized().
  void start() {
    // One key per platform: an iOS app and an Android app are two Tenjin apps.
    final sdkKey = Platform.isAndroid ? '<ANDROID_SDK_KEY>' : '<IOS_SDK_KEY>';
    TenjinSDK.instance.initialize(sdkKey: sdkKey);

    if (Platform.isIOS) {
      // SKAdNetwork registration; only has an effect on iOS 14.0-15.3.
      TenjinSDK.instance.registerAppForAdNetworkAttribution();
    }

    WidgetsBinding.instance.addObserver(this);
    // First launch: wait for the first frame so iOS can show the ATT prompt.
    WidgetsBinding.instance.addPostFrameCallback((_) => _connect());
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) {
      _connect();
    }
  }

  Future<void> _connect() async {
    if (_connecting) return;
    _connecting = true;
    try {
      // iOS 14+: shows the ATT prompt the first time, returns at once afterwards.
      // Android: returns true at once.
      await TenjinSDK.instance.requestTrackingAuthorization();
      TenjinSDK.instance.connect();
    } finally {
      _connecting = false;
    }
  }
}
```

### Using in Your App

```dart
import 'package:flutter/material.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  TenjinService.instance.start();
  runApp(const MyApp());
}
```

> **Note:** `init(apiKey:)` is deprecated. Use `initialize(sdkKey:)`.

---

## 5. Verify from the Device Log

Do this before adding any optional feature, **once per platform**: the two platforms use different keys and different Tenjin apps, so one passing does not prove the other.

The Dart API has no debug-log call. The log lines come from the native SDKs.

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

The native iOS SDK prints requests and responses only after its `debugLogs()` method has been called. In a development build, call it natively in `ios/Runner/AppDelegate.swift` before `GeneratedPluginRegistrant.register(with: self)`:

```swift
import TenjinSDK

#if DEBUG
TenjinSDK.debugLogs()
#endif
```

If `import TenjinSDK` does not resolve in the Runner target, skip this and verify iOS with the dashboard tool below instead. With debug logs on, the Xcode console shows:

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
| `invalid device identifier` | 202 | The request carried no advertising ID | Android: add the `AD_ID` permission and test on a device with Google Play services |
| `not logged` | 202 | The SDK key is disabled | Enable the key in the dashboard or use another key of the same app |
| `ignored` | 202 | The request was filtered by an app-version rule configured for the app | Check the app's version rules in the dashboard |

A 202 is **not** success: the request was received and dropped.

### No Request at All

A `connect()` within 30 seconds of the previous one is skipped by the native SDK and sends nothing. The timestamp is stored on the device, so it survives an app restart and a hot restart.

- Android logs `Connect deduped by persisted timestamp` under the tag `TenjinSDK`. Wait 30 seconds or clear the app's data (`adb shell pm clear <applicationId>`).
- iOS logs `Connect sent ...s ago (interval: 30.0s), ignoring duplicate ping` with debug logs on. Wait 30 seconds or reinstall the app.

### In the Dashboard

After a 200 response, the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics) shows events for devices registered as test devices.

---

## 6. Purchase Event Tracking

### Transaction with Receipt Validation

For validated purchases, pass platform-specific receipt data. On iOS both `iosReceipt` and `iosTransactionId` are required; on Android both `androidPurchaseData` and `androidDataSignature` are required. If they are missing the call is dropped.

```dart
void trackPurchase({
  required String productId,
  required String currencyCode,
  required double unitPrice,
  required int quantity,
  // iOS
  String? iosReceipt,
  String? iosTransactionId,
  // Android
  String? androidPurchaseData,
  String? androidDataSignature,
}) {
  TenjinSDK.instance.transactionWithReceipt(
    productId: productId,
    currencyCode: currencyCode,
    unitPrice: unitPrice,
    quantity: quantity,
    iosReceipt: iosReceipt,
    iosTransactionId: iosTransactionId,
    androidPurchaseData: androidPurchaseData,
    androidDataSignature: androidDataSignature,
  );
}
```

### Manual Revenue (No Validation)

When not using platform receipt validation. Note that `quantity` is a `double` in this method:

```dart
TenjinSDK.instance.transaction(
  'premium_upgrade',  // productName
  'USD',              // currencyCode
  1.0,                // quantity (double)
  9.99,               // unitPrice
);
```

---

## 7. Subscription Tracking

Subscriptions are **not** captured by `connect()`. One of the methods below must be called from the purchase-handling code.

### iOS

The simplest path lets the native SDK fetch the StoreKit 2 transaction itself (iOS 16+; does nothing on Android):

```dart
await TenjinSDK.instance.subscriptionWithStoreKit(
  productId: 'com.example.premium_monthly',
  currencyCode: 'USD',
  unitPrice: 9.99,
);
```

Or pass the StoreKit 2 data yourself. On iOS **all four** `ios*` parameters are required; if one is missing the call is dropped with a console message:

```dart
TenjinSDK.instance.subscription(
  productId: 'com.example.premium_monthly',
  currencyCode: 'USD',
  unitPrice: 9.99,
  iosTransactionId: '2000000123456789',
  iosOriginalTransactionId: '2000000123456789',
  iosReceipt: 'jws_signed_transaction',
  iosSKTransaction: '{"id": 2000000123456789, ...}',  // StoreKit 2 transaction JSON
);
```

### Android (Google Play Billing)

On Android all three `android*` parameters are required:

```dart
TenjinSDK.instance.subscription(
  productId: 'premium_monthly',
  currencyCode: 'USD',
  unitPrice: 9.99,
  androidPurchaseToken: 'purchase_token_from_google_play',
  androidPurchaseData: 'purchase_data_json',
  androidDataSignature: 'signature_string',
);
```

### Integration with in_app_purchase Package

If using the `in_app_purchase` package:

```dart
import 'dart:io' show Platform;

import 'package:in_app_purchase/in_app_purchase.dart';
import 'package:in_app_purchase_android/in_app_purchase_android.dart';
import 'package:tenjin_plugin/tenjin_sdk.dart';

Future<void> trackSubscription(PurchaseDetails purchase, ProductDetails product) async {
  if (Platform.isIOS) {
    // The native SDK reads the StoreKit 2 transaction for this product.
    await TenjinSDK.instance.subscriptionWithStoreKit(
      productId: purchase.productID,
      currencyCode: product.currencyCode,
      unitPrice: product.rawPrice,
    );
  } else if (Platform.isAndroid && purchase is GooglePlayPurchaseDetails) {
    final billingPurchase = purchase.billingClientPurchase;
    TenjinSDK.instance.subscription(
      productId: purchase.productID,
      currencyCode: product.currencyCode,
      unitPrice: product.rawPrice,
      androidPurchaseToken: billingPurchase.purchaseToken,
      androidPurchaseData: billingPurchase.originalJson,
      androidDataSignature: billingPurchase.signature,
    );
  }
}
```

**Notes:**
- **iOS:** add the app's **App-Specific Shared Secret** in the Tenjin dashboard. Send one transaction per billing interval (first charge and each renewal), and none during a free trial.
- **Android:** subscriptions are verified through the **Google Play Developer API**, so the Android app needs Google Play Developer API access configured in the Tenjin dashboard (a different credential from the RSA public key used for one-time purchases). Send **once per subscription**, not once per renewal: Tenjin resolves renewals, trials and cancellations from the purchase token.

---

## 8. Custom Events

> **Prerequisite:** `connect()` must have been called before sending any custom events.

```dart
// Event without value
TenjinSDK.instance.eventWithName('level_complete');

// Event with integer value (used as count/sum)
TenjinSDK.instance.eventWithNameAndValue('coins_spent', 50);
```

**Limits:**
- Event names must be under **80 characters**
- Maximum **500 unique** event names per app

---

## 9. SKAdNetwork Conversion Values (iOS Only)

```dart
import 'dart:io' show Platform;

// Basic conversion value (0-63)
if (Platform.isIOS) {
  TenjinSDK.instance.updatePostbackConversionValue(5);
}

// With coarse value (iOS 16.1+ / SKAN 4.0)
if (Platform.isIOS) {
  TenjinSDK.instance.updatePostbackConversionValueCoarseValue(5, 'medium');
}

// With coarse value and lock window
if (Platform.isIOS) {
  TenjinSDK.instance.updatePostbackConversionValueCoarseValueLockWindow(5, 'high', true);
}
```

Valid coarse values: `"low"`, `"medium"`, `"high"`

---

## 10. GDPR & Privacy Compliance

### Full Opt-In / Opt-Out

```dart
TenjinSDK.instance.initialize(sdkKey: '<SDK_KEY>');

if (userConsented) {
  TenjinSDK.instance.optIn();
} else {
  TenjinSDK.instance.optOut();  // No API requests will be sent
}

TenjinSDK.instance.connect();
```

### Granular Parameter Control

```dart
// Only send these specific parameters
TenjinSDK.instance.optInParams([
  'ip_address',
  'advertising_id',
  'developer_device_id',
  'limit_ad_tracking',
  'referrer',
  'iad',
]);

// Or send everything EXCEPT these parameters
TenjinSDK.instance.optOutParams([
  'locale',
  'timezone',
  'build_id',
]);
```

> **Required parameters:** Tenjin needs at least `ip_address`, `advertising_id`, `developer_device_id`, `limit_ad_tracking`, `referrer` (Android) and `iad` (iOS) to track devices.

### CMP-Based Consent

Automatically opt in/out based on CMP consent (TCF purpose 1):

```dart
TenjinSDK.instance.initialize(sdkKey: '<SDK_KEY>');
TenjinSDK.instance.optInOutUsingCMP();
TenjinSDK.instance.connect();
```

### Google DMA Parameters

```dart
// Manual control
TenjinSDK.instance.setGoogleDMAParameters(true, true);  // (adPersonalization, adUserData)

// Toggle collection
TenjinSDK.instance.optInGoogleDMA();   // default
TenjinSDK.instance.optOutGoogleDMA();
```

---

## 11. Attribution Info & Deep Links

### Attribution Info (LiveOps Campaigns)

> **Note:** `getAttributionInfo()` is a paid feature. Contact your Tenjin account manager for access.

```dart
Future<void> readAttribution() async {
  final info = await TenjinSDK.instance.getAttributionInfo();
  if (info == null) return;

  final adNetwork = info['ad_network'];
  final campaignId = info['campaign_id'];
  final campaignName = info['campaign_name'];
}
```

Values are returned only when available. Other keys: `advertising_id`, `tenjin_parameter_0` … `tenjin_parameter_5`.

### Re-engagement Deep Links

Report the URL the app was opened with, so re-engagement clicks can be attributed. Forward both the launch link and links received while the app is running, from whatever deep-link package the app uses:

```dart
void reportOpenUrl(Uri uri) {
  TenjinSDK.instance.handleOpenUrl(uri.toString());
}
```

On Android, opens that start or recreate the Activity are captured automatically, so this is only needed for links delivered to an Activity that is already running.

---

## 12. Impression Level Ad Revenue (ILRD)

> **Note:** ILRD is a paid feature. Contact your Tenjin account manager before implementing.

Every method takes a `Map<String, dynamic>`.

### AppLovin

```dart
void onAdRevenuePaid(MaxAd ad) {
  TenjinSDK.instance.eventAdImpressionAppLovin({
    'ad_unit_id': ad.adUnitId,
    'revenue': ad.revenue,
    'network_name': ad.networkName,
    'placement': ad.placement,
  });
}
```

### AdMob

> **Important:** despite its name, `value_micros` is **not** in micros on iOS. The iOS SDK reads it as
> currency units (e.g. `0.012245` USD); the Android SDK reads it as micros (e.g. `12245`).
> `google_mobile_ads` reports micros on both platforms, so divide by 1,000,000 on iOS only.
> Sending raw micros on iOS inflates ad revenue 1,000,000x; dividing on Android reports 1,000,000x too little.

```dart
import 'dart:io' show Platform;

void onPaidEvent(AdValue adValue, String adUnitId) {
  // adValue.valueMicros is in micros on both platforms
  final value = Platform.isIOS
      ? adValue.valueMicros / 1000000.0
      : adValue.valueMicros;

  TenjinSDK.instance.eventAdImpressionAdMob({
    'ad_unit_id': adUnitId,
    'value_micros': value,
    'currency_code': adValue.currencyCode,
    'precision_type': adValue.precisionType.index,
  });
}
```

### IronSource

```dart
void onImpressionDataReady(ImpressionData data) {
  TenjinSDK.instance.eventAdImpressionIronSource({
    'ad_unit': data.adUnit,
    'revenue': data.revenue,
    'ad_network': data.adNetwork,
    'placement': data.placement,
  });
}
```

### TopOn

```dart
TenjinSDK.instance.eventAdImpressionTopOn(topOnImpressionData);
```

### HyperBid

```dart
TenjinSDK.instance.eventAdImpressionHyperBid(hyperBidImpressionData);
```

### TradPlus

```dart
TenjinSDK.instance.eventAdImpressionTradPlus(tradPlusAdInfo);
// or, to pass TradPlus's own adInfo map and let the plugin convert its keys per platform
TenjinSDK.instance.eventAdImpressionTradPlusAdInfo(tradPlusAdInfo);
```

---

## 13. User Identity & Analytics

### Customer User ID

```dart
// Set custom user identifier
TenjinSDK.instance.setCustomerUserId('user_123');

// Retrieve stored user ID
String? userId = await TenjinSDK.instance.getCustomerUserId();
```

### Analytics Installation ID

A locally generated persistent identifier (useful when IDFA/AAID is unavailable):

```dart
String? analyticsId = await TenjinSDK.instance.getAnalyticsInstallationId();
```

### User Profile Data

```dart
Map<String, dynamic>? profile = await TenjinSDK.instance.getUserProfileDictionary();

if (profile != null) {
  final sessionCount = profile['session_count'];
  final totalSessionTimeMs = profile['total_session_time'];
  final iapCount = profile['iap_transaction_count'];
  final adRevenueUsd = profile['total_ilrd_revenue_usd'];
}

// Reset all profile data
TenjinSDK.instance.resetUserProfile();
```

---

## 14. Additional Configuration

### A/B Testing with App Subversion

```dart
TenjinSDK.instance.initialize(sdkKey: '<SDK_KEY>');
TenjinSDK.instance.appendAppSubversion(8888);  // Reports as e.g. "1.0.1.8888"
TenjinSDK.instance.connect();
```

### Event Caching (Offline Support)

Enable retry/cache for events when the device has no connectivity:

```dart
TenjinSDK.instance.setCacheEventSetting(true);
```

The setting is stored on the device. Removing the call in a later release does not turn caching off; call `setCacheEventSetting(false)` to disable it.

### Request Encryption

Enable encryption for SDK requests:

```dart
TenjinSDK.instance.setEncryptRequestsSetting(true);
```

---

## 15. Integration Checklist

When integrating Tenjin into a Flutter project, verify these items:

- [ ] **SDK version** was resolved by `flutter pub add` or the pub.dev command in this guide, not from memory
- [ ] **The import** is `package:tenjin_plugin/tenjin_sdk.dart`
- [ ] **`initialize(sdkKey:)`** is used, not the deprecated `init(apiKey:)`
- [ ] **Two SDK keys**, selected with `Platform.isAndroid` / `Platform.isIOS`, each belonging to the Tenjin app with that platform's bundle ID; placeholders are replaced
- [ ] **iOS Info.plist** has `NSUserTrackingUsageDescription` with a user-facing message
- [ ] **iOS Info.plist** has `NSAdvertisingAttributionReportEndpoint` set to `https://tenjin-skan.com`
- [ ] **iOS Podfile** platform is 12.0 or higher
- [ ] **Android Manifest** has `INTERNET`, `ACCESS_NETWORK_STATE` and `AD_ID` permissions and the `TENJIN_APP_STORE` meta-data
- [ ] **Android `minSdk`** is 21 or higher
- [ ] **ProGuard rules** are added (Flutter release builds are minified)
- [ ] **The ATT prompt** is requested once, when the app is active, before `connect()` on iOS
- [ ] **`connect()`** is called on every launch and every resume
- [ ] **Custom events** are only sent after `connect()` has been called
- [ ] **Both platforms** show a 200 / `"success":true` response in the device log
- [ ] Integration is verified using the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics)

---

## 16. Common Mistakes to Avoid

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Importing `package:tenjin_plugin/tenjin_plugin.dart` | That file does not exist; the build fails | Import `package:tenjin_plugin/tenjin_sdk.dart` |
| Using an SDK version from memory | It is usually many releases old and lacks the APIs in this guide | Use `flutter pub add tenjin_plugin` or the pub.dev command |
| One SDK key for both platforms | Each platform is a separate Tenjin app; the wrong key gets `unauthorized` | Select the key with `Platform.isAndroid` |
| Verifying on one platform only | The other platform uses a different key and app | Check the device log on iOS and on Android |
| Using `init(apiKey:)` | Deprecated | Use `initialize(sdkKey:)` |
| Requesting ATT in `main()` before the first frame | The prompt only shows while the app is active and may be skipped | Request it after the first frame or on `resumed` |
| Adding a second ATT prompt | The app already asks elsewhere | Call `connect()` after the existing request |
| Calling `connect()` before the ATT request | IDFA will be zeros, degrading attribution quality | Call `requestTrackingAuthorization()` first, then `connect()` |
| Calling `connect()` only on first launch | Tenjin needs session data on every launch; accounts may be suspended | Call `connect()` on every launch and resume |
| Missing `AD_ID` permission on Android | No advertising ID: requests are rejected with `invalid device identifier` | Add the permission to AndroidManifest.xml |
| Missing ProGuard rules | Release builds fail at runtime only | Add the rules from Section 3 |
| Calling `subscription()` on iOS without all four `ios*` parameters | The call is dropped | Pass all four, or use `subscriptionWithStoreKit()` |
| Sending events before `connect()` | Events will not be processed | Always call `connect()` first |
| Event names over 80 characters | Will be rejected | Keep event names concise |
| Exceeding 500 unique event names | Additional events will be dropped | Reuse event names with different values |
| Sending AdMob `value_micros` without platform branching | iOS reads it as currency units, Android as micros; revenue is off by 1,000,000x | Divide `adValue.valueMicros` by 1,000,000 on iOS only |
| Relaunching within 30 seconds while testing | The native SDK skips the second `connect()` and sends nothing | Wait 30 seconds, or clear app data / reinstall |

---

## 17. Full API Reference

All methods are on `TenjinSDK.instance`.

### Initialization

| Method | Purpose |
|--------|---------|
| `initialize(sdkKey:)` | Initialize SDK with the SDK key |
| `connect()` | Send install/session data to Tenjin |
| `requestTrackingAuthorization()` | Request ATT permission (iOS; returns `true` on Android) |
| `registerAppForAdNetworkAttribution()` | Register for SKAdNetwork (iOS 14.0-15.3; no effect on newer iOS or Android) |

### Events & Revenue

| Method | Purpose |
|--------|---------|
| `eventWithName(String)` | Custom event (name only) |
| `eventWithNameAndValue(String, int)` | Custom event with integer value |
| `transaction(String, String, double, double)` | Manual revenue tracking |
| `transactionWithReceipt(...)` | Purchase with receipt validation |
| `subscription(...)` | Subscription tracking with full transaction data |
| `subscriptionWithStoreKit(...)` | iOS-only native StoreKit 2 subscription fetch |

### SKAdNetwork (iOS)

| Method | Purpose |
|--------|---------|
| `updatePostbackConversionValue(int)` | Set basic conversion value (0-63) |
| `updatePostbackConversionValueCoarseValue(int, String)` | Set with coarse value |
| `updatePostbackConversionValueCoarseValueLockWindow(int, String, bool)` | Set with coarse value and lock |

### Privacy & Consent

| Method | Purpose |
|--------|---------|
| `optIn()` / `optOut()` | GDPR full opt-in/out |
| `optInParams(List)` / `optOutParams(List)` | Granular parameter control |
| `optInOutUsingCMP()` | Automatic CMP-based consent |
| `optInGoogleDMA()` / `optOutGoogleDMA()` | Google DMA parameter control |
| `setGoogleDMAParameters(bool, bool)` | Set Google DMA consent flags |

### Ad Revenue (ILRD)

| Method | Purpose |
|--------|---------|
| `eventAdImpressionAppLovin(Map)` | AppLovin impression |
| `eventAdImpressionAdMob(Map)` | AdMob impression |
| `eventAdImpressionIronSource(Map)` | IronSource impression |
| `eventAdImpressionTopOn(Map)` | TopOn impression |
| `eventAdImpressionHyperBid(Map)` | HyperBid impression |
| `eventAdImpressionTradPlus(Map)` | TradPlus impression |
| `eventAdImpressionTradPlusAdInfo(Map)` | TradPlus impression from TradPlus's adInfo map |

### Identity & Analytics

| Method | Purpose |
|--------|---------|
| `setCustomerUserId(String)` | Set custom user identifier |
| `getCustomerUserId()` | Retrieve stored user ID |
| `getAnalyticsInstallationId()` | Get persistent local analytics ID |
| `getAttributionInfo()` | Get attribution data (paid feature) |
| `handleOpenUrl(String)` | Report an app-open deep link |
| `getUserProfileDictionary()` | Get user metrics as a map |
| `resetUserProfile()` | Clear all local profile data |

### Configuration

| Method | Purpose |
|--------|---------|
| `appendAppSubversion(int)` | A/B test variant tracking |
| `setCacheEventSetting(bool)` | Enable offline event caching |
| `setEncryptRequestsSetting(bool)` | Enable request encryption |

---

## 18. How to Use This Document

**With any LLM:**

```
Add Tenjin to my Flutter app using this guide:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/flutter/llm-guide.md
```

**Keeping this document up to date:**

This guide is derived from the official [README.md](https://github.com/tenjin/flutter-sdk/blob/main/README.md) and the public API in [tenjin_sdk.dart](https://github.com/tenjin/flutter-sdk/blob/main/lib/tenjin_sdk.dart). When the SDK is updated, review those sources and update this file accordingly.
