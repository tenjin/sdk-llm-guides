#!/usr/bin/env python3
"""Check the guides against the public API of the Tenjin SDKs.

For every fenced code block in guides/<platform>/llm-guide.md this script
extracts the Tenjin calls and checks them against sdk-symbols/<platform>.json,
which scripts/update_sdk_symbols.py generates from the public SDK
distributions. It fails when a guide names a method, type, import or argument
shape that the SDK does not have, or uses something the SDK marks deprecated.

It also checks a few things about the guides themselves: required sections,
the version-lookup command, no hardcoded SDK versions, placeholders for keys.

What it does not do: it does not compile anything. Argument types, calls into
other libraries (StoreKit, Play Billing, ad SDKs), XML and Gradle contents and
everything written in prose are not checked.

Usage:
  python3 scripts/check_guides.py            # check every guide
  python3 scripts/check_guides.py -v         # also list what was checked

Standard library only.
"""

import json
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLATFORMS = ["android", "ios", "flutter", "react-native", "ionic", "unity"]

LANGUAGES = {
    "java": "java", "kotlin": "kotlin", "kt": "kotlin",
    "swift": "swift",
    "objectivec": "objc", "objective-c": "objc", "objc": "objc",
    "dart": "dart",
    "javascript": "js", "js": "js", "jsx": "js",
    "typescript": "js", "ts": "js", "tsx": "js",
    "csharp": "csharp", "cs": "csharp",
    "json": "json",
}

REQUIRED_HEADINGS = [
    r"Resolve the SDK Version",
    r"One App and One SDK Key per Platform",
    r"Where [Cc]onnect\(\) Goes",
    r"Verify from the Device Log",
    r"Integration Checklist",
    r"Common Mistakes",
]

VERSION_LOOKUP = {
    "android": "repo1.maven.org/maven2/com/tenjin/android-sdk/maven-metadata.xml",
    "ios": "trunk.cocoapods.org/api/v1/pods/TenjinSDK",
    "flutter": "pub.dev/api/packages/tenjin_plugin",
    "react-native": "npm view react-native-tenjin version",
    "ionic": "npm view ionic-capacitor-tenjin version",
    "unity": "api.github.com/repos/tenjin/tenjin-unity-sdk/releases/latest",
}

# A Tenjin SDK version written into an install snippet.
VERSION_PINS = [
    (r"com\.tenjin:android-sdk:\d", "hardcoded Android SDK version"),
    (r"tenjin_plugin:\s*['\"^~>= ]*\d", "hardcoded tenjin_plugin version"),
    (r"tenjin-unity-sdk\.git#v?\d", "hardcoded Unity SDK tag"),
    (r"pod\s+['\"]TenjinSDK['\"]\s*,\s*['\"][~>= ]*\d", "hardcoded TenjinSDK pod version"),
    (r"tenjin-ios-spm[^\n]*(?:from|exact):\s*\"\d", "hardcoded TenjinSDK package version"),
    (r"\"(?:react-native-tenjin|ionic-capacitor-tenjin)\"\s*:\s*\"[\^~]?\d", "hardcoded npm package version"),
    (r"(?:react-native-tenjin|ionic-capacitor-tenjin)@\d", "hardcoded npm package version"),
    (r":\{version\}", "version placeholder with no way to resolve it"),
    (r"(?i)\bcheck (?:for |[\w.]+ for )?(?:the )?latest\b", "tells the reader to check for the latest version without saying how"),
]

POSSIBLE_KEY = re.compile(r"[\"'][A-Z0-9]{20,}[\"']")


# ---------------------------------------------------------------------------
# text helpers
# ---------------------------------------------------------------------------

def load_symbols():
    symbols = {}
    for platform in PLATFORMS:
        with open(os.path.join(ROOT, "sdk-symbols", platform + ".json"), encoding="utf-8") as handle:
            symbols[platform] = json.load(handle)
    return symbols


def code_blocks(markdown):
    """Yield (language, first_line_number, code) for each fenced block."""
    blocks, language, start, lines = [], None, 0, []
    for number, line in enumerate(markdown.split("\n"), 1):
        fence = re.match(r"\s*```\s*([\w+-]*)\s*$", line)
        if fence and language is None:
            language, start, lines = fence.group(1).lower() or "text", number + 1, []
        elif fence:
            blocks.append((language, start, "\n".join(lines)))
            language = None
        elif language is not None:
            lines.append(line)
    return blocks


