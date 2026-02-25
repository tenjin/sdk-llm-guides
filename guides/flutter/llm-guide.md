# Tenjin Flutter SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin Flutter SDK into a Flutter project without requiring external documentation lookups.
>
> **Requirements:** Flutter >= 3.3.0 | Dart >= 3.0.0 | iOS 10.0+ | Android API 21+
>
> **Sources:**
> - Repository: [github.com/tenjin/tenjin-flutter-sdk](https://github.com/tenjin/tenjin-flutter-sdk)
> - Full README: [README.md](https://github.com/tenjin/tenjin-flutter-sdk/blob/master/README.md)
> - pub.dev: [tenjin_plugin](https://pub.dev/packages/tenjin_plugin)
>
> **Important:** Always check the [latest release](https://pub.dev/packages/tenjin_plugin) before integrating. Do not use hardcoded version numbers from this document — fetch the current version from pub.dev.

---

## Before You Begin

### Check the Latest SDK Version

Before writing any integration code:

1. **Fetch the latest version** from [pub.dev](https://pub.dev/packages/tenjin_plugin)
2. **Use that version** in your `pubspec.yaml` declaration
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
> - **Purchase tracking** — track in-app purchases with receipt validation (Section 5)
> - **Subscription tracking** — track subscription IAP with StoreKit 2 or Google Play Billing (Section 6)
> - **Custom events** — track in-app actions like level completions or signups (Section 7)
> - **SKAdNetwork conversion values** — for SKAN attribution on iOS (Section 8)
> - **GDPR / consent management** — opt-in/out, CMP, Google DMA (Section 9)
> - **Deep linking** — handle attribution deep links (Section 10)
> - **Ad revenue (ILRD)** — impression-level revenue from ad networks (Section 11, paid feature)
> - **User identity & analytics** — customer user IDs, analytics IDs (Section 12)

Only implement the sections the developer requests. Do not add features they didn't ask for.

---

## Quick Context

Tenjin is a mobile attribution and analytics platform. The SDK tracks app installs, sessions, in-app purchases, ad revenue, and custom events. It integrates with Apple's ATT framework and SKAdNetwork for privacy-compliant attribution on iOS, and supports Google Play and Amazon stores on Android.

---

## 1. Installation

Add the dependency to your `pubspec.yaml`:

```yaml
dependencies:
  tenjin_plugin: ^1.3.0  # Check pub.dev for latest version
```

Then run:

```bash
flutter pub get
```

---

## 2. iOS Platform Setup

### Info.plist Configuration

Add these keys to `ios/Runner/Info.plist`:

```xml
<!-- Required for ATT prompt (iOS 14+) -->
<key>NSUserTrackingUsageDescription</key>
<string>We use this data to provide a better and personalized ad experience.</string>

<!-- Required for SKAdNetwork postbacks (iOS 15+) -->
<key>NSAdvertisingAttributionReportEndpoint</key>
<string>https://tenjin-skan.com</string>
```

### Podfile Configuration

Ensure your `ios/Podfile` has the minimum iOS version set:

```ruby
platform :ios, '10.0'
```

After adding the plugin, run:

```bash
cd ios && pod install
```

---

## 3. Android Platform Setup

### AndroidManifest.xml Permissions

Add these permissions to `android/app/src/main/AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

<!-- Required for Android 13+ (API 33) -->
<uses-permission android:name="com.google.android.gms.permission.AD_ID" />
```

### build.gradle Configuration

In `android/app/build.gradle`, ensure the minimum SDK is set:

```gradle
android {
    defaultConfig {
        minSdkVersion 21
    }
}
```

### ProGuard / R8 Rules

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

On iOS 14+, Apple requires the ATT prompt before accessing the IDFA. The **recommended** pattern is to request tracking authorization first, then call `connect()`. This ensures Tenjin receives the IDFA when the user grants permission.

> **Critical:** `connect()` must run on **every** app launch, not just the first launch. Tenjin may suspend accounts that only call connect on first open.

### Recommended Implementation

```dart
import 'dart:io';
import 'package:tenjin_plugin/tenjin_plugin.dart';

class TenjinService {
  static final TenjinSDK _instance = TenjinSDK.instance;

  static Future<void> initialize() async {
    // Initialize with API key
    _instance.init(apiKey: '<SDK_KEY>');

    // Register for SKAdNetwork (iOS only)
    if (Platform.isIOS) {
      _instance.registerAppForAdNetworkAttribution();
    }

    // Request ATT and connect
    await _connectWithATT();
  }

  static Future<void> _connectWithATT() async {
    if (Platform.isIOS) {
      // Request tracking authorization first (iOS 14+)
      await _instance.requestTrackingAuthorization();
    }

    // Always connect after ATT request completes
    _instance.connect();
  }
}
```

### Using in Your App

Call the initialization early in your app lifecycle:

```dart
import 'package:flutter/material.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await TenjinService.initialize();
  runApp(MyApp());
}
```

### Enable Debug Logging (Development Only)

The Flutter SDK does not expose a debug log method directly. To verify integration:
1. Use the [Live Test Device Data Tool](https://www.tenjin.io/dashboard/sdk_diagnostics) in the Tenjin dashboard
2. Check native logs in Xcode (iOS) or Android Studio (Android)

---

## 5. Purchase Event Tracking

### Transaction with Receipt Validation

For validated purchases, pass platform-specific receipt data:

```dart
import 'dart:io';

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

When not using platform receipt validation:

```dart
TenjinSDK.instance.transaction(
  'premium_upgrade',  // productName
  'USD',              // currencyCode
  1,                  // quantity
  9.99,               // unitPrice
);
```

---

## 6. Subscription Tracking

For subscription purchases, use the `subscription` method with full transaction data:

### iOS (StoreKit 2)

```dart
TenjinSDK.instance.subscription(
  productId: 'com.example.premium_monthly',
  currencyCode: 'USD',
  unitPrice: 9.99,
  iosTransactionId: '2000000123456789',
  iosOriginalTransactionId: '2000000123456789',
  iosReceipt: 'base64_encoded_receipt_data',
  iosSKTransaction: '{"id": 2000000123456789, ...}',  // JSON serialized transaction
);
```

### Android (Google Play Billing)

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

If using the `in_app_purchase` package, extract the necessary data from `PurchaseDetails`:

```dart
import 'package:in_app_purchase/in_app_purchase.dart';

void trackSubscription(PurchaseDetails purchase, ProductDetails product) {
  if (Platform.isIOS) {
    final iosPurchase = purchase as AppStorePurchaseDetails;
    TenjinSDK.instance.subscription(
      productId: purchase.productID,
      currencyCode: product.currencyCode,
      unitPrice: product.rawPrice,
      iosTransactionId: purchase.purchaseID ?? '',
      iosOriginalTransactionId: iosPurchase.skPaymentTransaction.originalTransaction?.transactionIdentifier ?? purchase.purchaseID ?? '',
      iosReceipt: purchase.verificationData.localVerificationData,
    );
  } else if (Platform.isAndroid) {
    final androidPurchase = purchase as GooglePlayPurchaseDetails;
    TenjinSDK.instance.subscription(
      productId: purchase.productID,
      currencyCode: product.currencyCode,
      unitPrice: product.rawPrice,
      androidPurchaseToken: androidPurchase.billingClientPurchase.purchaseToken,
      androidPurchaseData: purchase.verificationData.localVerificationData,
      androidDataSignature: androidPurchase.billingClientPurchase.signature,
    );
  }
}
```

**Notes:**
- Add your **App-Specific Shared Secret** (iOS) or **Base64-encoded RSA public key** (Android) in the Tenjin dashboard
- Send **one transaction per billing interval** (at first charge and each renewal)
- Do **not** send transactions during free trial periods

---

## 7. Custom Events

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

## 8. SKAdNetwork Conversion Values (iOS Only)

```dart
import 'dart:io';

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

## 9. GDPR & Privacy Compliance

### Full Opt-In / Opt-Out

```dart
TenjinSDK.instance.init(apiKey: '<SDK_KEY>');

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
]);

// Or send everything EXCEPT these parameters
TenjinSDK.instance.optOutParams([
  'locale',
  'timezone',
  'build_id',
]);
```

> **Required parameter:** `developer_device_id` must always be included for proper device tracking. Events missing this parameter will not be processed.

### CMP-Based Consent

Automatically opt in/out based on CMP consent (TCF purpose 1):

```dart
TenjinSDK.instance.init(apiKey: '<SDK_KEY>');
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

## 10. Deep Linking

The Flutter SDK retrieves deferred deep link data through the attribution info:

```dart
Future<void> handleDeepLink() async {
  final attributionInfo = await TenjinSDK.instance.getAttributionInfo();

  if (attributionInfo != null && attributionInfo['clicked_tenjin_link'] == true) {
    // User came from a Tenjin attribution link
    final campaign = attributionInfo['campaign_name'];
    final adset = attributionInfo['adset_name'];

    // Handle deep link parameters
  }
}
```

> **Note:** `getAttributionInfo()` is a paid feature. Contact your Tenjin account manager for access.

---

## 11. Impression Level Ad Revenue (ILRD)

> **Note:** ILRD is a paid feature. Contact your Tenjin account manager before implementing.

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

```dart
void onPaidEvent(AdValue adValue, String adUnitId) {
  TenjinSDK.instance.eventAdImpressionAdMob({
    'ad_unit_id': adUnitId,
    'value_micros': adValue.valueMicros,
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
// or with platform-aware conversion
TenjinSDK.instance.eventAdImpressionTradPlusAdInfo(tradPlusAdInfo);
```

---

## 12. User Identity & Analytics

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

---

## 13. Additional Configuration

### A/B Testing with App Subversion

```dart
TenjinSDK.instance.init(apiKey: '<SDK_KEY>');
TenjinSDK.instance.appendAppSubversion(8888);  // Reports as e.g. "1.0.1.8888"
TenjinSDK.instance.connect();
```

### Event Caching (Offline Support)

Enable retry/cache for events when the device has no connectivity:

```dart
TenjinSDK.instance.setCacheEventSetting(true);
```

### Request Encryption

Enable encryption for SDK requests:

```dart
TenjinSDK.instance.setEncryptRequestsSetting(true);
```

---

## 14. Integration Checklist

When integrating Tenjin into a Flutter project, verify these items:

- [ ] **SDK version** is the latest from [pub.dev](https://pub.dev/packages/tenjin_plugin)
- [ ] **iOS Info.plist** has `NSUserTrackingUsageDescription` with a user-facing message
- [ ] **iOS Info.plist** has `NSAdvertisingAttributionReportEndpoint` set to `https://tenjin-skan.com`
- [ ] **Android Manifest** has `INTERNET` and `ACCESS_NETWORK_STATE` permissions
- [ ] **Android Manifest** has `AD_ID` permission for Android 13+
- [ ] **ATT prompt** is requested before calling `connect()` on iOS 14+
- [ ] **`connect()`** is called on every app launch, not just first launch
- [ ] **`registerAppForAdNetworkAttribution()`** is called on iOS
- [ ] **Custom events** are only sent after `connect()` has been called
- [ ] **`<SDK_KEY>`** placeholder is replaced with the actual key from the Tenjin dashboard
- [ ] **ProGuard rules** are added if using Android code obfuscation
- [ ] Integration is verified using the [Live Test Device Data Tool](https://www.tenjin.io/dashboard/sdk_diagnostics)

---

## 15. Common Mistakes to Avoid

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Calling `connect()` only on first launch | Tenjin needs session data on every launch; accounts may be suspended | Call `connect()` in your app initialization on every launch |
| Calling `connect()` before ATT request | IDFA will be zeros, degrading attribution quality | Call `requestTrackingAuthorization()` first, then `connect()` |
| Sending events before `connect()` | Events will not be processed | Always call `connect()` first |
| Missing `AD_ID` permission on Android | Cannot access AAID on Android 13+, degrades attribution quality | Add the permission to AndroidManifest.xml |
| Not calling `registerAppForAdNetworkAttribution()` | SKAdNetwork postbacks won't work | Call it during iOS initialization |
| Event names over 80 characters | Will be rejected | Keep event names concise |
| Exceeding 500 unique event names | Additional events will be dropped | Reuse event names with different values |
| Sending subscription transactions during trial | Inflates revenue metrics | Only send at first charge and renewals |
| Missing `developer_device_id` in opt-in params | Events will not be processed | Always include `developer_device_id` in `optInParams` |

---

## 16. Full API Reference

### Initialization

| Method | Purpose |
|--------|---------|
| `init(apiKey:)` | Initialize SDK with API key |
| `connect()` | Send install/session data to Tenjin |
| `registerAppForAdNetworkAttribution()` | Register for SKAdNetwork (iOS only) |
| `requestTrackingAuthorization()` | Request ATT permission (iOS only) |

### Events & Revenue

| Method | Purpose |
|--------|---------|
| `eventWithName(String)` | Custom event (name only) |
| `eventWithNameAndValue(String, int)` | Custom event with integer value |
| `transaction(...)` | Manual revenue tracking |
| `transactionWithReceipt(...)` | Purchase with receipt validation |
| `subscription(...)` | Subscription tracking with full transaction data |

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

### Identity & Analytics

| Method | Purpose |
|--------|---------|
| `setCustomerUserId(String)` | Set custom user identifier |
| `getCustomerUserId()` | Retrieve stored user ID |
| `getAnalyticsInstallationId()` | Get persistent local analytics ID |
| `getAttributionInfo()` | Get attribution data (paid feature) |

### Configuration

| Method | Purpose |
|--------|---------|
| `appendAppSubversion(int)` | A/B test variant tracking |
| `setCacheEventSetting(bool)` | Enable offline event caching |
| `setEncryptRequestsSetting(bool)` | Enable request encryption |

---

## 17. How to Use This Document

**With any LLM:**

```
Add Tenjin to my Flutter app using this guide:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/flutter/llm-guide.md
```

**Keeping this document up to date:**

This guide is derived from the official [README.md](https://github.com/tenjin/tenjin-flutter-sdk/blob/master/README.md) and the public API in [tenjin_sdk.dart](https://github.com/tenjin/tenjin-flutter-sdk/blob/master/lib/tenjin_sdk.dart). When the SDK is updated, review those sources and update this file accordingly.
