# Tenjin SDK Integration Guide for AI

## Context
Tenjin is a mobile measurement platform (MMP) for attribution and analytics.
**Crucial Implementation Detail:** Unlike most SDKs, Tenjin requires the `connect()` method to be called every time the app comes to the foreground (Lifecycle: `onResume` or `OnApplicationPause`), not just on startup.

---

## 1. Android Integration (Native)

### Core Setup
* **Dependency (build.gradle):**
    `implementation 'com.tenjin:android-sdk:1.15.4'` (Check for latest)
* **Permissions (AndroidManifest.xml):**
    * `<uses-permission android:name="android.permission.INTERNET" />`
    * `<uses-permission android:name="com.google.android.gms.permission.AD_ID" />` (Required for Android 13+)
* **Meta Data:**
    Inside `<application>` tag:
    `<meta-data android:name="TENJIN_APP_STORE" android:value="googleplay" />`

### Initialization Code
**Rule:** Must be in `onResume()`.

```java
import com.tenjin.android.TenjinSDK;

@Override
protected void onResume() {
    super.onResume();
    TenjinSDK instance = TenjinSDK.getInstance(this, "YOUR_SDK_KEY");
    instance.connect();
}
```

### ProGuard / R8 Rules
If using obfuscation, add this to `proguard-rules.pro`:
```text
-keep class com.tenjin.** { *; }
-keep public class com.google.android.gms.ads.identifier.** { *; }
-keep public class com.android.installreferrer.** { *; }
```

---

## 2. Unity Integration

### Core Setup
* Download and import the specific `Tenjin.unitypackage`.
* Add the script to a GameObject that persists across scenes (`DontDestroyOnLoad`).

### Initialization Code
**Rule:** Use `OnApplicationPause` to handle background/foreground transitions.

```csharp
using UnityEngine;

public class TenjinManager : MonoBehaviour
{
    void Start()
    {
        TenjinConnect();
    }

    void OnApplicationPause(bool pauseStatus)
    {
        if (!pauseStatus)
        {
            // App is returning to foreground
            TenjinConnect();
        }
    }

    void TenjinConnect()
    {
        BaseTenjin instance = Tenjin.getInstance("YOUR_SDK_KEY");
        instance.Connect();
    }
}
```

---

## 3. Privacy (GDPR/CMP) & Compliance

For EEA users, you must pass consent flags **before** calling `connect()`.

```java
// Android Example
instance.optIn(); // If user consented
instance.optOut(); // If user declined
instance.setGoogleAdAppSetIdReporting(true); // For Google DMA compliance
instance.connect();
```

---

## 4. Event Tracking

### Standard Events
* **Custom Event:** `instance.eventWithName("level_complete");`
* **Event with Value:** `instance.eventWithNameAndValue("coins_spent", 100);`

### Revenue Validation (Android)
Do not use simple events for revenue. Use `transaction` to validate receipts.

```java
instance.transaction(
    "product_id",
    "USD",
    1,
    0.99,
    "purchase_data_string",
    "signature_string"
);
```