def clean(code):
    """Blank out comments and the contents of string literals, keeping every offset."""
    out = list(code)
    index, length = 0, len(code)
    while index < length:
        char = code[index]
        if code.startswith("//", index):
            end = code.find("\n", index)
            end = length if end == -1 else end
            for position in range(index, end):
                out[position] = " "
            index = end
        elif code.startswith("/*", index):
            end = code.find("*/", index)
            end = length if end == -1 else end + 2
            for position in range(index, end):
                if code[position] != "\n":
                    out[position] = " "
            index = end
        elif char in "\"'`":
            end = index + 1
            while end < length and code[end] != char and code[end] != "\n":
                end += 2 if code[end] == "\\" else 1
            for position in range(index + 1, min(end, length)):
                out[position] = "_"
            index = end + 1
        else:
            index += 1
    return "".join(out)


def strip_comments_only(code):
    """Blank out comments but keep string contents (for import checks)."""
    masked = clean(code)
    return "".join(original if cleaned != " " or original == " " else " "
                   for original, cleaned in zip(code, masked))


def matching(text, start):
    """Index of the bracket closing the one at text[start], or -1."""
    pairs = {"(": ")", "[": "]", "{": "}"}
    stack = []
    for index in range(start, len(text)):
        char = text[index]
        if char in pairs:
            stack.append(pairs[char])
        elif char in ")]}":
            if not stack or stack.pop() != char:
                return -1
            if not stack:
                return index
    return -1


def split_args(text):
    parts, depth, current = [], 0, []
    for char in text:
        if char in "([{":
            depth += 1
        elif char in ")]}":
            depth -= 1
        if char == "," and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
    parts.append("".join(current))
    return [part.strip() for part in parts if part.strip()]


def line_of(code, index):
    return code.count("\n", 0, index)


def member_uses(text, receiver_pattern):
    """Yield (name, args, trailing_block, index, end) for `receiver.name...` in cleaned code.

    args is None for a plain member access, otherwise the text between the parentheses
    ("" when a call has only a trailing block). end is the index just after the use.
    """
    pattern = re.compile(r"(?<![\w.$])(?:%s)\s*\.\s*(\w+)" % receiver_pattern)
    for match in pattern.finditer(text):
        yield parse_use(text, match.group(1), match.start(), match.end())


def parse_use(text, name, start, position):
    rest = text[position:]
    stripped = rest.lstrip(" \t")
    offset = position + len(rest) - len(stripped)
    if stripped.startswith("("):
        close = matching(text, offset)
        if close == -1:
            return name, "", False, start, offset
        after = text[close + 1:].lstrip(" \t")
        return name, text[offset + 1:close], after.startswith("{"), start, close + 1
    if stripped.startswith("{"):
        close = matching(text, offset)
        return name, "", True, start, (close + 1 if close != -1 else offset)
    return name, None, False, start, position


def chained_use(text, end):
    """A `.name(...)` that directly follows position end, or None."""
    match = re.match(r"\s*\.\s*(\w+)", text[end:])
    if not match:
        return None
    return parse_use(text, match.group(1), end, end + match.end())


def object_keys(arg):
    """Top-level keys of an object literal `{ a: 1, b }`; None if it has a spread."""
    inner = arg.strip()[1:-1]
    keys = []
    for item in split_args(inner):
        if item.startswith("..."):
            return None
        keys.append(re.match(r"[\w$]+", item).group(0))
    return keys


class Report:
    def __init__(self, path):
        self.path = path
        self.errors = []
        self.checked = 0

    def error(self, line, message):
        if (line, message) not in self.errors:
            self.errors.append((line, message))

    def ok(self):
        self.checked += 1


# ---------------------------------------------------------------------------
# android (java, kotlin)
# ---------------------------------------------------------------------------

def android_simple_names(symbols):
    return {name.rsplit(".", 1)[-1].replace("$", "."): data for name, data in symbols["classes"].items()}


