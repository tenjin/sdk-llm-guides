# Tenjin Ionic SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin Ionic SDK (Capacitor plugin) into an Ionic project without requiring external documentation lookups.
>
> **Requirements:** Capacitor >= 4.0.0 | iOS 13.0+ | Android API 22+
>
> **Sources:**
> - Repository: [github.com/tenjin/tenjin-ionic-sdk](https://github.com/tenjin/tenjin-ionic-sdk)
> - Full README: [README.md](https://github.com/tenjin/tenjin-ionic-sdk/blob/main/README.md)
> - npm: [ionic-capacitor-tenjin](https://www.npmjs.com/package/ionic-capacitor-tenjin)
>
> **Important:** Always check the [latest release](https://www.npmjs.com/package/ionic-capacitor-tenjin) before integrating. Do not use hardcoded version numbers from this document — fetch the current version from npm.

---

## Before You Begin

### Check the Latest SDK Version

Before writing any integration code:

1. **Fetch the latest version** from [npm](https://www.npmjs.com/package/ionic-capacitor-tenjin)
2. **Use that version** in your `package.json` declaration
3. **Do not hardcode** version numbers from this document — they may be outdated

### Get the SDK Key

**Ask the developer for their Tenjin SDK key.** Every code example in this document uses `<SDK_KEY>` as a placeholder. Before writing any integration code, prompt the user:

> "What is your Tenjin SDK key? You can find it in the [Tenjin dashboard](https://www.tenjin.io/dashboard/organizations) on your app's page. Each app has up to 3 unique keys. If you don't have it handy, I can use a placeholder and you can fill it in later — just search your project for `TENJIN_SDK_KEY_PLACEHOLDER` to find it."

If the developer provides their key, substitute it directly in all generated code. If they prefer to add it later, use the literal string `TENJIN_SDK_KEY_PLACEHOLDER` so it is easy to find with a project-wide search.

## Integration Workflow

Follow this two-step approach:

1. **First, integrate the basics.** Complete sections 1–4 (Installation, iOS Setup, Android Setup, Core Initialization). This gives the developer install tracking and session tracking — the foundation every Tenjin integration needs.

2. **Then, ask what else they need.** After the basic integration is working, prompt the user:

> "Tenjin basic integration is done (install tracking). Would you like to add any of these features?"
> - **Purchase tracking** — track in-app purchases (Section 5)
> - **Custom events** — track in-app actions like level completions or signups (Section 6)
> - **SKAdNetwork conversion values** — for SKAN attribution on iOS (Section 7)
> - **GDPR / consent management** — opt-in/out, CMP, Google DMA (Section 8)
> - **Ad revenue (ILRD)** — impression-level revenue from ad networks (Section 9, paid feature)
> - **User identity & analytics** — customer user IDs, analytics IDs, user profiles (Section 10)

Only implement the sections the developer requests. Do not add features they didn't ask for.

---

## Quick Context

Tenjin is a mobile attribution and analytics platform. The SDK tracks app installs, sessions, in-app purchases, ad revenue, and custom events. This Ionic SDK is a **Capacitor plugin** that bridges to the native Tenjin SDKs on iOS and Android.

> **Note:** This is a Capacitor plugin, not a Cordova plugin. It requires Capacitor 4.0.0 or higher.

---

## 1. Installation

Install the package and sync with Capacitor:

```bash
npm install ionic-capacitor-tenjin
npx cap sync
```

---

## 2. iOS Platform Setup

### Info.plist Configuration

Add these keys to `ios/App/App/Info.plist`:

```xml
<!-- Required for ATT prompt (iOS 14+) -->
<key>NSUserTrackingUsageDescription</key>
<string>We use this data to provide a better and personalized ad experience.</string>

<!-- Required for SKAdNetwork postbacks (iOS 15+) -->
<key>NSAdvertisingAttributionReportEndpoint</key>
<string>https://tenjin-skan.com</string>
```

### Minimum iOS Version

The plugin requires iOS 13.0+. Ensure your `ios/App/Podfile` has:

```ruby
platform :ios, '13.0'
```

After adding the plugin, run:

```bash
cd ios/App && pod install
```

---

## 3. Android Platform Setup

### Minimum SDK Version

The plugin requires Android API 22+. Ensure your `android/variables.gradle` has:

```gradle
ext {
    minSdkVersion = 22
    // ...
}
```

### Permissions

The Capacitor framework handles most permissions automatically. If needed, verify these are in `android/app/src/main/AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

<!-- Required for Android 13+ (API 33) -->
<uses-permission android:name="com.google.android.gms.permission.AD_ID" />
```

---

## 4. Core Initialization

### Import and Initialize

```typescript
import { Tenjin } from 'ionic-capacitor-tenjin';

// Initialize with your SDK key
await Tenjin.initialize({ sdkKey: '<SDK_KEY>' });

// Connect to Tenjin (call on every app launch)
await Tenjin.connect();
```

### Recommended Implementation

Create a service to manage Tenjin initialization:

```typescript
import { Injectable } from '@angular/core';
import { Tenjin } from 'ionic-capacitor-tenjin';
import { Platform } from '@ionic/angular';

@Injectable({
  providedIn: 'root'
})
export class TenjinService {

  constructor(private platform: Platform) {}

  async initialize(): Promise<void> {
    await this.platform.ready();

    // Initialize SDK
    await Tenjin.initialize({ sdkKey: '<SDK_KEY>' });

    // Connect on every app launch
    await Tenjin.connect();
  }
}
```

### Using in Your App

Call initialization early in your app lifecycle (e.g., in `app.component.ts`):

```typescript
import { Component } from '@angular/core';
import { TenjinService } from './services/tenjin.service';

@Component({
  selector: 'app-root',
  templateUrl: 'app.component.html'
})
export class AppComponent {

  constructor(private tenjinService: TenjinService) {
    this.initializeApp();
  }

  async initializeApp() {
    await this.tenjinService.initialize();
  }
}
```

> **Critical:** `connect()` must run on **every** app launch, not just the first launch. Tenjin may suspend accounts that only call connect on first open.

---

## 5. Purchase Event Tracking

Track in-app purchases with product details:

```typescript
await Tenjin.transaction({
  productName: 'premium_upgrade',
  currencyCode: 'USD',
  quantity: 1,
  unitPrice: 9.99
});
```

**Notes:**
- Add your **App-Specific Shared Secret** (iOS) or **Base64-encoded RSA public key** (Android) in the Tenjin dashboard for receipt validation
- Send **one transaction per billing interval** for subscriptions (at first charge and each renewal)
- Do **not** send transactions during free trial periods

---

## 6. Custom Events

> **Prerequisite:** `connect()` must have been called before sending any custom events.

```typescript
// Event without value
await Tenjin.eventWithName({ name: 'level_complete' });

// Event with value (value is a string)
await Tenjin.eventWithNameAndValue({ name: 'coins_spent', value: '50' });
```

**Limits:**
- Event names must be under **80 characters**
- Maximum **500 unique** event names per app

---

## 7. SKAdNetwork Conversion Values (iOS Only)

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

## 8. GDPR & Privacy Compliance

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

> **Required parameter:** `developer_device_id` must always be included for proper device tracking. Events missing this parameter will not be processed.

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

## 9. Impression Level Ad Revenue (ILRD)

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

```typescript
await Tenjin.eventAdImpressionAdMob({
  json: {
    ad_unit_id: 'ca-app-pub-xxx/yyy',
    value_micros: 10000,
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

## 10. User Identity & Analytics

### Customer User ID

```typescript
// Set custom user identifier
await Tenjin.setCustomerUserId({ userId: 'user_123' });

// Retrieve stored user ID
const result = await Tenjin.getCustomerUserId();
// result contains { userId: string }
```

### Analytics Installation ID

A locally generated persistent identifier (useful when IDFA/AAID is unavailable):

```typescript
const analyticsId = await Tenjin.getAnalyticsInstallationId();
// Returns string | null
```

### Attribution Info

> **Note:** This is a paid feature.

```typescript
const attributionInfo = await Tenjin.getAttributionInfo();
// Returns JSONObject with attribution data
```

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

## 11. Additional Configuration

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

### Request Encryption

Enable encryption for SDK requests:

```typescript
await Tenjin.setEncryptRequestsSetting({ setting: true });
```

---

## 12. Integration Checklist

When integrating Tenjin into an Ionic Capacitor project, verify these items:

- [ ] **SDK version** is the latest from [npm](https://www.npmjs.com/package/ionic-capacitor-tenjin)
- [ ] **Capacitor** is version 4.0.0 or higher
- [ ] **iOS Info.plist** has `NSUserTrackingUsageDescription` with a user-facing message
- [ ] **iOS Info.plist** has `NSAdvertisingAttributionReportEndpoint` set to `https://tenjin-skan.com`
- [ ] **iOS minimum version** is 13.0 or higher in Podfile
- [ ] **Android minimum SDK** is 22 or higher
- [ ] **Android Manifest** has `AD_ID` permission for Android 13+
- [ ] **`npx cap sync`** was run after installing the plugin
- [ ] **`connect()`** is called on every app launch, not just first launch
- [ ] **Custom events** are only sent after `connect()` has been called
- [ ] **`<SDK_KEY>`** placeholder is replaced with the actual key from the Tenjin dashboard
- [ ] Integration is verified using the [Live Test Device Data Tool](https://www.tenjin.io/dashboard/sdk_diagnostics)

---

## 13. Common Mistakes to Avoid

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Calling `connect()` only on first launch | Tenjin needs session data on every launch; accounts may be suspended | Call `connect()` in your app initialization on every launch |
| Forgetting `npx cap sync` | Plugin won't be registered with native platforms | Run `npx cap sync` after installing |
| Using Cordova instead of Capacitor | This is a Capacitor-only plugin | Ensure project uses Capacitor 4.0.0+ |
| Sending events before `connect()` | Events will not be processed | Always call `connect()` first |
| Missing `AD_ID` permission on Android 13+ | Cannot access AAID, degrades attribution quality | Add the permission to AndroidManifest.xml |
| Event names over 80 characters | Will be rejected | Keep event names concise |
| Exceeding 500 unique event names | Additional events will be dropped | Reuse event names with different values |
| Using SKAN methods on Android | They do nothing on Android | Check platform before calling |
| Missing `developer_device_id` in opt-in params | Events will not be processed | Always include `developer_device_id` in `optInParams` |

---

## 14. Full API Reference

### Initialization

| Method | Purpose |
|--------|---------|
| `initialize({ sdkKey })` | Initialize SDK with API key |
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
| `getUserProfileDictionary()` | Get user metrics as dictionary |
| `resetUserProfile()` | Clear all local profile data |

### Configuration

| Method | Purpose |
|--------|---------|
| `appendAppSubversion({ version })` | A/B test variant tracking |
| `setCacheEventSetting({ setting })` | Enable offline event caching |
| `setEncryptRequestsSetting({ setting })` | Enable request encryption |

---

## 15. How to Use This Document

**With any LLM:**

```
Add Tenjin to my Ionic app using this guide:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/ionic/llm-guide.md
```

**Keeping this document up to date:**

This guide is derived from the official [README.md](https://github.com/tenjin/tenjin-ionic-sdk/blob/main/README.md) and the TypeScript definitions in [definitions.ts](https://github.com/tenjin/tenjin-ionic-sdk/blob/main/src/definitions.ts). When the SDK is updated, review those sources and update this file accordingly.
