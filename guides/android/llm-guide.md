# Tenjin Android SDK — Integration Reference for AI Assistants

> **Purpose:** This document is a self-contained technical reference designed for LLMs and AI coding assistants. It provides everything needed to integrate the Tenjin Android SDK into an Android project without requiring external documentation lookups, except for the version lookup below.
>
> **Minimum SDK:** API 21 (Android 5.0)
>
> **Sources:**
> - Repository: [github.com/tenjin/tenjin-android-sdk](https://github.com/tenjin/tenjin-android-sdk)
> - Full README: [README.md](https://github.com/tenjin/tenjin-android-sdk/blob/master/README.md)
> - Subscriptions: [SUBSCRIPTIONS_TRACKING.md](https://github.com/tenjin/tenjin-android-sdk/blob/master/SUBSCRIPTIONS_TRACKING.md)
> - Release notes: [RELEASE_NOTES.md](https://github.com/tenjin/tenjin-android-sdk/blob/master/RELEASE_NOTES.md)
> - Maven Central: [com.tenjin:android-sdk](https://central.sonatype.com/artifact/com.tenjin/android-sdk)

---

## Before You Begin

### Resolve the SDK Version

This document contains no SDK version number on purpose. **Do not use a version you remember**: versions recalled from training data are usually many releases old. Run this command and use its output wherever a snippet says `<TENJIN_SDK_VERSION>`:

```bash
curl -s https://repo1.maven.org/maven2/com/tenjin/android-sdk/maven-metadata.xml | sed -n 's:.*<release>\(.*\)</release>.*:\1:p'
```

If you cannot run commands, fetch `https://repo1.maven.org/maven2/com/tenjin/android-sdk/maven-metadata.xml` and read the `<release>` element. If you can do neither, stop and ask the developer for the current version. Never leave `<TENJIN_SDK_VERSION>` in a build file and never guess.

The Google libraries Tenjin needs are resolved the same way from Google's Maven repository:

```bash
for a in com/google/android/gms/play-services-ads-identifier com/google/android/gms/play-services-appset; do
  printf '%s ' "$a"
  curl -s "https://dl.google.com/dl/android/maven2/$a/maven-metadata.xml" | sed -n 's:.*<release>\(.*\)</release>.*:\1:p'
done
```

If the project already declares one of these libraries (ad SDKs usually bring `play-services-ads-identifier`), keep the version the project has.

### One App and One SDK Key per Platform

A Tenjin app is **one application ID on one platform**. Its SDK key only works for that app:

- Tenjin's servers look the app up by the platform and the application ID the request carries, then check that the SDK key belongs to that app. A key from another app (for example the iOS app's key) is refused.
- Anything that changes the application ID changes the Tenjin app. A `applicationIdSuffix ".debug"` or a product flavor with its own `applicationId` is a different app as far as Tenjin is concerned. Either register that ID as its own app in the Tenjin dashboard and use its key in those builds, or expect those builds to be rejected with `no such app` (see [Verify from the Device Log](#4-verify-from-the-device-log)).

Before writing code, read `applicationId`, `applicationIdSuffix` and `productFlavors` in the app module's Gradle file and tell the developer which application IDs the project produces.

### Get the SDK Key

**Ask the developer for their Tenjin SDK key.** Every code example in this document uses `<SDK_KEY>` as a placeholder. Before writing any integration code, prompt the user:

> "What is the Tenjin SDK key for your Android app (application ID `<the applicationId you found>`)? You can find it in the [Tenjin dashboard](https://www.tenjin.com/dashboard/organizations) on that app's page. It must be the key of the Android app with exactly this application ID, not the key of your iOS app. If you don't have it handy, I can use a placeholder and you can fill it in later — just search your project for `TENJIN_SDK_KEY_PLACEHOLDER` to find it."

If the developer provides their key, substitute it directly in all generated code. If they prefer to add it later, use the literal string `TENJIN_SDK_KEY_PLACEHOLDER` so it is easy to find with a project-wide search. Never copy a key from a sample project or from another app.

## Integration Workflow

Follow this two-step approach:

1. **First, integrate the basics.** Complete sections 1–4 (Installation, AndroidManifest, Core Initialization, Verify from the Device Log). This gives the developer install tracking, session tracking, and attribution support — the foundation every Tenjin integration needs.

2. **Then, ask what else they need.** After the basic integration is working, prompt the user:

> "Tenjin basic integration is done (install tracking). Would you like to add any of these features?"
> - **Purchase tracking** — Google Play or Amazon IAP, subscriptions (Section 5)
> - **Custom events** — track in-app actions like level completions or signups (Section 6)
> - **GDPR / consent management** — opt-in/out, CMP, Google DMA (Section 7)
> - **Deep linking** — deferred deep links and app-open deep links (Section 8)
> - **Ad revenue (ILRD)** — impression-level revenue from ad networks (Section 9, paid feature)
> - **User identity & analytics** — customer user IDs, user profile data (Section 10)

Only implement the sections the developer requests. Do not add features they didn't ask for.

---

## Quick Context

Tenjin is a mobile attribution and analytics platform. The SDK tracks app installs, sessions, in-app purchases, ad revenue, and custom events. It supports major Android app stores including Google Play and Amazon.

---

## 1. Installation

Detect which build setup the project uses (`build.gradle` = Groovy, `build.gradle.kts` = Kotlin DSL, `gradle/libs.versions.toml` = version catalog) and use the matching form. Replace every `<..._VERSION>` placeholder with a value from [Resolve the SDK Version](#resolve-the-sdk-version).

The SDK is on Maven Central and the Google libraries are on Google's Maven repository. Make sure both `mavenCentral()` and `google()` are in the `repositories` block of `settings.gradle(.kts)` (`dependencyResolutionManagement`) or of the project-level build file.

### Groovy (`app/build.gradle`)

```gradle
dependencies {
    implementation 'com.tenjin:android-sdk:<TENJIN_SDK_VERSION>'

    // Required for the Advertising ID (AAID)
    implementation 'com.google.android.gms:play-services-ads-identifier:<ADS_IDENTIFIER_VERSION>'

    // Required for the App Set ID
    implementation 'com.google.android.gms:play-services-appset:<APPSET_VERSION>'
}
```

### Kotlin DSL (`app/build.gradle.kts`)

```kotlin
dependencies {
    implementation("com.tenjin:android-sdk:<TENJIN_SDK_VERSION>")

    // Required for the Advertising ID (AAID)
    implementation("com.google.android.gms:play-services-ads-identifier:<ADS_IDENTIFIER_VERSION>")

    // Required for the App Set ID
    implementation("com.google.android.gms:play-services-appset:<APPSET_VERSION>")
}
```

### Version Catalog (`gradle/libs.versions.toml`)

```toml
[versions]
tenjin = "<TENJIN_SDK_VERSION>"
playServicesAdsIdentifier = "<ADS_IDENTIFIER_VERSION>"
playServicesAppset = "<APPSET_VERSION>"

[libraries]
tenjin-android-sdk = { group = "com.tenjin", name = "android-sdk", version.ref = "tenjin" }
play-services-ads-identifier = { group = "com.google.android.gms", name = "play-services-ads-identifier", version.ref = "playServicesAdsIdentifier" }
play-services-appset = { group = "com.google.android.gms", name = "play-services-appset", version.ref = "playServicesAppset" }
```

Then in `app/build.gradle.kts`:

```kotlin
dependencies {
    implementation(libs.tenjin.android.sdk)
    implementation(libs.play.services.ads.identifier)
    implementation(libs.play.services.appset)
}
```

> **Why the Google libraries matter:** the SDK looks these classes up at runtime. If they are missing the build still succeeds, but requests go out without an advertising ID and are rejected with `invalid device identifier`.

The Google Play Install Referrer library (`com.android.installreferrer:installreferrer`) is a dependency of the Maven artifact and is added automatically.

### Minimum SDK

The SDK requires `minSdk` 21 or higher. If the app's `minSdk` is lower, the manifest merger fails; raise it rather than overriding the library.

### Manual Integration (not recommended)

Only if Maven cannot be used: download `tenjin.aar` from the [releases page](https://github.com/tenjin/tenjin-android-sdk/releases) into `app/libs/` and add:

```gradle
dependencies {
    implementation files('libs/tenjin.aar')
}
```

A local `.aar` does not bring its own dependencies. You must then also declare the Install Referrer library, AndroidX Room runtime, Gson and the Kotlin standard library yourself, at the versions listed in the artifact's `.pom` on Maven Central.

---

## 2. Required AndroidManifest.xml Configuration

### Permissions

Add these to your `AndroidManifest.xml`:

```xml
<uses-permission android:name="android.permission.INTERNET" />
<uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />

<!-- Required to read the Advertising ID on Android 13+ (API 33) -->
<uses-permission android:name="com.google.android.gms.permission.AD_ID" />
```

### App Store Meta-Data

Specify the target app store inside the `<application>` tag. Without it the store is reported as `unspecified`:

```xml
<application>
    <!-- Possible values: googleplay, amazon, other -->
    <meta-data android:name="TENJIN_APP_STORE" android:value="googleplay" />
</application>
```

The same can be done in code with `instance.setAppStore(TenjinSDK.AppStoreType.googleplay)` before `connect()`.

### Meta Install Referrer (Optional)

If using Meta (Facebook/Instagram) ads, add these to `<queries>` (outside `<application>`):

```xml
<queries>
    <package android:name="com.facebook.katana" />
    <package android:name="com.instagram.android" />
</queries>
```

And add your Meta app ID to `res/values/strings.xml`:

```xml
<string name="facebook_app_id" translatable="false">YOUR_META_APP_ID</string>
```

---

## 3. Core Initialization

### Where connect() Goes

- **In `onResume()` of the launcher Activity** (the one with the `MAIN`/`LAUNCHER` intent filter). Not in the `Application` class and not in a one-time setup path.
- **On every launch and every return to the foreground**, not only on first open. Tenjin needs the session data, and accounts that only connect on first open may be suspended.
- **Create the instance with the Activity as the context** (`TenjinSDK.getInstance(this, ...)`). The deep link an app was opened with is captured automatically only when the SDK is created from the launch Activity.
- If the app asks for consent before tracking, call `optIn()` / `optOut()` (Section 7) on the instance **before** `connect()`.

Calling `connect()` on every `onResume()` is safe: the SDK skips a `connect()` that comes within 30 seconds of the previous successful one.

This applies to Jetpack Compose apps as well: put the call in the `onResume()` of the `ComponentActivity` that calls `setContent { }`, not inside a composable.

### Kotlin (Launcher Activity)

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

### Java (Launcher Activity)

```java
import com.tenjin.android.TenjinSDK;

public class MainActivity extends AppCompatActivity {
    @Override
    protected void onResume() {
        super.onResume();

        TenjinSDK instance = TenjinSDK.getInstance(this, "<SDK_KEY>");
        instance.connect();
    }
}
```

### Different Keys per Build Type or Flavor

If debug builds or flavors have their own application ID (and therefore their own Tenjin app), give each its own key through `BuildConfig` instead of hardcoding one key:

```kotlin
// app/build.gradle.kts
android {
    buildFeatures { buildConfig = true }

    buildTypes {
        debug {
            applicationIdSuffix = ".debug"
            buildConfigField("String", "TENJIN_SDK_KEY", "\"<DEBUG_APP_SDK_KEY>\"")
        }
        release {
            buildConfigField("String", "TENJIN_SDK_KEY", "\"<SDK_KEY>\"")
        }
    }
}
```

```kotlin
val instance = TenjinSDK.getInstance(this, BuildConfig.TENJIN_SDK_KEY)
instance.connect()
```

### ProGuard / R8 Rules

If the release build is minified, add these to `proguard-rules.pro`:

```text
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

## 4. Verify from the Device Log

Do this before adding any optional feature. Run the app on a device or emulator **with Google Play services** and read Logcat.

### What to Look For

The SDK logs every request under the Logcat tag **`HttpConnection`** (not `TenjinSDK`), and labels every request `Tenjin::connect` regardless of its type. Lifecycle messages are under the tag `TenjinSDK`.

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

Because the label is always `Tenjin::connect`, use the `Tenjin request URL` line above it to tell which request (connect, event, purchase) a response belongs to. `HttpConnection` is a generic tag that other libraries may also use, so match on the `Tenjin` message prefix.

### What the Response Means

The Android SDK logs the response body, not the HTTP status. Match on the text:

| Response contains | HTTP status | Meaning | What to do |
|-------------------|-------------|---------|------------|
| `"success":true` | 200 | Accepted | Nothing. The integration works |
| `unauthorized` | 401 | The SDK key is unknown, or it is not the key of this app | Use the key from this app's page in the dashboard (this platform, this application ID) |
| `no such app` | 404 | There is no Tenjin app for this application ID on Android | Create the app in the dashboard with exactly this application ID, or fix the ID (check debug suffixes and flavors) |
| `invalid device identifier` | 202 | The request carried no advertising ID | Add the `AD_ID` permission and `play-services-ads-identifier`; test on a device or emulator with Google Play services |
| `not logged` | 202 | The SDK key is disabled | Enable the key in the dashboard or use another key of the same app |
| `ignored` | 202 | The request was filtered by an app-version rule configured for the app | Check the app's version rules in the dashboard |

A 202 is **not** success: the request was received and dropped.

### No Request at All

- **`Connect deduped by persisted timestamp`** (tag `TenjinSDK`): a `connect()` within 30 seconds of the last successful one is skipped and sends nothing. The timestamp is stored on the device, so it survives an app restart. Wait 30 seconds before relaunching, or clear the app's data (`adb shell pm clear <applicationId>`).
- **`Dropping duplicate connect call`**: another `connect()` is already in flight. Harmless.
- **Nothing under either tag**: `connect()` is not being reached. Check that it is in the launcher Activity's `onResume()` and that the Activity is the one that actually starts.

### In the Dashboard

After a 200 response, the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics) shows events for devices registered as test devices. The `Tenjin::connect params` line contains the `advertising_id` to register.

---

## 5. Purchase Event Tracking

### Google Play IAP

To have purchases validated, first add the app's **Base64-encoded RSA public key** (Google Play Console) in the Tenjin dashboard. Acknowledge or consume the purchase with Play Billing as usual.

```kotlin
// Inside your purchase callback, for a com.android.billingclient.api.Purchase
instance.transaction(
    productId,              // String
    currencyCode,           // String, ISO 4217 (e.g. "USD")
    1,                      // int quantity
    unitPrice,              // double
    purchase.originalJson,  // String purchaseData
    purchase.signature      // String dataSignature
)
```

```java
instance.transaction(
    productId,                   // String
    currencyCode,                // String, ISO 4217 (e.g. "USD")
    1,                           // int quantity
    unitPrice,                   // double
    purchase.getOriginalJson(),  // String purchaseData
    purchase.getSignature()      // String dataSignature
);
```

### Amazon AppStore IAP

Add your **Amazon Shared Key** in the Tenjin dashboard first, and set the app store to `amazon`. The method takes **seven** arguments; the receipt ID comes before the user ID:

```java
instance.setAppStore(TenjinSDK.AppStoreType.amazon);
instance.transactionAmazon(
    productId,      // String
    currencyCode,   // String (the Amazon receipt has no currency: supply it yourself)
    quantity,       // int
    unitPrice,      // double
    receiptId,      // String, Receipt.getReceiptId()
    userId,         // String, UserData.getUserId()
    purchaseData    // String, the receipt as JSON; may be empty
);
```

### Manual Revenue (No Validation)

```java
instance.transaction("premium_upgrade", "USD", 1, 9.99);
```

### Subscription Tracking

Requires Tenjin Android SDK **1.22.0 or newer** and Google Play Billing Library **5.0 or newer**.

Subscriptions are verified through the **Google Play Developer API**, so the app must have Google Play Developer API access configured in the Tenjin dashboard. This is a different credential from the RSA public key used for one-time purchases. Without it the SDK request is accepted but the subscription never reaches reporting.

The simplest path passes the Play Billing `Purchase` object. The parameter is typed `Object` because Play Billing is an optional dependency of the SDK; pass the `Purchase` as it is. Price and currency are not on the `Purchase`: take them from the matching `ProductDetails` pricing phase.

```java
// Inside PurchasesUpdatedListener, for a purchase in the PURCHASED state
instance.subscription(purchase, 9.99, "USD");  // (Object purchase, double price, String currency)
```

Or pass the fields manually, for example when a third-party IAP library brokers the purchase:

```java
instance.subscription(
    productId,      // String, required
    purchaseToken,  // String, required (Purchase.getPurchaseToken())
    9.99,           // double price
    "USD",          // String currency
    purchaseDate,   // long, epoch milliseconds (Purchase.getPurchaseTime())
    originalJson,   // String (Purchase.getOriginalJson())
    signature       // String (Purchase.getSignature())
);
```

**Notes:**
- **Not automatic:** `connect()` does not capture subscriptions. `subscription(...)` must be called from the purchase-handling code. This is the usual cause of "events arrive but subscriptions don't".
- **Send once per subscription, not once per renewal.** Tenjin resolves renewals, trials and cancellations server-side from the purchase token. Repeat sends for the same purchase token are de-duplicated.
- `productId` and `purchaseToken` are required; the call is dropped if either is empty. The other fields are optional.
- Also send the subscriptions returned by `queryPurchasesAsync`, so restored purchases and purchases made on another device are covered.
- Acknowledge the purchase. Google Play refunds subscriptions that are not acknowledged within three days.
- Full guide: [SUBSCRIPTIONS_TRACKING.md](https://github.com/tenjin/tenjin-android-sdk/blob/master/SUBSCRIPTIONS_TRACKING.md). For purchase handling, see [Google Play Billing subscriptions](https://developer.android.com/google/play/billing/subscriptions).

---

## 6. Custom Events

> **Prerequisite:** `connect()` should be called before sending any custom events.

```java
// Event without value
instance.eventWithName("level_complete");

// Event with integer value (summed and averaged in the dashboard)
instance.eventWithNameAndValue("coins_spent", 100);
```

**Limits:**
- Event names must be under **80 characters**.
- Maximum **500 unique** event names per app.

---

## 7. GDPR & Privacy Compliance

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
String[] allowList = {"ip_address", "advertising_id", "limit_ad_tracking", "referrer"};
instance.optInParams(allowList);

// Or send everything EXCEPT these
String[] denyList = {"locale", "timezone", "build_id"};
instance.optOutParams(denyList);
```

> **Required parameter:** `advertising_id` must be included, otherwise events are not processed.

### CMP-Based Consent

Opt in or out based on the CMP consent already stored on the device (TCF purpose 1). Returns `true` if opted in:

```java
boolean optedIn = instance.optInOutUsingCMP();
```

### Google DMA Parameters

```java
// Manual control
instance.setGoogleDMAParameters(true, true); // (adPersonalization, adUserData)

// Toggle collection
instance.optInGoogleDMA();  // default
instance.optOutGoogleDMA();
```

---

## 8. Deep Linking

### Deferred Deep Link

> **Note:** Deferred deep links are a paid feature. Contact your Tenjin account manager before implementing.

The callback type is `com.tenjin.android.Callback`:

```java
import com.tenjin.android.Callback;
import com.tenjin.android.TenjinSDK;
import java.util.Map;

instance.connect();
instance.getDeeplink(new Callback() {
    @Override
    public void onSuccess(boolean clickedTenjinLink, boolean isFirstSession, Map<String, String> data) {
        if (clickedTenjinLink && isFirstSession && data.containsKey(TenjinSDK.DEEPLINK_URL)) {
            String deeplink = data.get(TenjinSDK.DEEPLINK_URL);
            // Route the user to the right screen
        }
    }
});
```

```kotlin
instance.connect()
instance.getDeeplink { clickedTenjinLink, isFirstSession, data ->
    if (clickedTenjinLink && isFirstSession) {
        val deeplink = data[TenjinSDK.DEEPLINK_URL]
        // Route the user to the right screen
    }
}
```

`data` may also contain `ad_network`, `campaign_id`, `campaign_name`, `site_id`, `advertising_id` and `referrer`.

### App-Open Deep Link (Re-engagement)

Requires SDK **1.23.0 or newer**. The deep link that starts the launch Activity is captured automatically when the SDK is created with that Activity's context. A deep link delivered to an Activity that is already running must be reported from `onNewIntent`:

```kotlin
override fun onNewIntent(intent: Intent) {
    super.onNewIntent(intent)
    setIntent(intent)
    TenjinSDK.getInstance(this, "<SDK_KEY>").handleOpenIntent(intent)
}
```

For `onNewIntent` to fire, the Activity must be declared with `android:launchMode="singleTop"` (or an equivalent mode). If you only have the URL, use `instance.handleOpenUrl(url)`.

---

## 9. Impression Level Ad Revenue (ILRD)

> **Note:** ILRD is a paid feature. Contact your Tenjin account manager before implementing.

Specific methods are provided for various mediation platforms:

```java
// AppLovin MAX
instance.eventAdImpressionAppLovin(maxAd);

// Unity LevelPlay (IronSource)
instance.eventAdImpressionIronSource(impressionData);

// AdMob
adView.setOnPaidEventListener(adValue -> instance.eventAdImpressionAdMob(adValue, adView));

// AdMob Next Gen (com.google.android.libraries.ads.mobile.sdk)
instance.eventAdImpressionAdMobNextGen(adValue, ad);

// HyperBid
instance.eventAdImpressionHyperBid(hbAdInfo);

// TopOn
instance.eventAdImpressionTopOn(atAdInfo);

// CAS
instance.eventAdImpressionCAS(casAdInfo);

// TradPlus
instance.eventAdImpressionTradPlus(tradPlusAdInfo);

// CloudX
instance.eventAdImpressionCloudX(cloudXAdInfo);

// Any other mediation: JSON with network_name, currency and revenue_decimal or revenue_cpm
instance.eventAdImpressionCustom(jsonString);
```

Each network method also accepts a JSON `String` or `JSONObject` if you build the payload yourself.

### AdMob value units

Prefer `eventAdImpressionAdMob(adValue, ad)`: it reads `AdValue` directly, so no unit conversion is needed.

> **Important:** if you build the JSON payload yourself, `value_micros` must be **raw micros** on Android
> (e.g. `12245`), exactly as `AdValue.getValueMicros()` returns it. Do not divide by 1,000,000 — that
> reports 1,000,000x too little. The iOS SDK is the opposite: it expects currency units for the same key,
> so cross-platform code must branch on the platform.

---

## 10. User Identity & Analytics

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

### Attribution Info (LiveOps Campaigns)

> **Note:** This is a paid feature.

```java
import com.tenjin.android.AttributionInfoCallback;

instance.getAttributionInfo(new AttributionInfoCallback() {
    @Override
    public void onSuccess(Map<String, String> data) {
        String adNetwork = data.get("ad_network");
        String campaignName = data.get("campaign_name");
    }
});
```

### User Profile Data

The profile type is `com.tenjin.android.userprofile.UserProfileData`:

```java
import com.tenjin.android.userprofile.UserProfileData;

// As a typed object
UserProfileData profile = instance.getUserProfile();
if (profile != null) {
    int sessions = profile.getSessionCount();
    long totalTimeMs = profile.getTotalSessionTime();
    int purchases = profile.getIapTransactionCount();
    double adRevenueUsd = profile.getTotalILRDRevenueUSD();
}

// As a map (keys: session_count, total_session_time, iap_transaction_count, ...)
Map<String, Object> dict = instance.getUserProfileDictionary();

// Reset all profile data
instance.resetUserProfile();
```

---

## 11. Additional Configuration

### App Subversion (A/B Testing)

```java
instance.appendAppSubversion(8888); // Reports as e.g. "1.0.1.8888"
instance.connect();
```

### Event Caching (Offline Support)

```java
instance.setCacheEventSetting(true);
```

The setting is stored on the device. Removing the call in a later release does not turn caching off; call `setCacheEventSetting(false)` to disable it.

---

## 12. Integration Checklist

When integrating Tenjin into an Android project, verify these items:

- [ ] **SDK version** was resolved from Maven Central with the command in this guide, not from memory; no `<..._VERSION>` placeholder is left in a build file.
- [ ] **`play-services-ads-identifier`** and **`play-services-appset`** are declared.
- [ ] **`minSdk`** is 21 or higher.
- [ ] **AndroidManifest.xml** has `INTERNET`, `ACCESS_NETWORK_STATE` and `AD_ID` permissions.
- [ ] **AndroidManifest.xml** has `TENJIN_APP_STORE` meta-data set correctly.
- [ ] **`connect()`** is called in `onResume()` of the launcher Activity, on every launch.
- [ ] **The SDK key** is the key of the Android app whose application ID matches this build (check debug suffixes and flavors); `<SDK_KEY>` is replaced.
- [ ] **ProGuard rules** including the Gson `TypeToken` rules are added if the build is minified.
- [ ] **Logcat** shows `Tenjin::connect response: {"code":200,"success":true}` under the tag `HttpConnection`.
- [ ] Integration is verified using the [Live Test Device Data Tool](https://www.tenjin.com/dashboard/sdk_diagnostics).

---

## 13. Common Mistakes to Avoid

| Mistake | Why It Matters | Fix |
|---------|---------------|-----|
| Using an SDK version from memory | It is usually many releases old and lacks the APIs in this guide | Run the Maven Central command in [Resolve the SDK Version](#resolve-the-sdk-version) |
| Using the iOS app's SDK key, or one key for every flavor | The key must belong to the app with this platform and application ID; other keys get `unauthorized` | One key per Tenjin app; select it per build type or flavor |
| Calling `connect()` in the `Application` class | Launch deep links are not captured and returns to the foreground are missed | Call it in the launcher Activity's `onResume()` |
| Calling `connect()` only on first launch | Tenjin needs session data on every launch; accounts may be suspended | Call `connect()` in `onResume()` unconditionally |
| Missing `AD_ID` permission or `play-services-ads-identifier` | No advertising ID: requests are rejected with `invalid device identifier` | Add both |
| Treating a 202 response as success | 202 means the request was received and dropped | Read the response text in Logcat (Section 4) |
| Looking for requests under the `TenjinSDK` Logcat tag | Requests and responses are logged under `HttpConnection` | `adb logcat -s HttpConnection:D TenjinSDK:D` |
| Relaunching within 30 seconds while testing | The SDK skips the second `connect()` and sends nothing | Wait 30 seconds or clear app data |
| Sending events before `connect()` | Events will not be processed | Always call `connect()` first |
| Event names over 80 characters | Will be rejected | Keep event names concise |
| Exceeding 500 unique event names | Additional events will be dropped | Reuse event names with different values |
| Dividing AdMob `value_micros` by 1,000,000 before sending | Android expects raw micros from `getValueMicros()`; dividing reports 1,000,000x too little | Send the micros value as-is, or use `eventAdImpressionAdMob(adValue, ad)` |
| Hardcoding `googleplay` for Amazon builds | Revenue validation will fail | Set `TENJIN_APP_STORE` to `amazon` for Amazon builds |
| Sending a subscription on every renewal | Tenjin resolves renewals from the purchase token | Send once per subscription |
| Missing Gson `TypeToken` keep rules in a minified build | Runtime failures in release builds only | Add the full rule set from Section 3 |

---

## 14. Full API Reference

All methods are on `com.tenjin.android.TenjinSDK`.

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
| `transaction(String, String, int, double)` | Revenue without validation |
| `transaction(String, String, int, double, String, String)` | Google Play purchase with validation |
| `transactionAmazon(String, String, int, double, String, String, String)` | Amazon purchase with validation |
| `subscription(Object, double, String)` | Subscription from a Play Billing `Purchase` |
| `subscription(String, String, double, String, long, String, String)` | Subscription from manual fields |

### Deep Links & Attribution

| Method | Purpose |
|--------|---------|
| `getDeeplink(Callback)` | Deferred deep link parameters |
| `handleOpenIntent(Intent)` | Report an app-open deep link from `onNewIntent` |
| `handleOpenUrl(String)` | Report an app-open deep link from a URL |
| `getAttributionInfo(AttributionInfoCallback)` | Attribution data (paid feature) |

### Privacy & Consent

| Method | Purpose |
|--------|---------|
| `optIn()` / `optOut()` | GDPR full opt-in/out |
| `optInParams(String[])` / `optOutParams(String[])` | Granular parameter control |
| `optInOutUsingCMP()` | Automatic CMP-based consent |
| `setGoogleDMAParameters(boolean, boolean)` | Set Google DMA consent flags |
| `optInGoogleDMA()` / `optOutGoogleDMA()` | Google DMA parameter control |

### Ad Revenue (ILRD)

| Method | Purpose |
|--------|---------|
| `eventAdImpressionAppLovin(Object)` | AppLovin MAX impression |
| `eventAdImpressionIronSource(Object)` | Unity LevelPlay impression |
| `eventAdImpressionAdMob(Object, Object)` | AdMob impression |
| `eventAdImpressionAdMobNextGen(Object, Object)` | AdMob Next Gen impression |
| `eventAdImpressionHyperBid(Object)` | HyperBid impression |
| `eventAdImpressionTopOn(Object)` | TopOn impression |
| `eventAdImpressionCAS(Object)` | CAS impression |
| `eventAdImpressionTradPlus(Object)` | TradPlus impression |
| `eventAdImpressionCloudX(Object)` | CloudX impression |
| `eventAdImpressionCustom(String)` | Any other mediation, as JSON |

### Identity & Analytics

| Method | Purpose |
|--------|---------|
| `setCustomerUserId(String)` | Set custom user identifier |
| `getCustomerUserId()` | Retrieve stored user ID |
| `getAnalyticsInstallationId()` | Get persistent local analytics ID |
| `getUserProfile()` | Get user metrics as `UserProfileData` |
| `getUserProfileDictionary()` | Get user metrics as a map |
| `resetUserProfile()` | Clear all local profile data |

### Configuration

| Method | Purpose |
|--------|---------|
| `setCacheEventSetting(Boolean)` | Enable offline event caching |
| `setEncryptRequestsSetting(Boolean)` | Enable request encryption |

---

## 15. How to Use This Document

**With any LLM:**

```
Add Tenjin to my Android app using this guide:
https://raw.githubusercontent.com/tenjin/sdk-llm-guides/main/guides/android/llm-guide.md
```