def check_android(report, start, code, symbols, guide_code):
    text = clean(code)
    classes = symbols["classes"]
    sdk = classes["com.tenjin.android.TenjinSDK"]
    simple = android_simple_names(symbols)
    profile = classes["com.tenjin.android.userprofile.UserProfileData"]

    receivers = {"instance", "tenjin"} | set(
        re.findall(r"(\w+)\s*=\s*TenjinSDK\s*\.\s*getInstance\w*\s*\(", guide_code))
    profiles = set(re.findall(r"(\w+)\s*=\s*\w+\s*\.\s*getUserProfile\s*\(\s*\)", guide_code))

    def check_instance_use(use):
        name, args, block, index, end = use
        line = start + line_of(code, index)
        arities = sorted(set(sdk["methods"].get(name, []) + sdk["static_methods"].get(name, [])))
        if not arities:
            getter = "get" + name[:1].upper() + name[1:]
            if args is None and getter in sdk["methods"]:
                report.ok()
                return
            report.error(line, "TenjinSDK has no method `%s`" % name)
            return
        if args is None:
            report.ok()
            return
        count = len(split_args(args)) + (1 if block else 0)
        if count not in arities:
            report.error(line, "TenjinSDK.%s takes %s argument(s), the guide passes %d"
                         % (name, " or ".join(map(str, arities)), count))
        else:
            report.ok()
        for anonymous in re.findall(r"\bnew\s+(\w+)\s*\(\s*\)\s*\{", args):
            if anonymous not in simple:
                report.error(line, "`%s` is not a type of the Tenjin Android SDK" % anonymous)
            else:
                report.ok()

    for use in member_uses(text, "|".join(sorted(map(re.escape, receivers)))):
        check_instance_use(use)

    for name, args, block, index, end in member_uses(text, "TenjinSDK"):
        line = start + line_of(code, index)
        if args is None:
            nested = "TenjinSDK." + name
            if nested in simple:
                member = re.match(r"\s*\.\s*(\w+)", text[end:])
                if member and member.group(1) not in simple[nested]["fields"]:
                    report.error(line, "`%s.%s` does not exist" % (nested, member.group(1)))
                else:
                    report.ok()
            elif name in sdk["fields"]:
                report.ok()
            else:
                report.error(line, "TenjinSDK has no static member `%s`" % name)
            continue
        if name not in sdk["static_methods"]:
            report.error(line, "TenjinSDK has no static method `%s`" % name)
            continue
        count = len(split_args(args))
        if count not in sdk["static_methods"][name]:
            report.error(line, "TenjinSDK.%s takes %s argument(s), the guide passes %d"
                         % (name, " or ".join(map(str, sdk["static_methods"][name])), count))
        else:
            report.ok()
        if name.startswith("getInstance"):
            chained = chained_use(text, end)
            if chained:
                check_instance_use(chained)

    for receiver in profiles:
        for name, args, block, index, end in member_uses(text, re.escape(receiver)):
            line = start + line_of(code, index)
            if name not in profile["methods"]:
                report.error(line, "UserProfileData has no method `%s`" % name)
            else:
                report.ok()

    for match in re.finditer(r"import\s+(com\.tenjin\.[\w.]+)", strip_comments_only(code)):
        imported = match.group(1)
        known = {name.replace("$", ".") for name in classes}
        if imported not in known and not imported.endswith(".*"):
            report.error(start + line_of(code, match.start()), "import `%s`: no such class in the Tenjin Android SDK" % imported)
        else:
            report.ok()

    return {name for name in simple if "." not in name}


# ---------------------------------------------------------------------------
# ios (objective-c, swift)
# ---------------------------------------------------------------------------

def swift_candidates(selector, info):
    """Swift spellings (base, labels) a selector can be called with."""
    candidates = set()
    if "swift_name" in info:
        base, labels = re.match(r"(\w+)\((.*)\)", info["swift_name"]).groups()
        candidates.add((base, tuple(label for label in labels.split(":") if label)))
    if ":" not in selector:
        candidates.add((selector, ()))
        return candidates
    parts = selector.split(":")[:-1]
    rest = tuple(part or "_" for part in parts[1:])
    first = parts[0]
    candidates.add((first, ("_",) + rest))
    for index in range(1, len(first)):
        if first[index].isupper():
            base, word = first[:index], first[index:]
            candidates.add((base, (word[0].lower() + word[1:],) + rest))
            # Swift drops "With" before a completion handler:
            # fooWithCompletionHandler: is called as foo(completionHandler:).
            if word in ("WithCompletionHandler", "WithCompletion", "WithHandler", "WithBlock"):
                candidates.add((base, (word[4].lower() + word[5:],) + rest))
    return candidates


def swift_labels(args):
    labels = []
    for arg in split_args(args):
        label = re.match(r"([A-Za-z_]\w*)\s*:", arg)
        labels.append(label.group(1) if label else "_")
    return tuple(labels)


