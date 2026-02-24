# Tenjin iOS SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin iOS SDK into an iOS project without requiring external documentation lookups.
>
> **Minimum iOS:** 14.0+ | **Minimum Xcode:** 13
>
> **Sources:**
> - Repository: [github.com/tenjin/tenjin-ios-sdk](https://github.com/tenjin/tenjin-ios-sdk)
> - Full README: [README.md](https://github.com/tenjin/tenjin-ios-sdk/blob/master/README.md)
> - Public API header: [TenjinSDK.h](https://github.com/tenjin/tenjin-ios-sdk/blob/master/TenjinSDK.h)
> - SPM package: [tenjin-ios-spm](https://github.com/tenjin/tenjin-ios-spm)
> - Release notes: [RELEASE_NOTES.md](https://github.com/tenjin/tenjin-ios-sdk/blob/master/RELEASE_NOTES.md)
>
> **Important:** Always check the [latest release](https://github.com/tenjin/tenjin-ios-sdk/releases) before integrating. Do not use hardcoded version numbers from this document — fetch the current version from GitHub or CocoaPods.

---

## Before You Begin

### Check the Latest SDK Version

Before writing any integration code:

1. **Fetch the latest version** from [GitHub Releases](https://github.com/tenjin/tenjin-ios-sdk/releases) or [CocoaPods](https://cocoapods.org/pods/TenjinSDK)
2. **Use that version** in all Podfile or Package.swift declarations
3. **Do not hardcode** version numbers from this document — they may be outdated

### Get the SDK Key

**Ask the developer for their Tenjin SDK key.** Every code example in this document uses `<SDK_KEY>` as a placeholder. Before writing any integration code, prompt the user:

> "What is your Tenjin SDK key? You can find it in the [Tenjin dashboard](https://www.tenjin.io/dashboard/organizations) on your app's page. Each app has up to 3 unique keys. If you don't have it handy, I can use a placeholder and you can fill it in later — just search your project for `TENJIN_SDK_KEY_PLACEHOLDER` to find it."

If the developer provides their key, substitute it directly in all generated code. If they prefer to add it later, use the literal string `TENJIN_SDK_KEY_PLACEHOLDER` (not `<SDK_KEY>`) so it is easy to find with a project-wide search.

## Integration Workflow

Follow this two-step approach:

1. **First, integrate the basics.** Complete sections 1–3 (Installation, Info.plist, Core Initialization). This gives the developer install tracking, session tracking, and ATT support — the foundation every Tenjin integration needs.

2. **Then, ask what else they need.** After the basic integration is working, prompt the user:

> "Tenjin basic integration is done (install tracking + ATT). Would you like to add any of these features?"
> - **Purchase tracking** — StoreKit 1 or StoreKit 2 IAP (Section 4)
> - **Custom events** — track in-app actions like level completions or signups (Section 5)
> - **SKAdNetwork conversion values** — for SKAN attribution (Section 6)
> - **GDPR / consent management** — opt-in/out, CMP, Google DMA (Section 7)
> - **Deferred deep links** — handle attribution deep links (Section 8)
> - **Ad revenue (ILRD)** — impression-level revenue from ad networks (Section 9, paid feature)
> - **User identity & analytics** — customer user IDs, user profile data (Section 10)

Only implement the sections the developer requests. Do not add features they didn't ask for.

---

## Quick Context

Tenjin is a mobile attribution and analytics platform. The SDK tracks app installs, sessions, in-app purchases, ad revenue, and custom events. It integrates with Apple's ATT framework and SKAdNetwork for privacy-compliant attribution.

---

## 1. Installation

Detect which package manager the project uses and follow the corresponding method.

### CocoaPods

If the project has a `Podfile`, add the dependency and install:

```ruby
pod 'TenjinSDK'
```

Then run `pod install`.

### Swift Package Manager

If the project uses SPM (check for `Package.swift` or `.xcodeproj` with package dependencies), add the Tenjin SPM repository:

```
https://github.com/tenjin/tenjin-ios-spm
```

---

## 2. Required Info.plist Configuration

Add these keys to `Info.plist` before writing any code:

```xml
<!-- Required for ATT prompt (iOS 14+) -->
<key>NSUserTrackingUsageDescription</key>
<string>We use this data to provide a better and personalized ad experience.</string>

<!-- Required for SKAdNetwork postbacks (iOS 15+) -->
<key>NSAdvertisingAttributionReportEndpoint</key>
<string>https://tenjin-skan.com</string>
```

Also add the `AdServices.framework` (iOS 14.3+) for Apple Search Ads Attribution support:
- Build Phases → Link Binary With Libraries → Add `AdServices.framework` (set to Optional)

---

## 3. Core Initialization

### Best Practice: Always Call connect() from the ATT Callback

On iOS 14+, Apple requires the ATT prompt before accessing the IDFA. The **recommended** pattern is to call `connect()` inside the ATT completion handler. This ensures Tenjin receives the IDFA when the user grants permission, resulting in better attribution accuracy.

> **Critical:** `initialize` + `connect` must run on **every** app launch inside `didFinishLaunchingWithOptions` (or the SwiftUI equivalent), not just the first launch. Tenjin may suspend accounts that only call connect on first open.

### Swift (Recommended Pattern)

```swift
import AppTrackingTransparency
import TenjinSDK

class AppDelegate: UIResponder, UIApplicationDelegate {
    func application(
        _ application: UIApplication,
        didFinishLaunchingWithOptions launchOptions: [UIApplication.LaunchOptionsKey: Any]?
    ) -> Bool {

        TenjinSDK.getInstance("<SDK_KEY>")

        if #available(iOS 14, *) {
            ATTrackingManager.requestTrackingAuthorization { _ in
                TenjinSDK.connect()
            }
        } else {
            TenjinSDK.connect()
        }

        return true
    }
}
```

### Objective-C (Recommended Pattern)

```objectivec
#import "TenjinSDK.h"
#import <AppTrackingTransparency/AppTrackingTransparency.h>

@implementation AppDelegate

- (BOOL)application:(UIApplication *)application
    didFinishLaunchingWithOptions:(NSDictionary *)launchOptions {

    [TenjinSDK initialize:@"<SDK_KEY>"];

    if (@available(iOS 14, *)) {
        [ATTrackingManager requestTrackingAuthorizationWithCompletionHandler:^(ATTrackingManagerAuthorizationStatus status) {
            [TenjinSDK connect];
        }];
    } else {
        [TenjinSDK connect];
    }

    return YES;
}

@end
```

### SwiftUI App Lifecycle

For apps using `@main` with `App` protocol instead of `AppDelegate`:

```swift
import SwiftUI
import AppTrackingTransparency

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

> **Note on ATT timing:** The ATT prompt can only be displayed when the app is in the `.active` state. In SwiftUI, use `didBecomeActiveNotification` to ensure the prompt appears at the right time. Calling it too early (e.g., in `init()`) will silently fail.

### Enable Debug Logging (Development Only)

```swift
TenjinSDK.debugLogs()  // Call before connect() — remove for production builds
```

```objectivec
[TenjinSDK debugLogs];
```

---

## 4. Purchase Event Tracking

### StoreKit 1 (Objective-C / Swift)

```objectivec
// After a successful purchase (SKPaymentTransactionStatePurchased)
NSURL *receiptURL = [[NSBundle mainBundle] appStoreReceiptURL];
NSData *receiptData = [NSData dataWithContentsOfURL:receiptURL];
[TenjinSDK transaction:transaction andReceipt:receiptData];
```

### StoreKit 2 (Swift only)

```swift
func handlePurchase(_ result: VerificationResult<Transaction>) async {
    switch result {
    case .verified(let transaction):
        let jwsRepresentation = transaction.jwsRepresentation

        TenjinSDK.transaction(
            withProductName: transaction.productID,
            andCurrencyCode: transaction.currency?.identifier ?? "USD",
            andQuantity: transaction.purchasedQuantity,
            andUnitPrice: NSDecimalNumber(decimal: transaction.price ?? Decimal(0)),
            andTransactionId: String(transaction.id),
            andBase64Receipt: jwsRepresentation
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

- Add your app's **App-Specific Shared Secret** in the [Tenjin dashboard](https://www.tenjin.io/dashboard/apps)
- Send **one transaction per billing interval** (at first charge and each renewal)
- Do **not** send transactions during free trial periods
- Tenjin does not de-duplicate transactions

---

## 5. Custom Events

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

## 6. SKAdNetwork Conversion Values

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

## 7. GDPR & Privacy Compliance

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

## 8. Deferred Deep Links

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
let instance = TenjinSDK.getInstance("<SDK_KEY>")
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

---

## 9. Impression Level Ad Revenue (ILRD)

> **Note:** ILRD is a paid feature. Contact your Tenjin account manager before implementing.

### AppLovin

```swift
TenjinSDK.subscribeAppLovinImpressions()
```

### Unity LevelPlay (IronSource)

```swift
TenjinSDK.subscribeIronSourceImpressions()
```

### AdMob

```objectivec
// In your ad delegate callback
[TenjinSDK handleAdMobILRD:bannerView :adValue];
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

---

## 10. User Identity & Analytics

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
// As a typed object
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

## 11. Additional Configuration

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

---

## 12. Integration Checklist

When integrating Tenjin into an iOS project, verify these items:

- [ ] **SDK version** is the latest from [GitHub Releases](https://github.com/tenjin/tenjin-ios-sdk/releases)
- [ ] **Info.plist** has `NSUserTrackingUsageDescription` with a user-facing message
- [ ] **Info.plist** has `NSAdvertisingAttributionReportEndpoint` set to `https://tenjin-skan.com`
- [ ] **AdServices.framework** is linked (set to Optional)
- [ ] **ATT prompt** is requested before calling `connect()` on iOS 14+
- [ ] **`connect()`** is called on every app launch, not just first launch
- [ ] **`connect()`** is called from within the ATT completion handler (best practice)
- [ ] **Custom events** are only sent after `connect()` has been called
- [ ] **Debug logs** are enabled during development and disabled in production
- [ ] **`<SDK_KEY>`** placeholder is replaced with the actual key from the Tenjin dashboard
- [ ] Integration is verified using the [Live Test Device Data Tool](https://www.tenjin.io/dashboard/sdk_diagnostics)

---

## 13. Common Mistakes to Avoid

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Calling `connect()` only on first launch | Tenjin needs session data on every launch; accounts may be suspended | Move `connect()` to `didFinishLaunchingWithOptions` unconditionally |
| Calling `connect()` before ATT prompt | IDFA will be zeros, degrading attribution quality | Wrap `connect()` inside the ATT completion handler |
| Sending events before `connect()` | Events will not be processed | Always call `connect()` first |
| Using deprecated `init:` methods | Will be removed in a future version | Use `initialize:` (ObjC) or `getInstance()` (Swift) |
| Event names over 80 characters | Will be rejected | Keep event names concise |
| Exceeding 500 unique event names | Additional events will be dropped | Reuse event names with different values |
| Sending subscription transactions during trial | Inflates revenue metrics | Only send at first charge and renewals |
| Missing `developer_device_id` in opt-in params | Events will not be processed | Always include `developer_device_id` in `optInParams` |

---

## 14. Full API Reference

### Initialization

| Method | Language | Notes |
|--------|----------|-------|
| `TenjinSDK.getInstance("<KEY>")` | Swift | Returns singleton, preferred for Swift |
| `[TenjinSDK initialize:@"<KEY>"]` | ObjC | Preferred for Objective-C |
| `TenjinSDK.connect()` | Both | Sends install/session data to Tenjin |
| `TenjinSDK.connectWithDeferredDeeplink(url)` | Both | Connect with third-party deep link |

### Events & Revenue

| Method | Purpose |
|--------|---------|
| `sendEventWithName(_:)` | Custom event (name only) |
| `sendEventWithName(_:andValue:)` | Custom event with integer value |
| `transaction(_:andReceipt:)` | StoreKit 1 purchase |
| `transactionWithProductName(...)` | Manual revenue or StoreKit 2 |
| `updatePostbackConversionValue(_:)` | SKAdNetwork conversion value |

### Privacy & Consent

| Method | Purpose |
|--------|---------|
| `optIn()` / `optOut()` | GDPR full opt-in/out |
| `optInParams(_:)` / `optOutParams(_:)` | Granular parameter control |
| `optInOutUsingCMP()` | Automatic CMP-based consent |
| `optInGoogleDMA()` / `optOutGoogleDMA()` | Google DMA parameter control |

### Identity & Analytics

| Method | Purpose |
|--------|---------|
| `setCustomerUserId(_:)` | Set custom user identifier |
| `getCustomerUserId()` | Retrieve stored user ID |
| `getAnalyticsInstallationId()` | Get persistent local analytics ID |
| `getUserProfile()` | Get user metrics as typed object |
| `getUserProfileAsDictionary()` | Get user metrics as dictionary |
| `resetUserProfile()` | Clear all local profile data |

### Configuration

| Method | Purpose |
|--------|---------|
| `appendAppSubversion(_:)` | A/B test variant tracking |
| `setCacheEventSetting(_:)` | Enable offline event caching |
| `debugLogs()` | Enable verbose debug output |

---

## 15. How to Use This Document

**With any LLM:**

```
Add Tenjin to my iOS app using this guide:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/ios/llm-guide.md
```

**Keeping this document up to date:**

This guide is derived from the official [README.md](https://github.com/tenjin/tenjin-ios-sdk/blob/master/README.md) and the public API header [TenjinSDK.h](https://github.com/tenjin/tenjin-ios-sdk/blob/master/TenjinSDK.h). When the SDK is updated, review those sources and update this file accordingly.
