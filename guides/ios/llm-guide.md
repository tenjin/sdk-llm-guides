# Tenjin iOS SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin iOS SDK into an iOS project without requiring external documentation lookups, except for the version lookup below.
>
> **Minimum iOS:** 12.0 (App Tracking Transparency needs iOS 14, AdServices needs iOS 14.3; the SDK handles older systems)
>
> **Sources:**
> - Repository: [github.com/tenjin/tenjin-ios-sdk](https://github.com/tenjin/tenjin-ios-sdk)
> - Full README: [README.md](https://github.com/tenjin/tenjin-ios-sdk/blob/master/README.md)
> - Public API header: [TenjinSDK.h](https://github.com/tenjin/tenjin-ios-sdk/blob/master/TenjinSDK.h)
> - SPM package: [tenjin-ios-spm](https://github.com/tenjin/tenjin-ios-spm)
> - Release notes: [RELEASE_NOTES.md](https://github.com/tenjin/tenjin-ios-sdk/blob/master/RELEASE_NOTES.md)

---

## Before You Begin

### Resolve the SDK Version

This document contains no SDK version number on purpose. **Do not use a version you remember**: versions recalled from training data are usually many releases old. Run the command for the project's package manager and use its output wherever a snippet says `<TENJIN_SDK_VERSION>`.

CocoaPods:

```bash
curl -s https://trunk.cocoapods.org/api/v1/pods/TenjinSDK | grep -o '"name":"[0-9.]*"' | cut -d'"' -f4 | sort -V | tail -1
```

Swift Package Manager:

```bash
git ls-remote --tags --refs https://github.com/tenjin/tenjin-ios-spm.git | sed 's:.*refs/tags/::' | sort -V | tail -1
```

If you cannot run commands, fetch `https://trunk.cocoapods.org/api/v1/pods/TenjinSDK` and take the highest entry in `versions`. If you can do neither, stop and ask the developer for the current version. Never leave `<TENJIN_SDK_VERSION>` in a project file and never guess.

### One App and One SDK Key per Platform

A Tenjin app is **one bundle ID on one platform**. Its SDK key only works for that app:

- Tenjin's servers look the app up by the platform and the bundle ID the request carries, then check that the SDK key belongs to that app. A key from another app (for example the Android app's key) is refused.
- Anything that changes the bundle ID changes the Tenjin app. A Debug configuration with a `.debug` suffix, a second target, or a white-label scheme with its own `PRODUCT_BUNDLE_IDENTIFIER` is a different app as far as Tenjin is concerned. Either register that bundle ID as its own app in the Tenjin dashboard and use its key in those builds, or expect those builds to be rejected with HTTP 404 (see [Verify from the Device Log](#4-verify-from-the-device-log)).

Before writing code, read `PRODUCT_BUNDLE_IDENTIFIER` for every build configuration of the app target and tell the developer which bundle IDs the project produces.

### Get the SDK Key

**Ask the developer for their Tenjin SDK key.** Every code example in this document uses `<SDK_KEY>` as a placeholder. Before writing any integration code, prompt the user:

> "What is the Tenjin SDK key for your iOS app (bundle ID `<the bundle ID you found>`)? You can find it in the [Tenjin dashboard](https://www.tenjin.com/dashboard/organizations) on that app's page. It must be the key of the iOS app with exactly this bundle ID, not the key of your Android app. If you don't have it handy, I can use a placeholder and you can fill it in later — just search your project for `TENJIN_SDK_KEY_PLACEHOLDER` to find it."

If the developer provides their key, substitute it directly in all generated code. If they prefer to add it later, use the literal string `TENJIN_SDK_KEY_PLACEHOLDER` (not `<SDK_KEY>`) so it is easy to find with a project-wide search. Never copy a key from a sample project or from another app.

## Integration Workflow

Follow this two-step approach:

1. **First, integrate the basics.** Complete sections 1–4 (Installation, Info.plist, Core Initialization, Verify from the Device Log). This gives the developer install tracking, session tracking, and ATT support — the foundation every Tenjin integration needs.

2. **Then, ask what else they need.** After the basic integration is working, prompt the user:

> "Tenjin basic integration is done (install tracking + ATT). Would you like to add any of these features?"
> - **Purchase tracking** — StoreKit 1 or StoreKit 2 IAP, subscriptions (Section 5)
> - **Custom events** — track in-app actions like level completions or signups (Section 6)
> - **SKAdNetwork conversion values** — for SKAN attribution (Section 7)
> - **GDPR / consent management** — opt-in/out, CMP, Google DMA (Section 8)
> - **Deep links** — deferred deep links and app-open deep links (Section 9)
> - **Ad revenue (ILRD)** — impression-level revenue from ad networks (Section 10, paid feature)
> - **User identity & analytics** — customer user IDs, user profile data (Section 11)

Only implement the sections the developer requests. Do not add features they didn't ask for.

---

## Quick Context

Tenjin is a mobile attribution and analytics platform. The SDK tracks app installs, sessions, in-app purchases, ad revenue, and custom events. It integrates with Apple's ATT framework and SKAdNetwork for privacy-compliant attribution.

---

## 1. Installation

Detect which package manager the project uses and follow the corresponding method. Replace `<TENJIN_SDK_VERSION>` with the value from [Resolve the SDK Version](#resolve-the-sdk-version).

### CocoaPods

If the project has a `Podfile`, add the dependency to the app target:

```ruby
pod 'TenjinSDK', '~> <TENJIN_SDK_VERSION>'
```

Then run `pod install`. If `TenjinSDK` is already listed in `Podfile.lock` at an older version, run `pod update TenjinSDK` instead.

### Swift Package Manager

If the project uses SPM, add the Tenjin package:

```
https://github.com/tenjin/tenjin-ios-spm
```

In Xcode: File → Add Package Dependencies → paste the URL → "Up to Next Major Version" from `<TENJIN_SDK_VERSION>` → add the `TenjinSDK` product to the app target. Package dependencies of an `.xcodeproj` live in `project.pbxproj`; if you cannot edit that file safely, ask the developer to add the package in Xcode.

For a `Package.swift` manifest:

```swift
dependencies: [
    .package(url: "https://github.com/tenjin/tenjin-ios-spm", from: "<TENJIN_SDK_VERSION>")
]
```

### Importing the SDK

- **Swift, with CocoaPods or SPM:** `import TenjinSDK` in every file that uses it.
- **Objective-C:** `#import "TenjinSDK.h"`.
- **Swift, with the framework added by hand:** add `#import "TenjinSDK.h"` to the bridging header instead of `import TenjinSDK`.

---

## 2. Required Info.plist Configuration

Add these keys to `Info.plist` before writing any code:

```xml
<!-- Required for the ATT prompt (iOS 14+). The app crashes on the ATT request if this is missing. -->
<key>NSUserTrackingUsageDescription</key>
<string>We use this data to provide a better and personalized ad experience.</string>

<!-- Required for SKAdNetwork postbacks (iOS 15+) -->
<key>NSAdvertisingAttributionReportEndpoint</key>
<string>https://tenjin-skan.com</string>
```

If the project already has an `NSUserTrackingUsageDescription`, keep the developer's wording.

For Apple Search Ads attribution the SDK uses `AdServices.framework` (iOS 14.3+). CocoaPods links it automatically. Otherwise add it under Build Phases → Link Binary With Libraries and set it to **Optional**.

---

## 3. Core Initialization

### Where connect() Goes

- **On every launch and every return to the foreground**, not only on first open. Tenjin needs the session data, and accounts that only connect on first open may be suspended.
- **After the user has answered the tracking prompt.** Calling `connect()` before the ATT answer sends a zeroed IDFA and degrades attribution.
- **Do not request ATT from `didFinishLaunchingWithOptions`.** iOS shows the prompt only while the app is active; a request made earlier may not display. Request it when the app becomes active.
- **If the app already has a tracking prompt, hook into it. Do not add a second one.** Search the project for `requestTrackingAuthorization` first. A consent flow, an ads SDK or a CMP may already present it. See [Apps That Already Request Tracking](#apps-that-already-request-tracking).

So: create the SDK instance in `didFinishLaunchingWithOptions` (or the SwiftUI `App` initializer), and call `connect()` from the ATT completion handler each time the app becomes active. Once the user has answered, iOS calls the completion handler immediately without showing the prompt again, so this runs on every launch.

Calling `connect()` on every activation is safe: the SDK skips a `connect()` that comes within 30 seconds of the previous one.

### Swift (UIKit)

Works for both `AppDelegate`-only apps and apps with a `SceneDelegate`:

```swift
import UIKit
import AppTrackingTransparency
import TenjinSDK

@main
class AppDelegate: UIResponder, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {

        TenjinSDK.getInstance("<SDK_KEY>")

        NotificationCenter.default.addObserver(
            forName: UIApplication.didBecomeActiveNotification,
            object: nil,
            queue: .main
        ) { _ in
            self.requestTrackingAndConnect()
        }

        return true
    }

    private func requestTrackingAndConnect() {
        if #available(iOS 14, *) {
            ATTrackingManager.requestTrackingAuthorization { _ in
                TenjinSDK.connect()
            }
        } else {
            TenjinSDK.connect()
        }
    }
}
```

### Objective-C

```objectivec
#import "TenjinSDK.h"
#import <AppTrackingTransparency/AppTrackingTransparency.h>

@implementation AppDelegate

- (BOOL)application:(UIApplication *)application
    didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {

    [TenjinSDK initialize:@"<SDK_KEY>"];

    [[NSNotificationCenter defaultCenter] addObserverForName:UIApplicationDidBecomeActiveNotification
                                                      object:nil
                                                       queue:[NSOperationQueue mainQueue]
                                                  usingBlock:^(NSNotification *note) {
        [self requestTrackingAndConnect];
    }];

    return YES;
}

- (void)requestTrackingAndConnect {
    if (@available(iOS 14, *)) {
        [ATTrackingManager requestTrackingAuthorizationWithCompletionHandler:^(ATTrackingManagerAuthorizationStatus status) {
            [TenjinSDK connect];
        }];
    } else {
        [TenjinSDK connect];
    }
}

@end
```

### SwiftUI App Lifecycle

For apps using `@main` with the `App` protocol instead of an `AppDelegate`:

```swift
import SwiftUI
import AppTrackingTransparency
import TenjinSDK

@main
struct MyApp: App {
    init() {
        TenjinSDK.getInstance("<SDK_KEY>")
    }

    var body: some Scene {
        WindowGroup {
            ContentView()
                .onReceive(NotificationCenter.default.publisher(for: UIApplication.didBecomeActiveNotification)) { _ in
                    requestTrackingAndConnect()
                }
        }
    }

    private func requestTrackingAndConnect() {
        if #available(iOS 14, *) {
            ATTrackingManager.requestTrackingAuthorization { _ in
                TenjinSDK.connect()
            }
        } else {
            TenjinSDK.connect()
        }
    }
}
```

### Apps That Already Request Tracking

If the project already calls `requestTrackingAuthorization` somewhere (its own onboarding screen, a consent manager, an ads SDK wrapper), keep that single prompt:

1. Create the instance at launch as above.
2. In the **existing** completion handler, add `TenjinSDK.connect()`.
3. On every activation where the user has already answered, connect directly:

```swift
import AppTrackingTransparency
import TenjinSDK

func connectTenjinIfTrackingIsDecided() {
    if #available(iOS 14, *), ATTrackingManager.trackingAuthorizationStatus == .notDetermined {
        // The app's own prompt has not been answered yet.
        // Its completion handler calls TenjinSDK.connect().
        return
    }
    TenjinSDK.connect()
}
```

Call `connectTenjinIfTrackingIsDecided()` from the same did-become-active hook shown above.

### Different Keys per Configuration

If Debug and Release (or several targets) have different bundle IDs, each needs the key of its own Tenjin app. Select it at compile time instead of hardcoding one key:

```swift
#if DEBUG
let tenjinSDKKey = "<DEBUG_APP_SDK_KEY>"
#else
let tenjinSDKKey = "<SDK_KEY>"
#endif

TenjinSDK.getInstance(tenjinSDKKey)
```

---

## 4. Verify from the Device Log

Do this before adding any optional feature.

### Turn On Debug Logs

By default the SDK prints only its error messages. Requests and responses are printed only after `debugLogs()` has been called. Call it before `connect()`, in development builds only:

```swift
#if DEBUG
TenjinSDK.debugLogs()
#endif
```

```objectivec
#ifdef DEBUG
[TenjinSDK debugLogs];
#endif
```

### What to Look For

Every line the SDK prints starts with `[Tenjin]`. Run the app from Xcode and filter the console for `[Tenjin]`. A working integration prints, on launch:

```text
[Tenjin] - LOG: Connect request
[Tenjin] - LOG: Sending request - https://track.tenjin.com/...
[Tenjin] - DEBUG: request body ...
[Tenjin] - LOG: Got http response 200
[Tenjin] - DEBUG: Response body {"code":200,"success":true}
```

The line that decides is `Got http response <status>`. The iOS SDK treats any HTTP response as delivered and prints no error for a rejected request, so **read the status code**; do not conclude success from the absence of errors.

### What the Response Means

| `Got http response` | Response body | Meaning | What to do |
|---------------------|---------------|---------|------------|
| 200 | `"success":true` | Accepted | Nothing. The integration works |
| 401 | `unauthorized` | The SDK key is unknown, or it is not the key of this app | Use the key from this app's page in the dashboard (this platform, this bundle ID) |
| 404 | `no such app` | There is no Tenjin app for this bundle ID on iOS | Create the app in the dashboard with exactly this bundle ID, or fix the ID (check per-configuration suffixes) |
| 202 | `invalid device identifier` | The request carried no device identifier | Check that `optInParams` / `optOutParams` are not removing `developer_device_id` |
| 202 | `not logged` | The SDK key is disabled | Enable the key in the dashboard or use another key of the same app |
| 202 | `ignored` | The request was filtered by an app-version rule configured for the app | Check the app's version rules in the dashboard |

A 202 is **not** success: the request was received and dropped.

### No Request at All

- **`Connect sent 4.2s ago (interval: 30.0s), ignoring duplicate ping`**: a `connect()` within 30 seconds of the previous one is skipped and sends nothing. The timestamp is stored on the device, so it survives an app restart. Wait 30 seconds before relaunching, or delete the app and reinstall.
- **No `[Tenjin]` lines**: `debugLogs()` was not called before `connect()`, or `connect()` is not reached (for example the ATT completion handler never runs because the request was made before the app was active).

### In the Dashboard

After a 200 response, the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics) shows events for devices registered as test devices.

---

## 5. Purchase Event Tracking

### StoreKit 1 (Objective-C / Swift)

```objectivec
// After a successful purchase (SKPaymentTransactionStatePurchased)
NSURL *receiptURL = [[NSBundle mainBundle] appStoreReceiptURL];
NSData *receiptData = [NSData dataWithContentsOfURL:receiptURL];
[TenjinSDK transaction:transaction andReceipt:receiptData];
```

### StoreKit 2 (Swift only)

The signed (JWS) representation is a property of the `VerificationResult`, not of the `Transaction`:

```swift
import StoreKit
import TenjinSDK

@available(iOS 15.0, *)
func handlePurchase(_ result: VerificationResult<StoreKit.Transaction>, product: Product) async {
    switch result {
    case .verified(let transaction):
        TenjinSDK.transaction(
            withProductName: transaction.productID,
            andCurrencyCode: product.priceFormatStyle.currencyCode,
            andQuantity: transaction.purchasedQuantity,
            andUnitPrice: NSDecimalNumber(decimal: product.price),
            andTransactionId: String(transaction.id),
            andBase64Receipt: result.jwsRepresentation
        )

        await transaction.finish()

    case .unverified:
        break
    }
}
```

### Manual Revenue (No SKPaymentTransaction)

When not using Apple's transaction objects directly:

```objectivec
[TenjinSDK transactionWithProductName:@"premium_upgrade"
                       andCurrencyCode:@"USD"
                           andQuantity:1
                          andUnitPrice:[NSDecimalNumber decimalNumberWithString:@"9.99"]];
```

### Subscription IAP

Track subscription purchases for server-side verification and attribution.

```swift
// Pass StoreKit 2 transaction data manually
TenjinSDK.subscription(withProductName: "com.example.monthly",
                       andCurrencyCode: "USD",
                       andUnitPrice: NSDecimalNumber(string: "9.99"),
                       andTransactionId: "2000000123456789",
                       andOriginalTransactionId: "2000000123456789",
                       andBase64Receipt: "jws_or_base64_receipt",
                       andSKTransaction: "{\"id\": 2000000123456789, ...}")

// Or let the SDK fetch the StoreKit 2 transaction itself (iOS 16+).
// Recommended for IAP libraries that don't expose StoreKit 2 data (e.g. RevenueCat).
if #available(iOS 16.0, *) {
    TenjinSDK.subscriptionWithStoreKit(forProductId: "com.example.monthly",
                                       andCurrencyCode: "USD",
                                       andUnitPrice: NSDecimalNumber(string: "9.99"))
}
```

```objectivec
[TenjinSDK subscriptionWithProductName:@"com.example.monthly"
                       andCurrencyCode:@"USD"
                          andUnitPrice:[NSDecimalNumber decimalNumberWithString:@"9.99"]
                      andTransactionId:@"2000000123456789"
              andOriginalTransactionId:@"2000000123456789"
                      andBase64Receipt:@"jws_or_base64_receipt"
                      andSKTransaction:@"{\"id\": 2000000123456789, ...}"];

// iOS 16+ native StoreKit 2 fetch
if (@available(iOS 16.0, *)) {
    [TenjinSDK subscriptionWithStoreKitForProductId:@"com.example.monthly"
                                    andCurrencyCode:@"USD"
                                       andUnitPrice:[NSDecimalNumber decimalNumberWithString:@"9.99"]];
}
```

**Notes:**
- **Not automatic:** `connect()` does not capture subscriptions. One of these methods must be called from the purchase-handling code.
- All seven arguments of the manual method are required; the call is dropped if one is missing.
- Add your app's **App-Specific Shared Secret** in the [Tenjin dashboard](https://www.tenjin.com/dashboard/apps)
- Send **one transaction per billing interval** (at first charge and each renewal)
- Do **not** send transactions during free trial periods
- Tenjin does not de-duplicate transactions

---

## 6. Custom Events

> **Prerequisite:** `connect()` must have been called before sending any custom events.

```swift
// Event without value
TenjinSDK.sendEvent(withName: "level_complete")

// Event with integer value (used as count/sum)
TenjinSDK.sendEvent(withName: "coins_spent", andValue: 50)
```

```objectivec
[TenjinSDK sendEventWithName:@"level_complete"];
[TenjinSDK sendEventWithName:@"coins_spent" andValue:50];
```

**Limits:**
- Event names must be under **80 characters**
- Maximum **500 unique** event names per app

---

## 7. SKAdNetwork Conversion Values

```swift
// Basic (0-63)
TenjinSDK.updatePostbackConversionValue(5)

// With coarse value (iOS 16.1+ / SKAN 4.0)
TenjinSDK.updatePostbackConversionValue(5, coarseValue: "medium")

// With coarse value and lock window
TenjinSDK.updatePostbackConversionValue(5, coarseValue: "high", lockWindow: true)
```

```objectivec
[TenjinSDK updatePostbackConversionValue:5];
[TenjinSDK updatePostbackConversionValue:5 coarseValue:@"medium"];
[TenjinSDK updatePostbackConversionValue:5 coarseValue:@"high" lockWindow:YES];
```

Valid coarse values: `"low"`, `"medium"`, `"high"`

---

## 8. GDPR & Privacy Compliance

### Full Opt-In / Opt-Out

```objectivec
[TenjinSDK initialize:@"<SDK_KEY>"];

if (userConsented) {
    [TenjinSDK optIn];
} else {
    [TenjinSDK optOut];   // No API requests will be sent
}

[TenjinSDK connect];
```

### Granular Parameter Control

```objectivec
// Only send these specific parameters
NSArray *allowList = @[@"ip_address", @"advertising_id", @"developer_device_id", @"limit_ad_tracking"];
[TenjinSDK optInParams:allowList];

// Or send everything EXCEPT these parameters
NSArray *denyList = @[@"locale", @"timezone", @"build_id"];
[TenjinSDK optOutParams:denyList];
```

> **Required parameter:** `developer_device_id` must always be included for proper device tracking. Events missing this parameter will not be processed.

### CMP-Based Consent

Automatically opt in/out based on CMP consent (TCF purpose 1):

```objectivec
[TenjinSDK initialize:@"<SDK_KEY>"];
BOOL isOptedIn = [TenjinSDK optInOutUsingCMP];
```

### Google DMA Parameters

If you have a CMP integrated, Google DMA parameters are collected automatically. To override manually:

```objectivec
[[TenjinSDK sharedInstance] setGoogleDMAParametersWithAdPersonalization:YES adUserData:YES];

// Or toggle collection entirely
[TenjinSDK optInGoogleDMA];   // default
[TenjinSDK optOutGoogleDMA];
```

---

## 9. Deep Links

### Deferred Deep Links

To handle deep links from third-party services alongside Tenjin attribution:

```objectivec
[TenjinSDK initialize:@"<SDK_KEY>"];

NSURL *thirdPartyDeepLink = /* deep link from another service */;

if (thirdPartyDeepLink) {
    [TenjinSDK connectWithDeferredDeeplink:thirdPartyDeepLink];
} else {
    [TenjinSDK connect];
}
```

To register a deep link handler:

```swift
let instance: TenjinSDK = TenjinSDK.getInstance("<SDK_KEY>")
instance.registerDeepLinkHandler { params, error in
    if let error = error {
        print("Deep link error: \(error)")
        return
    }
    if let params = params {
        // Handle deep link parameters
    }
}
TenjinSDK.connect()
```

### App-Open Deep Link (Re-engagement)

Requires SDK **1.19.0 or newer**. Cold launches are captured automatically for apps that only use `UIApplicationDelegate`. Warm opens, and every launch of a scene-based app, must be reported by calling `handleOpenURL` wherever the app receives a URL:

```swift
// AppDelegate: custom scheme
func application(_ app: UIApplication, open url: URL,
                 options: [UIApplication.OpenURLOptionsKey: Any] = [:]) -> Bool {
    TenjinSDK.handleOpenURL(url)
    return true
}

// AppDelegate: Universal Link
func application(_ application: UIApplication, continue userActivity: NSUserActivity,
                 restorationHandler: @escaping ([UIUserActivityRestoring]?) -> Void) -> Bool {
    if let url = userActivity.webpageURL {
        TenjinSDK.handleOpenURL(url)
    }
    return true
}
```

In a `UISceneDelegate` app, call it from `scene(_:openURLContexts:)`, `scene(_:continue:)` and, for cold launches, from the `connectionOptions` in `scene(_:willConnectTo:options:)`.

---

## 10. Impression Level Ad Revenue (ILRD)

> **Note:** ILRD is a paid feature. Contact your Tenjin account manager before implementing.

The ILRD methods are visible from Swift (`import TenjinSDK`) with SDK 1.19.1 or newer. They can always be called from Objective-C.

### AppLovin

```swift
TenjinSDK.subscribeAppLovinImpressions()
```

### Unity LevelPlay (IronSource)

```swift
TenjinSDK.subscribeIronSourceImpressions()
```

### AdMob

Prefer the native method: it reads `GADAdValue` directly, so no unit conversion is needed.

```objectivec
// In your ad delegate callback
[TenjinSDK handleAdMobILRD:bannerView :adValue];
```

If you build the payload yourself (e.g. impression data arrives from elsewhere), use the JSON method.

> **Important:** despite its name, `value_micros` is **not** in micros on iOS. The iOS SDK reads it as
> currency units, which is what `GADAdValue.value` already returns (e.g. `0.012245` USD).
> Only divide by 1,000,000 if your value came from an API that reports micros, such as the Android,
> Unity, Flutter or React Native AdMob plugins. Sending raw micros here inflates ad revenue 1,000,000x.

```objectivec
NSString *json = @"{"
    "\"ad_unit_id\": \"ca-app-pub-xxx/yyy\","
    "\"value_micros\": 0.012245,"          // currency units, not micros
    "\"currency_code\": \"USD\","
    "\"precision_type\": \"3\","
    "\"response_id\": \"<RESPONSE_ID>\","
    "\"mediation_adapter_class_name\": \"GADMAdapterGoogleAdMobAds\""
"}";
[TenjinSDK adMobImpressionFromJSON:json];
```

### TopOn

```objectivec
[TenjinSDK topOnImpressionFromDict:adImpressionDictionary];
```

### HyperBid

```objectivec
[TenjinSDK hyperBidImpressionFromDict:adImpressionDictionary];
```

### CAS

```objectivec
[TenjinSDK subscribeCASBannerImpressions];
// or
[TenjinSDK handleCASILRD:adImpression];
```

### TradPlus

```objectivec
[TenjinSDK subscribeTradPlusImpressions];
// or
[TenjinSDK handleTradPlusILRD:adInfo];
```

### CloudX

```objectivec
[TenjinSDK handleCloudXILRD:adImpression];
```

### Any Other Mediation

```objectivec
// JSON with network_name, currency and revenue_decimal or revenue_cpm
[TenjinSDK customImpressionFromJSON:json];
```

---

## 11. User Identity & Analytics

### Customer User ID

```swift
TenjinSDK.setCustomerUserId("user_123")
let userId = TenjinSDK.getCustomerUserId()
```

### Analytics Installation ID

A locally generated persistent identifier (useful when IDFA is unavailable):

```swift
let analyticsId = TenjinSDK.getAnalyticsInstallationId()
```

### User Profile Data

The SDK automatically tracks sessions, IAP revenue, and ad revenue. Access the data programmatically:

```swift
// As a typed object (TJNUserProfileData)
if let profile = TenjinSDK.getUserProfile() {
    let sessions = profile.sessionCount
    let totalTime = profile.totalSessionTime           // milliseconds
    let iapCount = profile.iapTransactionCount
    let adRevenue = profile.totalILRDRevenueUSD
    let revenueByNetwork = profile.ilrdRevenueByNetwork // [String: NSNumber]
}

// As a dictionary (useful for serialization)
if let dict = TenjinSDK.getUserProfileAsDictionary() {
    // Keys: session_count, total_session_time, iap_transaction_count, etc.
}

// Reset all profile data
TenjinSDK.resetUserProfile()
```

---

## 12. Additional Configuration

### A/B Testing with App Subversion

```swift
TenjinSDK.getInstance("<SDK_KEY>")
TenjinSDK.appendAppSubversion(NSNumber(value: 8888))  // Reports as e.g. "1.0.1.8888"
TenjinSDK.connect()
```

### Event Caching (Offline Support)

Enable retry/cache for events when the device has no connectivity:

```swift
TenjinSDK.setCacheEventSetting(true)
```

The setting is stored on the device. Removing the call in a later release does not turn caching off; call `setCacheEventSetting(false)` to disable it.

---

## 13. Integration Checklist

When integrating Tenjin into an iOS project, verify these items:

- [ ] **SDK version** was resolved with the command in this guide, not from memory; no `<TENJIN_SDK_VERSION>` placeholder is left in a project file
- [ ] **Every Swift file** that uses the SDK has `import TenjinSDK` (or the bridging header imports `TenjinSDK.h`)
- [ ] **Info.plist** has `NSUserTrackingUsageDescription` with a user-facing message
- [ ] **Info.plist** has `NSAdvertisingAttributionReportEndpoint` set to `https://tenjin-skan.com`
- [ ] **AdServices.framework** is linked as Optional (automatic with CocoaPods)
- [ ] **The ATT prompt** is requested when the app is active, not in `didFinishLaunchingWithOptions`, and there is only one prompt in the app
- [ ] **`connect()`** is called from the ATT completion handler, on every launch
- [ ] **The SDK key** is the key of the iOS app whose bundle ID matches this build (check per-configuration bundle IDs); `<SDK_KEY>` is replaced
- [ ] **Custom events** are only sent after `connect()` has been called
- [ ] **The console** shows `[Tenjin] - LOG: Got http response 200` with debug logs on
- [ ] **Debug logs** are disabled in production builds
- [ ] Integration is verified using the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics)

---

## 14. Common Mistakes to Avoid

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Using an SDK version from memory | It is usually many releases old and lacks the APIs in this guide | Run the command in [Resolve the SDK Version](#resolve-the-sdk-version) |
| Using the Android app's SDK key, or one key for every bundle ID | The key must belong to the app with this platform and bundle ID; other keys get 401 | One key per Tenjin app; select it per configuration |
| Requesting ATT in `didFinishLaunchingWithOptions` | The prompt only shows while the app is active and may be skipped | Request it when the app becomes active |
| Adding a second ATT prompt | The app already asks elsewhere; iOS shows the prompt once | Call `connect()` from the existing completion handler |
| Calling `connect()` before the ATT answer | IDFA will be zeros, degrading attribution quality | Call `connect()` inside the ATT completion handler |
| Calling `connect()` only on first launch | Tenjin needs session data on every launch; accounts may be suspended | Connect on every activation |
| Missing `import TenjinSDK` in a Swift file | `Cannot find 'TenjinSDK' in scope` | Add the import (CocoaPods/SPM) or the bridging header (manual framework) |
| Concluding success because no error was logged | The SDK prints no error for a 401, 404 or 202 | Enable `debugLogs()` and read the `Got http response` line |
| Relaunching within 30 seconds while testing | The SDK skips the second `connect()` and sends nothing | Wait 30 seconds or reinstall the app |
| Sending events before `connect()` | Events will not be processed | Always call `connect()` first |
| Using deprecated `init:` methods | Will be removed in a future version | Use `initialize:` (ObjC) or `getInstance()` (Swift) |
| Reading `jwsRepresentation` from the `Transaction` | It does not exist there and does not compile | Read it from the `VerificationResult` |
| `let instance = TenjinSDK.getInstance(...)` then `instance.registerDeepLinkHandler` | The inferred type is `TenjinSDK?`, so the call does not compile | Annotate the type: `let instance: TenjinSDK = ...` |
| `TenjinSDK.subscription(withStoreKitForProductId:...)` | That is not the Swift name of the method | `TenjinSDK.subscriptionWithStoreKit(forProductId:andCurrencyCode:andUnitPrice:)` |
| Event names over 80 characters | Will be rejected | Keep event names concise |
| Exceeding 500 unique event names | Additional events will be dropped | Reuse event names with different values |
| Dividing AdMob `value_micros` by 1,000,000 before sending | iOS expects currency units, which `GADAdValue.value` already returns; dividing reports 1,000,000x too little | Send `GADAdValue.value` as-is, or use `handleAdMobILRD:` |
| Sending subscription transactions during trial | Inflates revenue metrics | Only send at first charge and renewals |
| Missing `developer_device_id` in opt-in params | Events will not be processed | Always include `developer_device_id` in `optInParams` |

---

## 15. Full API Reference

Objective-C selectors of `TenjinSDK`. All are class methods unless marked (instance).

### Initialization

| Method | Purpose |
|--------|---------|
| `getInstance:` | Create or return the singleton; preferred from Swift (`TenjinSDK.getInstance("<KEY>")`) |
| `initialize:` | Create or return the singleton; preferred from Objective-C |
| `sharedInstance` | Return the existing singleton |
| `connect` | Send install/session data to Tenjin |
| `connectWithDeferredDeeplink:` | Connect with a third-party deep link |

### Events & Revenue

| Method | Purpose |
|--------|---------|
| `sendEventWithName:` | Custom event (name only) |
| `sendEventWithName:andValue:` | Custom event with integer value |
| `transaction:andReceipt:` | StoreKit 1 purchase |
| `transactionWithProductName:andCurrencyCode:andQuantity:andUnitPrice:` | Manual revenue |
| `transactionWithProductName:andCurrencyCode:andQuantity:andUnitPrice:andTransactionId:andBase64Receipt:` | StoreKit 2 purchase |
| `subscriptionWithProductName:andCurrencyCode:andUnitPrice:andTransactionId:andOriginalTransactionId:andBase64Receipt:andSKTransaction:` | Subscription tracking with full transaction data |
| `subscriptionWithStoreKitForProductId:andCurrencyCode:andUnitPrice:` | Native StoreKit 2 subscription fetch (iOS 16+) |
| `updatePostbackConversionValue:` | SKAdNetwork conversion value |
| `updatePostbackConversionValue:coarseValue:` | With coarse value (iOS 16.1+) |
| `updatePostbackConversionValue:coarseValue:lockWindow:` | With coarse value and lock window |

### Deep Links & Attribution

| Method | Purpose |
|--------|---------|
| `registerDeepLinkHandler:` (instance) | Deferred deep link / attribution callback |
| `handleOpenURL:` | Report an app-open deep link |
| `getAttributionInfo:` (instance) | Attribution data (paid feature) |

### Privacy & Consent

| Method | Purpose |
|--------|---------|
| `optIn` / `optOut` | GDPR full opt-in/out |
| `optInParams:` / `optOutParams:` | Granular parameter control |
| `optInOutUsingCMP` | Automatic CMP-based consent |
| `optInGoogleDMA` / `optOutGoogleDMA` | Google DMA parameter control |
| `setGoogleDMAParametersWithAdPersonalization:adUserData:` (instance) | Set Google DMA consent flags |

### Identity & Analytics

| Method | Purpose |
|--------|---------|
| `setCustomerUserId:` | Set custom user identifier |
| `getCustomerUserId` | Retrieve stored user ID |
| `getAnalyticsInstallationId` | Get persistent local analytics ID |
| `getUserProfile` | Get user metrics as typed object |
| `getUserProfileAsDictionary` | Get user metrics as dictionary |
| `resetUserProfile` | Clear all local profile data |

### Configuration

| Method | Purpose |
|--------|---------|
| `appendAppSubversion:` | A/B test variant tracking |
| `setCacheEventSetting:` | Enable offline event caching |
| `setEncryptRequestsSetting:` | Enable request encryption |
| `debugLogs` | Print requests and responses to the console |

---

## 16. How to Use This Document

**With any LLM:**

```
Add Tenjin to my iOS app using this guide:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/ios/llm-guide.md
```

**Keeping this document up to date:**

This guide is derived from the official [README.md](https://github.com/tenjin/tenjin-ios-sdk/blob/master/README.md) and the public API header [TenjinSDK.h](https://github.com/tenjin/tenjin-ios-sdk/blob/master/TenjinSDK.h). When the SDK is updated, review those sources and update this file accordingly.