def check_swift(report, start, code, symbols, guide_code):
    text = clean(code)
    selectors = symbols["selectors"]
    profile = symbols["types"].get("TJNUserProfileData", {"properties": [], "selectors": {}})

    index_by_call = {}
    for selector, info in selectors.items():
        for candidate in swift_candidates(selector, info):
            index_by_call.setdefault(candidate, []).append(selector)
    bases = {base for base, _ in index_by_call}

    instances = set(re.findall(
        r"(?:let|var)\s+(\w+)\s*=\s*TenjinSDK\s*\.\s*(?:getInstance|sharedInstance|initialize)\b", guide_code))
    profiles = set(re.findall(r"(?:let|var)\s+(\w+)\s*=\s*TenjinSDK\s*\.\s*getUserProfile\s*\(\s*\)", guide_code))

    def check_use(use, kind):
        name, args, block, index, end = use
        line = start + line_of(code, index)
        if args is None:
            return
        if name not in bases:
            report.error(line, "TenjinSDK has no method `%s` (Swift)" % name)
            return
        labels = swift_labels(args)
        found = list(index_by_call.get((name, labels), []))
        if block:
            for (base, candidate_labels), names in index_by_call.items():
                if base == name and candidate_labels[:-1] == labels and candidate_labels:
                    found.extend(names)
        found = [selector for selector in found if selectors[selector]["kind"] == kind]
        if not found:
            shown = "%s(%s)" % (name, "".join(label + ":" for label in labels))
            report.error(line, "no %s method of TenjinSDK matches the Swift call `%s`"
                         % ("class" if kind == "+" else "instance", shown))
            return
        if all(selectors[selector].get("deprecated") for selector in found):
            report.error(line, "`%s` is deprecated in the SDK header" % found[0])
            return
        report.ok()

    for use in member_uses(text, "TenjinSDK"):
        check_use(use, "+")
        if use[0] in ("sharedInstance", "getInstance", "initialize") and use[1] is not None:
            chained = chained_use(text, use[4])
            if chained:
                check_use(chained, "-")
    if instances:
        for use in member_uses(text, "|".join(sorted(map(re.escape, instances)))):
            check_use(use, "-")

    for receiver in profiles:
        for name, args, block, index, end in member_uses(text, re.escape(receiver)):
            line = start + line_of(code, index)
            if args is None and name not in profile["properties"]:
                report.error(line, "TJNUserProfileData has no property `%s`" % name)
            else:
                report.ok()

    raw = strip_comments_only(code)
    imports = re.findall(r"(?m)^\s*import\s+(\w+)", raw)
    if imports and re.search(r"\bTenjinSDK\s*\.", text) and symbols["module"] not in imports:
        report.error(start, "Swift block uses TenjinSDK and has imports, but not `import %s`" % symbols["module"])


def objc_messages(text):
    """Yield (receiver, selector, index) for each [receiver message] in cleaned code."""
    for index, char in enumerate(text):
        if char != "[" or (index > 0 and text[index - 1] == "@"):
            continue
        close = matching(text, index)
        if close == -1:
            continue
        inner = text[index + 1:close]
        stripped = inner.lstrip()
        if stripped.startswith("["):
            receiver_end = matching(stripped, 0)
            if receiver_end == -1:
                continue
            receiver, rest = stripped[:receiver_end + 1], stripped[receiver_end + 1:]
        else:
            token = re.match(r"[\w.]+", stripped)
            if not token:
                continue
            receiver, rest = token.group(0), stripped[token.end():]

        flat, depth = [], 0
        for item in rest:
            if item in "([{":
                depth += 1
            elif item in ")]}":
                depth -= 1
            elif depth == 0:
                flat.append(item)
        flat = "".join(flat)
        parts = re.findall(r"(\w*):", flat)
        if parts:
            selector = "".join(part + ":" for part in parts)
        else:
            word = re.match(r"\s*(\w+)", flat)
            if not word:
                continue
            selector = word.group(1)
        yield " ".join(receiver.split()), selector, index


def check_objc(report, start, code, symbols, guide_code):
    text = clean(code)
    selectors = symbols["selectors"]
    instances = set(re.findall(r"TenjinSDK\s*\*\s*(\w+)\s*=", guide_code))

    for receiver, selector, index in objc_messages(text):
        line = start + line_of(code, index)
        if receiver == "TenjinSDK":
            kind = "+"
        elif re.match(r"\[TenjinSDK (sharedInstance|getInstance|initialize)\b", receiver) or receiver in instances:
            kind = "-"
        else:
            continue
        info = selectors.get(selector)
        if info is None:
            report.error(line, "TenjinSDK has no selector `%s`" % selector)
        elif info["kind"] != kind:
            report.error(line, "`%s` is %s method, the guide calls it on %s"
                         % (selector, "a class" if info["kind"] == "+" else "an instance",
                            "the class" if kind == "+" else "an instance"))
        elif info.get("deprecated"):
            report.error(line, "`%s` is deprecated in the SDK header" % selector)
        else:
            report.ok()


