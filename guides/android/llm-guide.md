# Tenjin Android SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin Android SDK into an Android project without requiring external documentation lookups.
>
> **Minimum SDK:** 16 (Android 4.1+) | **Latest SDK:** 1.15.4 (as of Feb 2026)
>
> **Sources:**
> - Repository: [github.com/tenjin/tenjin-android-sdk](https://github.com/tenjin/tenjin-android-sdk)
> - Full README: [README.md](https://github.com/tenjin/tenjin-android-sdk/blob/master/README.md)
> - Release notes: [RELEASE_NOTES.md](https://github.com/tenjin/tenjin-android-sdk/blob/master/RELEASE_NOTES.md)
>
> **Important:** Always check for the [latest release](https://github.com/tenjin/tenjin-android-sdk/releases) before integrating. Fetch the current version from Maven Central.

---

## Before You Begin

### Check the Latest SDK Version

Before writing any integration code:

1. **Fetch the latest version** from [Maven Central](https://search.maven.org/search?q=g:com.tenjin%20AND%20a:android-sdk) or [GitHub Releases](https://github.com/tenjin/tenjin-android-sdk/releases).
2. **Use that version** in your `build.gradle` declaration.
3. **Do not hardcode** version numbers from this document — they may be outdated.

### Get the SDK Key

**Ask the developer for their Tenjin SDK key.** Every code example in this document uses `<SDK_KEY>` as a placeholder. Before writing any integration code, prompt the user:

> "What is your Tenjin SDK key? You can find it in the [Tenjin dashboard](https://www.tenjin.io/dashboard/organizations) on your app's page. Each app has up to 3 unique keys. If you don't have it handy, I can use a placeholder and you can fill it in later — just search your project for `TENJIN_SDK_KEY_PLACEHOLDER` to find it."

If the developer provides their key, substitute it directly in all generated code. If they prefer to add it later, use the literal string `TENJIN_SDK_KEY_PLACEHOLDER` so it is easy to find with a project-wide search.

## Integration Workflow

Follow this two-step approach:

1. **First, integrate the basics.** Complete sections 1–3 (Installation, AndroidManifest, Core Initialization). This gives the developer install tracking, session tracking, and attribution support — the foundation every Tenjin integration needs.

2. **Then, ask what else they need.** After the basic integration is working, prompt the user:

> "Tenjin basic integration is done (install tracking). Would you like to add any of these features?"
> - **Purchase tracking** — Google Play or Amazon IAP (Section 4)
> - **Custom events** — track in-app actions like level completions or signups (Section 5)
> - **GDPR / consent management** — opt-in/out, CMP, Google DMA (Section 6)
> - **Deep linking** — handle attribution deep links (Section 7)
> - **Ad revenue (ILRD)** — impression-level revenue from ad networks (Section 8, paid feature)
> - **User identity & analytics** — customer user IDs, user profile data (Section 9)

Only implement the sections the developer requests. Do not add features they didn't ask for.

---

## Quick Context

Tenjin is a mobile attribution and analytics platform. The SDK tracks app installs, sessions, in-app purchases, ad revenue, and custom events. It supports major Android app stores including Google Play and Amazon.

---

## 1. Installation

Detect which build system the project uses and follow the corresponding method.

### Gradle (Recommended)

In your app-level `build.gradle`, add the dependency:

```gradle
dependencies {
    implementation 'com.tenjin:android-sdk:1.15.4' // Check for latest
    
    // Required for Advertising ID (AAID)
    implementation 'com.google.android.gms:play-services-ads-identifier:18.0.1'
    
    // Required for AppSetID (Android 12+)
    implementation 'com.google.android.gms:play-services-appset:16.0.2'
    
    // Required for Google Play Install Referrer
    implementation 'com.android.installreferrer:installreferrer:2.2'
}
```

Ensure `mavenCentral()` is in your project-level `repositories` block.

### Manual Integration

Download `tenjin.aar` from the repository and place it in the `libs/` folder. Add it to `build.gradle`:

```gradle
dependencies {
    implementation fileTree(dir: 'libs', include: ['*.aar'])
    implementation files('libs/tenjin.aar')
}
```

---

## 2. Required AndroidManifest.xml Configuration

### Permissions

Add these to your `AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

<!-- Required for Android 13+ (API 33) -->
<uses-permission android:name="com.google.android.gms.permission.AD_ID" />
```

### App Store Meta-Data

Specify the target app store inside the `<application>` tag:

```xml
<application>
    <!-- Possible values: googleplay, amazon, other -->
    <meta-data android:name="TENJIN_APP_STORE" android:value="googleplay" />
</application>
```

### Meta Install Referrer (Optional)

If using Meta (Facebook/Instagram) ads, add these to `<queries>` (outside `<application>`):

```xml
<queries>
    <package android:name="com.facebook.katana" />
    <package android:name="com.instagram.android" />
</queries>
```

---

## 3. Core Initialization

### Critical: Call connect() in onResume()

Unlike many SDKs, Tenjin **must** be connected every time the app comes to the foreground to track sessions correctly. For most apps, this means calling `connect()` in the `onResume()` method of your main `Activity`.

> **Note for other stores:** If your app is not in Google Play or Amazon (e.g., Huawei, Samsung), call `connect()` in `onCreate()` instead.

### Java (Main Activity)

```java
import com.tenjin.android.TenjinSDK;

public class MainActivity extends AppCompatActivity {
    @Override
    protected void onResume() {
        super.onResume();
        
        // Initialize the singleton
        TenjinSDK instance = TenjinSDK.getInstance(this, "<SDK_KEY>");
        
        // Call connect() on every resume
        instance.connect();
    }
}
```

### Kotlin (Main Activity)

```kotlin
import com.tenjin.android.TenjinSDK

class MainActivity : AppCompatActivity() {
    override fun onResume() {
        super.onResume()
        
        val instance = TenjinSDK.getInstance(this, "<SDK_KEY>")
        instance.connect()
    }
}
```

### ProGuard / R8 Rules

If using obfuscation, add these to `proguard-rules.pro`:

```text
-keep class com.tenjin.** { *; }
-keep public class com.google.android.gms.ads.identifier.** { *; }
-keep public class com.android.installreferrer.** { *; }
-keep public class com.google.android.gms.appset.** { *; }
```

---

## 4. Purchase Event Tracking

### Google Play IAP

To track purchases with validation, you must first add your **Base64-encoded RSA public key** in the Tenjin dashboard.

```java
// Inside your purchase callback
instance.transaction(
    productId,      // String
    currencyCode,   // String (e.g. "USD")
    quantity,       // int
    unitPrice,      // double
    purchaseData,   // String (from Google Play response)
    signature       // String (from Google Play response)
);
```

### Amazon AppStore IAP

Add your **Amazon Shared Key** in the Tenjin dashboard first.

```java
instance.transactionAmazon(
    productId,
    currencyCode,
    quantity,
    unitPrice,
    amazonUserId,   // String
    amazonPurchaseToken // String
);
```

### Manual Revenue (No Validation)

```java
instance.transaction("premium_upgrade", "USD", 1, 9.99);
```

---

## 5. Custom Events

> **Prerequisite:** `connect()` should be called before sending any custom events.

```java
// Event without value
instance.eventWithName("level_complete");

// Event with integer value (used as count/sum)
instance.eventWithNameAndValue("coins_spent", 100);
```

**Limits:**
- Event names must be under **80 characters**.
- Maximum **500 unique** event names per app.

---

## 6. GDPR & Privacy Compliance

### Full Opt-In / Opt-Out

```java
TenjinSDK instance = TenjinSDK.getInstance(this, "<SDK_KEY>");

if (userConsented) {
    instance.optIn();
} else {
    instance.optOut(); // No API requests will be sent
}

instance.connect();
```

### Granular Parameter Control

```java
// Only send specific parameters
String[] allowList = {"ip_address", "advertising_id", "developer_device_id"};
instance.optInParams(allowList);

// Or send everything EXCEPT these
String[] denyList = {"locale", "timezone"};
instance.optOutParams(denyList);
```

### CMP-Based Consent

Automatically opt in/out based on CMP consent (TCF purpose 1):

```java
instance.optInOutUsingCMP();
```

### Google DMA Parameters

Manage consent for Google personalization and user data:

```java
// Manual control
instance.setGoogleDMAParameters(true, true); // (adPersonalization, adUserData)

// Toggle collection
instance.optInGoogleDMA();  // default
instance.optOutGoogleDMA();
```

---

## 7. Deep Linking (Deferred)

To handle deep links for attribution:

```java
instance.getDeeplink(new TenjinDeeplinkHandler() {
    @Override
    public void onSuccess(Map<String, String> params) {
        if (params.containsKey("clicked_tenjin_link")) {
            // Handle deep link parameters
            String adset = params.get("adset_name");
        }
    }
});
```

---

## 8. Impression Level Ad Revenue (ILRD)

> **Note:** ILRD is a paid feature. Contact your Tenjin account manager before implementing.

Specific methods are provided for various mediation platforms:

```java
// AppLovin MAX
instance.eventApplovin(maxAd);

// Unity LevelPlay (IronSource)
instance.eventIronsource(impressionData);

// AdMob
instance.eventAdmob(adValue);

// TopOn
instance.eventTopon(toponData);

// CAS
instance.eventCas(casData);
```

---

## 9. User Identity & Analytics

### Customer User ID

```java
instance.setCustomerUserId("user_123");
String userId = instance.getCustomerUserId();
```

### Analytics Installation ID

A locally generated persistent identifier:

```java
String analyticsId = instance.getAnalyticsInstallationId();
```

### User Profile Data

```java
// Get as object
TenjinUserProfile profile = instance.getUserProfile();

// Get as dictionary
Map<String, Object> dict = instance.getUserProfileDictionary();
```

---

## 10. Additional Configuration

### App Subversion (A/B Testing)

```java
instance.appendAppSubversion(8888); // Reports as e.g. "1.0.1.8888"
```

### Event Caching (Offline Support)

```java
instance.setCacheEventSetting(true);
```

---

## 11. Integration Checklist

When integrating Tenjin into an Android project, verify these items:

- [ ] **SDK version** is the latest from Maven Central.
- [ ] **AndroidManifest.xml** has `INTERNET` and `ACCESS_NETWORK_STATE` permissions.
- [ ] **AndroidManifest.xml** has `AD_ID` permission for Android 13+.
- [ ] **AndroidManifest.xml** has `TENJIN_APP_STORE` meta-data set correctly.
- [ ] **`connect()`** is called in `onResume()` of the main Activity.
- [ ] **`connect()`** is called on every app launch, not just the first.
- [ ] **Google Play dependencies** (AAID, AppSetID, Install Referrer) are included.
- [ ] **Proguard rules** are added if using obfuscation.
- [ ] **`<SDK_KEY>`** placeholder is replaced with the actual key.
- [ ] Integration is verified using the [Live Test Device Data Tool](https://www.tenjin.io/dashboard/sdk_diagnostics).

---

## 12. Common Mistakes to Avoid

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Calling `connect()` only on first launch | Tenjin needs session data on every launch; accounts may be suspended | Move `connect()` to `onResume()` unconditionally |
| Missing `AD_ID` permission | Cannot access AAID on Android 13+, degrades attribution quality | Add `<uses-permission android:name="com.google.android.gms.permission.AD_ID" />` |
| Forgetting `installreferrer` dependency | No Google Play install attribution | Add `com.android.installreferrer:installreferrer` to build.gradle |
| Sending events before `connect()` | Events will not be processed | Always call `connect()` first |
| Event names over 80 characters | Will be rejected | Keep event names concise |
| Exceeding 500 unique event names | Additional events will be dropped | Reuse event names with different values |
| Hardcoding `googleplay` for Amazon builds | Revenue validation will fail | Set `TENJIN_APP_STORE` to `amazon` for Amazon builds |

---

## 13. Full API Reference

### Initialization & Core

| Method | Purpose |
|--------|---------|
| `getInstance(Context, String)` | Returns singleton instance |
| `connect()` | Sends install/session data to Tenjin |
| `setAppStore(AppStoreType)` | Sets target app store programmatically |
| `appendAppSubversion(int)` | A/B test variant tracking |

### Events & Revenue

| Method | Purpose |
|--------|---------|
| `eventWithName(String)` | Custom event (name only) |
| `eventWithNameAndValue(String, int)` | Custom event with integer value |
| `transaction(...)` | Google Play purchase with validation |
| `transactionAmazon(...)` | Amazon purchase with validation |
| `getDeeplink(Handler)` | Retrieve deferred deep link parameters |

### Privacy & Consent

| Method | Purpose |
|--------|---------|
| `optIn()` / `optOut()` | GDPR full opt-in/out |
| `optInParams(String[])` / `optOutParams(String[])` | Granular parameter control |
| `optInOutUsingCMP()` | Automatic CMP-based consent |
| `setGoogleDMAParameters(...)` | Set Google DMA consent flags |

### Identity & Analytics

| Method | Purpose |
|--------|---------|
| `setCustomerUserId(String)` | Set custom user identifier |
| `getAnalyticsInstallationId()` | Get persistent local analytics ID |
| `getUserProfile()` | Get user metrics as typed object |

---

## 14. How to Use This Document

**With any LLM:**

```
Add Tenjin to my Android app using this guide:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/android/llm-guide.md
```
