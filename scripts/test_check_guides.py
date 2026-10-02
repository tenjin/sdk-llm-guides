#!/usr/bin/env python3
"""Tests for check_guides.py.

Each case feeds the checker a snippet that is wrong (or right) in a known way.
Most of the wrong ones are mistakes that were once published in these guides.

Run: python3 scripts/test_check_guides.py
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import check_guides  # noqa: E402

SYMBOLS = check_guides.load_symbols()

# Messages about the guide as a whole; a one-snippet document always triggers them.
STRUCTURAL = ("missing required section", "the guide does not give", "expected the guide to state",
              "no Tenjin API use was recognised")


def api_errors(platform, language, code):
    markdown = "```%s\n%s\n```\n" % (language, code)
    report = check_guides.check_guide(platform, markdown, SYMBOLS)
    return [message for _, message in report.errors if not message.startswith(STRUCTURAL)]


class CheckerTest(unittest.TestCase):
    def flagged(self, platform, language, code, expected):
        errors = api_errors(platform, language, code)
        self.assertTrue(any(expected in error for error in errors),
                        "expected an error containing %r, got %r" % (expected, errors))

    def clean(self, platform, language, code):
        self.assertEqual(api_errors(platform, language, code), [])


class AndroidTest(CheckerTest):
    def test_unknown_method(self):
        self.flagged("android", "java", "instance.eventApplovin(maxAd);", "no method `eventApplovin`")

    def test_unknown_callback_type(self):
        code = ("instance.getDeeplink(new TenjinDeeplinkHandler() {\n"
                "    public void onSuccess(Map<String, String> params) {}\n"
                "});")
        self.flagged("android", "java", code, "`TenjinDeeplinkHandler` is not a type")

    def test_wrong_arity(self):
        code = "instance.transactionAmazon(productId, currencyCode, quantity, unitPrice, userId, token);"
        self.flagged("android", "java", code, "transactionAmazon takes 1 or 7 argument(s), the guide passes 6")

    def test_unknown_type(self):
        self.flagged("android", "java", "TenjinUserProfile profile = instance.getUserProfile();",
                     "`TenjinUserProfile` is not a type")

    def test_unknown_import(self):
        self.flagged("android", "java", "import com.tenjin.android.TenjinDeeplinkHandler;", "no such class")

    def test_unknown_enum_value(self):
        self.flagged("android", "java", "instance.setAppStore(TenjinSDK.AppStoreType.huawei);", "does not exist")

    def test_comment_is_not_an_argument(self):
        code = ("instance.transaction(\n"
                "    productId,   // String, e.g. \"a, b\"\n"
                "    \"USD\",\n"
                "    1,\n"
                "    9.99\n"
                ");")
        self.clean("android", "java", code)

    def test_valid_calls(self):
        self.clean("android", "java", 'TenjinSDK.getInstance(this, "<SDK_KEY>").connect();')
        self.clean("android", "java", "instance.setAppStore(TenjinSDK.AppStoreType.googleplay);")
        self.clean("android", "kotlin",
                   'val instance = TenjinSDK.getInstance(this, "<SDK_KEY>")\n'
                   "instance.getDeeplink { clicked, first, data -> }")
        self.clean("android", "java",
                   "import com.tenjin.android.Callback;\n"
                   "instance.getDeeplink(new Callback() {\n"
                   "    public void onSuccess(boolean a, boolean b, Map<String, String> data) {}\n"
                   "});")


class IosTest(CheckerTest):
    def test_swift_missing_import(self):
        self.flagged("ios", "swift", 'import SwiftUI\n\nTenjinSDK.getInstance("<SDK_KEY>")', "not `import TenjinSDK`")

    def test_swift_wrong_label(self):
        self.flagged("ios", "swift", 'TenjinSDK.sendEvent(name: "level_complete")', "matches the Swift call")

    def test_swift_unknown_method(self):
        self.flagged("ios", "swift", 'TenjinSDK.trackEvent("level_complete")', "no method `trackEvent`")

    def test_swift_valid_calls(self):
        self.clean("ios", "swift", 'TenjinSDK.sendEvent(withName: "coins", andValue: 5)')
        self.clean("ios", "swift", 'TenjinSDK.updatePostbackConversionValue(5, coarseValue: "medium")')
        self.clean("ios", "swift", "TenjinSDK.handleOpenURL(url)")
        self.clean("ios", "swift",
                   'let instance = TenjinSDK.getInstance("<SDK_KEY>")\n'
                   "instance.registerDeepLinkHandler { params, error in }")

    def test_swift_class_method_on_instance(self):
        self.flagged("ios", "swift",
                     'let instance = TenjinSDK.getInstance("<SDK_KEY>")\ninstance.connect()',
                     "no instance method")

    def test_objc_deprecated(self):
        self.flagged("ios", "objectivec", '[TenjinSDK init:@"<SDK_KEY>"];', "deprecated")

    def test_objc_unknown_selector(self):
        self.flagged("ios", "objectivec", '[TenjinSDK sendEvent:@"level_complete"];', "no selector `sendEvent:`")

    def test_objc_instance_method_on_class(self):
        self.flagged("ios", "objectivec",
                     "[TenjinSDK setGoogleDMAParametersWithAdPersonalization:YES adUserData:YES];",
                     "an instance method")

    def test_objc_valid_calls(self):
        self.clean("ios", "objectivec", "[TenjinSDK handleAdMobILRD:bannerView :adValue];")
        self.clean("ios", "objectivec", '[TenjinSDK sendEventWithName:@"coins" andValue:50];')
        self.clean("ios", "objectivec",
                   "[[TenjinSDK sharedInstance] setGoogleDMAParametersWithAdPersonalization:YES adUserData:YES];")
        self.clean("ios", "objectivec",
                   "NSArray *allow = @[@\"ip_address\", @\"advertising_id\"];\n[TenjinSDK optInParams:allow];")


class FlutterTest(CheckerTest):
    def test_wrong_import(self):
        self.flagged("flutter", "dart", "import 'package:tenjin_plugin/tenjin_plugin.dart';", "does not exist")

    def test_deprecated(self):
        self.flagged("flutter", "dart", "TenjinSDK.instance.init(apiKey: '<SDK_KEY>');", "deprecated")

    def test_named_parameters(self):
        errors = api_errors("flutter", "dart", "TenjinSDK.instance.initialize(apiKey: '<SDK_KEY>');")
        self.assertTrue(any("no named parameter `apiKey`" in error and "requires `sdkKey`" in error for error in errors), errors)

    def test_positional_count(self):
        self.flagged("flutter", "dart", "TenjinSDK.instance.transaction('p', 'USD', 1.0);", "takes 4 positional")

    def test_static_call(self):
        self.flagged("flutter", "dart", "TenjinSDK.setCustomerUserId('user');", "no static member")

    def test_valid_calls(self):
        self.clean("flutter", "dart",
                   "import 'package:tenjin_plugin/tenjin_sdk.dart';\n"
                   "TenjinSDK.instance.initialize(sdkKey: '<SDK_KEY>');\n"
                   "TenjinSDK.instance.optInParams(['ip_address', 'advertising_id']);\n"
                   "TenjinSDK.instance.connect();")


class ReactNativeTest(CheckerTest):
    def test_opt_in_with_list(self):
        self.flagged("react-native", "javascript", "Tenjin.optIn(['ip_address']);", "optIn takes 0 argument(s)")

    def test_named_import(self):
        self.flagged("react-native", "javascript", "import { Tenjin } from 'react-native-tenjin';", "default export")

    def test_object_keys(self):
        errors = api_errors("react-native", "javascript",
                            "Tenjin.subscription({ productId: 'p', currencyCode: 'USD', price: 1 });")
        self.assertTrue(any("no option `price`" in error for error in errors), errors)
        self.assertTrue(any("requires `unitPrice`" in error for error in errors), errors)

    def test_valid_calls(self):
        self.clean("react-native", "javascript",
                   "import Tenjin from 'react-native-tenjin';\n"
                   "Tenjin.initialize('<SDK_KEY>');\n"
                   "Tenjin.updatePostbackConversionValue(5, 'medium');\n"
                   "Tenjin.getAttributionInfo((info) => { use(info.a, info.b); }, (error) => {});")


class IonicTest(CheckerTest):
    def test_default_import(self):
        self.flagged("ionic", "typescript", "import Tenjin from 'ionic-capacitor-tenjin';", "no default export")

    def test_positional_argument(self):
        self.flagged("ionic", "typescript", "await Tenjin.eventWithName('level_complete');", "options object")

    def test_unknown_option(self):
        self.flagged("ionic", "typescript", "await Tenjin.initialize({ apiKey: '<SDK_KEY>' });", "no option `apiKey`")

    def test_unknown_method(self):
        self.flagged("ionic", "typescript", "await Tenjin.subscription({ productId: 'p' });", "no method `subscription`")

    def test_valid_calls(self):
        self.clean("ionic", "typescript",
                   "import { Tenjin } from 'ionic-capacitor-tenjin';\n"
                   "await Tenjin.initialize({ sdkKey });\n"
                   "await Tenjin.eventWithNameAndValue({ name: 'coins', value: '50' });\n"
                   "await Tenjin.connect();")


class UnityTest(CheckerTest):
    def test_manifest_key(self):
        self.flagged("unity", "json",
                     '"com.tenjin.unity-sdk": "https://github.com/tenjin/tenjin-unity-sdk.git#<TENJIN_SDK_VERSION>"',
                     "the package is named `com.tenjin.sdk`")

    def test_wrong_case(self):
        self.flagged("unity", "csharp",
                     'BaseTenjin instance = Tenjin.getInstance("<SDK_KEY>");\ninstance.updatePostbackConversionValue(5);',
                     "no method `updatePostbackConversionValue`")

    def test_wrong_arity(self):
        self.flagged("unity", "csharp", "instance.Transaction(id, currency, 1, 0.99, null, receipt);",
                     "Transaction takes 7 argument(s), the guide passes 6")

    def test_unknown_enum_value(self):
        self.flagged("unity", "csharp", "instance.SetAppStoreType(AppStoreType.huawei);", "no value `huawei`")

    def test_valid_calls(self):
        self.clean("unity", "csharp", 'Tenjin.getInstance("<SDK_KEY>").SendEvent("level_complete");')
        self.clean("unity", "csharp",
                   'BaseTenjin tenjin = Tenjin.getInstance("<SDK_KEY>");\n'
                   "tenjin.RequestTrackingAuthorizationWithCompletionHandler((status) => { tenjin.Connect(); });")


class TextTest(unittest.TestCase):
    def errors(self, text):
        report = check_guides.Report("<text>")
        check_guides.check_text(report, text)
        return [message for _, message in report.errors]

    def test_version_pins(self):
        for line in ["implementation 'com.tenjin:android-sdk:1.15.4'",
                     "tenjin_plugin: ^1.3.0",
                     '"com.tenjin.sdk": "https://github.com/tenjin/tenjin-unity-sdk.git#1.16.3"',
                     "pod 'TenjinSDK', '~> 1.14'",
                     "implementation 'com.google.android.gms:play-services-ads-identifier:{version}'",
                     "Always check the latest release first."]:
            self.assertTrue(self.errors(line), line)

    def test_placeholders_are_fine(self):
        for line in ["implementation 'com.tenjin:android-sdk:<TENJIN_SDK_VERSION>'",
                     "tenjin_plugin: ^<TENJIN_SDK_VERSION>",
                     "Requires Tenjin Android SDK **1.22.0 or newer**.",
                     'TenjinSDK.getInstance(this, "TENJIN_SDK_KEY_PLACEHOLDER")']:
            self.assertEqual(self.errors(line), [], line)

    def test_key_like_literal(self):
        self.assertTrue(self.errors('TenjinSDK.getInstance(this, "ABCDEFGHIJKLMNOPQRSTUVWXYZ012345");'))


class GuidesTest(unittest.TestCase):
    def test_every_guide_passes(self):
        for platform in check_guides.PLATFORMS:
            path = os.path.join(check_guides.ROOT, "guides", platform, "llm-guide.md")
            with open(path, encoding="utf-8") as handle:
                report = check_guides.check_guide(platform, handle.read(), SYMBOLS, path)
            self.assertEqual(report.errors, [], platform)
            self.assertGreater(report.checked, 20, platform)


if __name__ == "__main__":
    unittest.main()