# ---------------------------------------------------------------------------
# flutter (dart)
# ---------------------------------------------------------------------------

def check_dart(report, start, code, symbols, guide_code):
    text = clean(code)
    methods = symbols["methods"]

    for match in re.finditer(r"package:%s/([\w./]+)" % symbols["package"], strip_comments_only(code)):
        if match.group(1) not in symbols["lib_files"]:
            report.error(start + line_of(code, match.start()),
                         "`package:%s/%s` does not exist; the package has: %s"
                         % (symbols["package"], match.group(1), ", ".join(symbols["lib_files"])))
        else:
            report.ok()

    for name, args, block, index, end in member_uses(text, symbols["class"]):
        if name not in symbols["static_members"]:
            report.error(start + line_of(code, index),
                         "`%s.%s`: the class has no static member `%s`; call methods on `%s.instance`"
                         % (symbols["class"], name, name, symbols["class"]))

    variables = set(re.findall(r"(\w+)\s*=\s*%s\s*\.\s*instance\b" % symbols["class"], guide_code))
    receivers = [r"%s\s*\.\s*instance" % symbols["class"]] + sorted(map(re.escape, variables))
    for name, args, block, index, end in member_uses(text, "|".join(receivers)):
        line = start + line_of(code, index)
        method = methods.get(name)
        if method is None:
            report.error(line, "%s has no method `%s`" % (symbols["class"], name))
            continue
        if method.get("deprecated"):
            report.error(line, "`%s` is deprecated in the plugin" % name)
            continue
        if args is None:
            report.ok()
            continue
        positional, named = 0, []
        for arg in split_args(args):
            label = re.match(r"([A-Za-z_]\w*)\s*:", arg)
            if label:
                named.append(label.group(1))
            else:
                positional += 1
        problems = []
        if positional != method["positional"]:
            problems.append("takes %d positional argument(s), the guide passes %d" % (method["positional"], positional))
        unknown = [label for label in named if label not in method["named"]]
        if unknown:
            problems.append("has no named parameter %s" % ", ".join("`%s`" % label for label in unknown))
        missing = [label for label, info in method["named"].items() if info["required"] and label not in named]
        if missing:
            problems.append("requires %s" % ", ".join("`%s`" % label for label in missing))
        if problems:
            report.error(line, "%s.%s %s" % (symbols["class"], name, "; ".join(problems)))
        else:
            report.ok()


# ---------------------------------------------------------------------------
# react-native and ionic (javascript, typescript)
# ---------------------------------------------------------------------------

def check_js_import(report, start, code, symbols, export_name):
    raw = strip_comments_only(code)
    for match in re.finditer(r"import\s+([^;'\"]+?)\s+from\s+['\"]%s['\"]" % re.escape(symbols["package"]), raw):
        clause = match.group(1).strip()
        line = start + line_of(code, match.start())
        default = re.match(r"[\w$]+", clause)
        named = re.search(r"\{([^}]*)\}", clause)
        if default and not symbols["default_export"]:
            report.error(line, "`%s` has no default export; use `import { %s } from '%s'`"
                         % (symbols["package"], export_name, symbols["package"]))
        elif named and "named_exports" in symbols:
            wanted = [item.strip().split(" ")[0] for item in named.group(1).split(",") if item.strip()]
            unknown = [item for item in wanted if item not in symbols["named_exports"] and item != "type"]
            if unknown:
                report.error(line, "`%s` does not export %s" % (symbols["package"], ", ".join(unknown)))
            else:
                report.ok()
        elif named and symbols["default_export"] and not default:
            report.error(line, "`%s` is a default export; use `import %s from '%s'`"
                         % (export_name, export_name, symbols["package"]))
        else:
            report.ok()


def check_object_arg(report, line, label, arg, allowed):
    keys = object_keys(arg)
    if keys is None:
        return True
    unknown = [key for key in keys if key not in allowed]
    missing = [key for key, info in allowed.items() if info["required"] and key not in keys]
    if unknown:
        report.error(line, "%s has no option %s" % (label, ", ".join("`%s`" % key for key in unknown)))
    if missing:
        report.error(line, "%s requires %s" % (label, ", ".join("`%s`" % key for key in missing)))
    return not (unknown or missing)


def check_react_native(report, start, code, symbols, guide_code):
    text = clean(code)
    check_js_import(report, start, code, symbols, "Tenjin")
    for name, args, block, index, end in member_uses(text, "Tenjin"):
        line = start + line_of(code, index)
        method = symbols["methods"].get(name)
        if method is None:
            report.error(line, "Tenjin has no method `%s`" % name)
            continue
        if args is None:
            report.ok()
            continue
        values = split_args(args)
        if not method["required"] <= len(values) <= len(method["params"]):
            expected = (str(method["required"]) if method["required"] == len(method["params"])
                        else "%d to %d" % (method["required"], len(method["params"])))
            report.error(line, "Tenjin.%s takes %s argument(s), the guide passes %d" % (name, expected, len(values)))
            continue
        if name in symbols["object_params"] and values and values[0].startswith("{"):
            if not check_object_arg(report, line, "Tenjin.%s" % name, values[0], symbols["object_params"][name]):
                continue
        report.ok()


def check_ionic(report, start, code, symbols, guide_code):
    text = clean(code)
    check_js_import(report, start, code, symbols, "Tenjin")
    for name, args, block, index, end in member_uses(text, "Tenjin"):
        line = start + line_of(code, index)
        method = symbols["methods"].get(name)
        if method is None:
            report.error(line, "Tenjin has no method `%s`" % name)
            continue
        if args is None:
            report.ok()
            continue
        values = split_args(args)
        expected = 0 if method["options"] is None else 1
        if len(values) != expected:
            report.error(line, "Tenjin.%s takes %s, the guide passes %d argument(s)"
                         % (name, "no arguments" if expected == 0 else "one options object", len(values)))
            continue
        if values and re.match(r"[\"'`\d\[]", values[0]):
            report.error(line, "Tenjin.%s takes one options object, the guide passes a bare value" % name)
            continue
        if values and values[0].startswith("{"):
            if not check_object_arg(report, line, "Tenjin.%s" % name, values[0], method["options"]):
                continue
        report.ok()


# ---------------------------------------------------------------------------
# unity (c#, json)
# ---------------------------------------------------------------------------

def check_csharp(report, start, code, symbols, guide_code):
    text = clean(code)
    base = symbols["BaseTenjin"]
    tenjin = symbols["Tenjin"]

    receivers = {"instance"} | set(re.findall(r"\bBaseTenjin\s+(\w+)\s*[=;]", guide_code))

    def check_instance_use(use):
        name, args, block, index, end = use
        line = start + line_of(code, index)
        if name not in base["methods"]:
            if args is None and name in base["properties"]:
                report.ok()
            else:
                report.error(line, "BaseTenjin has no method `%s`" % name)
            return
        if args is None:
            report.error(line, "`%s` is a method; call it with parentheses" % name)
            return
        count = len(split_args(args))
        if count not in base["methods"][name]:
            report.error(line, "BaseTenjin.%s takes %s argument(s), the guide passes %d"
                         % (name, " or ".join(map(str, base["methods"][name])), count))
        else:
            report.ok()

    for use in member_uses(text, "|".join(sorted(map(re.escape, receivers)))):
        check_instance_use(use)

    for name, args, block, index, end in member_uses(text, "Tenjin"):
        line = start + line_of(code, index)
        if args is None:
            if name in tenjin["nested_types"] or name in tenjin["static_fields"]:
                report.ok()
            else:
                report.error(line, "Tenjin has no member `%s`" % name)
            continue
        if name not in tenjin["static_methods"]:
            report.error(line, "Tenjin has no static method `%s`" % name)
            continue
        count = len(split_args(args))
        if count not in tenjin["static_methods"][name]:
            report.error(line, "Tenjin.%s takes %s argument(s), the guide passes %d"
                         % (name, " or ".join(map(str, tenjin["static_methods"][name])), count))
        else:
            report.ok()
        chained = chained_use(text, end)
        if chained:
            check_instance_use(chained)

    for name, args, block, index, end in member_uses(text, "AppStoreType"):
        if name not in symbols["AppStoreType"]:
            report.error(start + line_of(code, index), "AppStoreType has no value `%s`" % name)
        else:
            report.ok()

    for name, args, block, index, end in member_uses(text, "TenjinObject"):
        if name not in symbols["TenjinObject"]["static_properties"]:
            report.error(start + line_of(code, index), "TenjinObject has no static member `%s`" % name)
        else:
            report.ok()


def check_unity_json(report, start, code, symbols):
    for match in re.finditer(r"\"(com\.tenjin[\w.-]*)\"\s*:", code):
        if match.group(1) != symbols["package"]:
            report.error(start + line_of(code, match.start()),
                         "manifest key `%s`: the package is named `%s`" % (match.group(1), symbols["package"]))
        else:
            report.ok()


# ---------------------------------------------------------------------------
# the "Full API Reference" tables
# ---------------------------------------------------------------------------

def reference_spans(markdown):
    """Yield (line_number, code_span) for the first column of the API reference tables."""
    inside = False
    for number, line in enumerate(markdown.split("\n"), 1):
        if line.startswith("## "):
            inside = "Full API Reference" in line
            continue
        if not inside or not line.startswith("|") or re.match(r"\|\s*-", line):
            continue
        first = line.split("|")[1]
        for span in re.findall(r"`([^`]+)`", first):
            yield number, span


def check_reference(report, platform, markdown, symbols):
    for line, span in reference_spans(markdown):
        if platform == "ios":
            if not re.match(r"[\w:]+$", span):
                continue
            info = symbols["selectors"].get(span)
            if info is None:
                report.error(line, "API reference: TenjinSDK has no selector `%s`" % span)
            elif info.get("deprecated"):
                report.error(line, "API reference: `%s` is deprecated" % span)
            else:
                report.ok()
            continue

        call = re.match(r"(\w+)\s*\((.*)\)$", span)
        if not call:
            continue
        name, params = call.groups()
        listed = None if "..." in params else len(split_args(params))

        if platform == "android":
            sdk = symbols["classes"]["com.tenjin.android.TenjinSDK"]
            arities = sdk["methods"].get(name, []) + sdk["static_methods"].get(name, [])
        elif platform == "unity":
            arities = symbols["BaseTenjin"]["methods"].get(name, [])
        elif platform == "flutter":
            method = symbols["methods"].get(name)
            if method is None:
                report.error(line, "API reference: no method `%s`" % name)
            elif method.get("deprecated"):
                report.error(line, "API reference: `%s` is deprecated" % name)
            else:
                report.ok()
            continue
        elif platform == "react-native":
            method = symbols["methods"].get(name)
            if method is None:
                report.error(line, "API reference: no method `%s`" % name)
            elif listed is not None and not method["required"] <= listed <= len(method["params"]):
                report.error(line, "API reference: `%s` lists %d parameter(s), the SDK has %d"
                             % (name, listed, len(method["params"])))
            else:
                report.ok()
            continue
        elif platform == "ionic":
            method = symbols["methods"].get(name)
            if method is None:
                report.error(line, "API reference: no method `%s`" % name)
            elif params.strip().startswith("{"):
                check_object_arg(report, line, "API reference: `%s`" % name, params, method["options"] or {})
                report.ok()
            elif params.strip() == "" and method["options"] is not None:
                report.error(line, "API reference: `%s` takes an options object" % name)
            else:
                report.ok()
            continue
        else:
            continue

        if not arities:
            report.error(line, "API reference: no method `%s`" % name)
        elif listed is not None and listed not in arities:
            report.error(line, "API reference: `%s` lists %d parameter(s), the SDK has %s"
                         % (name, listed, " or ".join(map(str, sorted(set(arities))))))
        else:
            report.ok()


# ---------------------------------------------------------------------------
# guide-level checks
# ---------------------------------------------------------------------------

def expected_facts(platform, symbols):
    if platform == "android":
        return ["API %d" % symbols["min_sdk"]]
    if platform == "ios":
        return ["**Minimum iOS:** %s" % symbols["min_ios"]]
    if platform == "flutter":
        return ["iOS %s+" % symbols["min_ios"], "Android API %d+" % symbols["min_sdk"]]
    if platform == "ionic":
        return ["Capacitor %s" % symbols["peer_dependencies"]["@capacitor/core"].replace(">=", ">= "),
                "iOS %s+" % symbols["min_ios"], "Android API %d+" % symbols["min_sdk"]]
    if platform == "unity":
        return ["Unity %s" % symbols["min_unity"], '"%s"' % symbols["package"]]
    return []


def check_text(report, markdown, platform=None, symbols=None):
    lines = markdown.split("\n")
    for number, line in enumerate(lines, 1):
        for pattern, message in VERSION_PINS:
            if re.search(pattern, line):
                report.error(number, "%s: %s" % (message, line.strip()))
        if POSSIBLE_KEY.search(line):
            report.error(number, "looks like a real SDK key; use a placeholder: %s" % line.strip())

    if platform is None:
        return
    headings = [line for line in lines if line.startswith("#")]
    for pattern in REQUIRED_HEADINGS:
        if not any(re.search(pattern, heading) for heading in headings):
            report.error(1, "missing required section matching /%s/" % pattern)
    if VERSION_LOOKUP[platform] not in markdown:
        report.error(1, "the guide does not give the version lookup `%s`" % VERSION_LOOKUP[platform])
    for fact in expected_facts(platform, symbols):
        if fact not in markdown:
            report.error(1, "expected the guide to state `%s` (from sdk-symbols/%s.json)" % (fact, platform))


DECLARATION = re.compile(
    r"\b(?:class|struct|enum|interface|object|func|fun|void|function|const|let|var|val|string)\s+(Tenjin\w*)")


def check_guide(platform, markdown, all_symbols, path="<guide>"):
    report = Report(path)
    symbols = all_symbols[platform]
    blocks = [(LANGUAGES.get(language), start, code) for language, start, code in code_blocks(markdown)]
    by_language = {}
    for language, start, code in blocks:
        if language:
            by_language.setdefault(language, []).append(clean(code))

    def guide_code(*languages):
        return "\n".join(code for language in languages for code in by_language.get(language, []))

    known_types = set()
    for language, start, code in blocks:
        if language in ("java", "kotlin"):
            known_types |= check_android(report, start, code, all_symbols["android"], guide_code("java", "kotlin")) or set()
        elif language == "swift":
            check_swift(report, start, code, all_symbols["ios"], guide_code("swift"))
        elif language == "objc":
            check_objc(report, start, code, all_symbols["ios"], guide_code("objc"))
        elif language == "dart":
            check_dart(report, start, code, all_symbols["flutter"], guide_code("dart"))
        elif language == "csharp":
            check_csharp(report, start, code, all_symbols["unity"], guide_code("csharp"))
        elif language == "js" and platform == "react-native":
            check_react_native(report, start, code, symbols, guide_code("js"))
        elif language == "js" and platform == "ionic":
            check_ionic(report, start, code, symbols, guide_code("js"))
        elif language == "json" and platform == "unity":
            check_unity_json(report, start, code, symbols)

    # Any Tenjin-prefixed type in Java/Kotlin code must be an SDK class or declared in the guide.
    declared = set(DECLARATION.findall(guide_code("java", "kotlin")))
    for language, start, code in blocks:
        if language not in ("java", "kotlin"):
            continue
        text = clean(code)
        for match in re.finditer(r"\bTenjin[A-Z]\w*\b", text):
            if match.group(0) not in known_types and match.group(0) not in declared:
                report.error(start + line_of(code, match.start()),
                             "`%s` is not a type of the Tenjin Android SDK" % match.group(0))

    check_reference(report, platform, markdown, symbols)
    check_text(report, markdown, platform, symbols)
    if report.checked == 0:
        report.error(1, "no Tenjin API use was recognised in this guide; the checker may be out of date")
    return report


def main(argv):
    verbose = "-v" in argv or "--verbose" in argv
    all_symbols = load_symbols()
    reports = []

    for platform in PLATFORMS:
        path = os.path.join("guides", platform, "llm-guide.md")
        with open(os.path.join(ROOT, path), encoding="utf-8") as handle:
            reports.append(check_guide(platform, handle.read(), all_symbols, path))

    others = ["guides/llm-guide.md", "llms.txt", "README.md", "AGENTS.md"]
    skills_dir = os.path.join(ROOT, "skills")
    for name in sorted(os.listdir(skills_dir)):
        others.append(os.path.join("skills", name, "SKILL.md"))
    for path in others:
        full = os.path.join(ROOT, path)
        if not os.path.exists(full):
            continue
        report = Report(path)
        with open(full, encoding="utf-8") as handle:
            check_text(report, handle.read())
        reports.append(report)

    failed = 0
    for report in reports:
        for line, message in sorted(report.errors):
            print("%s:%d: %s" % (report.path, line, message))
            failed += 1
        if verbose and report.checked:
            print("%s: %d API uses checked against sdk-symbols (%s %s)" % (
                report.path, report.checked,
                report.path.split("/")[1], all_symbols[report.path.split("/")[1]]["version"]))

    if failed:
        print("\n%d problem(s) found." % failed)
        return 1
    print("OK: %d files checked, %d API uses verified against sdk-symbols/."
          % (len(reports), sum(report.checked for report in reports)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
