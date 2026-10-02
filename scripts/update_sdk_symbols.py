#!/usr/bin/env python3
"""Regenerate sdk-symbols/*.json from the public Tenjin SDK distributions.

Each file lists the public API of the newest published SDK for one platform.
scripts/check_guides.py compares the guides against these files, so CI never
needs network access or anything that is not public.

Sources (all public):
  android       Maven Central   com.tenjin:android-sdk (.aar, class files)
  ios           GitHub          tenjin/tenjin-ios-sdk at the newest CocoaPods version (headers)
  flutter       pub.dev         tenjin_plugin (Dart source)
  react-native  npm             react-native-tenjin (type definitions)
  ionic         npm             ionic-capacitor-tenjin (type definitions)
  unity         GitHub          tenjin/tenjin-unity-sdk at the newest release tag (C# source)

Usage:
  python3 scripts/update_sdk_symbols.py            # all platforms
  python3 scripts/update_sdk_symbols.py android    # one or more platforms

Standard library only.
"""

import io
import json
import os
import re
import struct
import sys
import tarfile
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(ROOT, "sdk-symbols")


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def fetch(url):
    headers = {"User-Agent": "tenjin-sdk-llm-guides-symbols"}
    token = os.environ.get("GITHUB_TOKEN")
    if token and url.startswith("https://api.github.com/"):
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read()


def fetch_text(url):
    return fetch(url).decode("utf-8", "replace")


def fetch_json(url):
    return json.loads(fetch_text(url))


def version_key(version):
    return [int(part) for part in re.findall(r"\d+", version)]


def strip_comments(text):
    """Remove // and /* */ comments. Good enough for headers and declarations."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return re.sub(r"(?m)//.*$", "", text)


def matching(text, start, open_char, close_char):
    """Index of the bracket that closes the one at text[start]."""
    depth = 0
    for index in range(start, len(text)):
        char = text[index]
        if char == open_char:
            depth += 1
        elif char == close_char:
            depth -= 1
            if depth == 0:
                return index
    raise ValueError("unbalanced %s%s" % (open_char, close_char))


def split_top_level(text, separator=","):
    """Split on a separator that is not inside (), [], {} or <>."""
    parts, depth, current = [], 0, []
    previous = ""
    for char in text:
        if char in "([{<":
            depth += 1
        elif char in ")]}":
            depth -= 1
        elif char == ">" and previous != "=":
            depth -= 1
        if char == separator and depth == 0:
            parts.append("".join(current))
            current = []
        else:
            current.append(char)
        previous = char
    parts.append("".join(current))
    return [part.strip() for part in parts if part.strip()]


def npm_package(name):
    """Return (version, {path: text}) for the newest version of an npm package."""
    meta = fetch_json("https://registry.npmjs.org/%s/latest" % name)
    archive = tarfile.open(fileobj=io.BytesIO(fetch(meta["dist"]["tarball"])), mode="r:gz")
    files = {}
    for member in archive.getmembers():
        if member.isfile() and member.name.endswith((".ts", ".json", ".gradle", ".podspec")):
            files[member.name.split("/", 1)[1]] = archive.extractfile(member).read().decode("utf-8", "replace")
    return meta["version"], meta["dist"]["tarball"], files


def interface_body(text, name):
    match = re.search(r"interface\s+%s\b[^{]*\{" % re.escape(name), text)
    if not match:
        raise ValueError("interface %s not found" % name)
    start = match.end() - 1
    return text[start + 1:matching(text, start, "{", "}")]


def ts_members(body):
    """Parse the members of a TypeScript interface body."""
    members = {}
    for chunk in split_top_level(strip_comments(body), ";"):
        method = re.match(r"(\w+)\s*\(", chunk)
        if method:
            open_index = chunk.index("(")
            params = split_top_level(chunk[open_index + 1:matching(chunk, open_index, "(", ")")])
            parsed = []
            for param in params:
                param_match = re.match(r"(\w+)\s*(\?)?\s*:\s*(.*)", param, flags=re.S)
                parsed.append({
                    "name": param_match.group(1),
                    "optional": bool(param_match.group(2)),
                    "type": " ".join(param_match.group(3).split()),
                })
            members[method.group(1)] = {"kind": "method", "params": parsed}
            continue
        prop = re.match(r"(\w+)\s*(\?)?\s*:", chunk)
        if prop:
            members[prop.group(1)] = {"kind": "property", "optional": bool(prop.group(2))}
    return members


# ---------------------------------------------------------------------------
# android: class files inside the .aar
# ---------------------------------------------------------------------------

ACC_PUBLIC, ACC_STATIC, ACC_BRIDGE, ACC_SYNTHETIC = 0x0001, 0x0008, 0x0040, 0x1000


def parse_class_file(data):
    position = 8
    (count,) = struct.unpack_from(">H", data, position)
    position += 2
    pool = [None] * count
    index = 1
    while index < count:
        tag = data[position]
        position += 1
        if tag == 1:
            (length,) = struct.unpack_from(">H", data, position)
            position += 2
            pool[index] = data[position:position + length].decode("utf-8", "replace")
            position += length
        elif tag in (3, 4):
            position += 4
        elif tag in (5, 6):
            position += 8
            index += 1
        elif tag == 7:
            pool[index] = struct.unpack_from(">H", data, position)[0]
            position += 2
        elif tag in (8, 16, 19, 20):
            position += 2
        elif tag in (9, 10, 11, 12, 17, 18):
            position += 4
        elif tag == 15:
            position += 3
        else:
            raise ValueError("unknown constant pool tag %d" % tag)
        index += 1

    access, this_class, _super, interface_count = struct.unpack_from(">HHHH", data, position)
    position += 8 + 2 * interface_count

    def read_members(position):
        (member_count,) = struct.unpack_from(">H", data, position)
        position += 2
        members = []
        for _ in range(member_count):
            flags, name_index, descriptor_index, attribute_count = struct.unpack_from(">HHHH", data, position)
            position += 8
            for _ in range(attribute_count):
                (length,) = struct.unpack_from(">I", data, position + 2)
                position += 6 + length
            members.append((flags, pool[name_index], pool[descriptor_index]))
        return members, position

    fields, position = read_members(position)
    methods, position = read_members(position)
    return {
        "name": pool[pool[this_class]].replace("/", "."),
        "public": bool(access & ACC_PUBLIC),
        "fields": fields,
        "methods": methods,
    }


def descriptor_arity(descriptor):
    params = descriptor[1:descriptor.index(")")]
    count, index = 0, 0
    while index < len(params):
        while params[index] == "[":
            index += 1
        if params[index] == "L":
            index = params.index(";", index)
        index += 1
        count += 1
    return count


def android():
    metadata = fetch_text("https://repo1.maven.org/maven2/com/tenjin/android-sdk/maven-metadata.xml")
    version = re.search(r"<release>(.*?)</release>", metadata).group(1)
    url = "https://repo1.maven.org/maven2/com/tenjin/android-sdk/%s/android-sdk-%s.aar" % (version, version)
    aar = zipfile.ZipFile(io.BytesIO(fetch(url)))
    manifest = aar.read("AndroidManifest.xml").decode("utf-8", "replace")
    jar = zipfile.ZipFile(io.BytesIO(aar.read("classes.jar")))

    classes = {}
    for entry in sorted(jar.namelist()):
        if not (entry.startswith("com/tenjin/android/") and entry.endswith(".class")):
            continue
        parsed = parse_class_file(jar.read(entry))
        if not parsed["public"]:
            continue
        methods, static_methods = {}, {}
        for flags, name, descriptor in parsed["methods"]:
            if not flags & ACC_PUBLIC or flags & (ACC_BRIDGE | ACC_SYNTHETIC):
                continue
            if name.startswith("<") or "$" in name:
                continue
            target = static_methods if flags & ACC_STATIC else methods
            arities = target.setdefault(name, [])
            arity = descriptor_arity(descriptor)
            if arity not in arities:
                arities.append(arity)
                arities.sort()
        fields = sorted(name for flags, name, _ in parsed["fields"]
                        if flags & ACC_PUBLIC and "$" not in name)
        classes[parsed["name"]] = {
            "methods": dict(sorted(methods.items())),
            "static_methods": dict(sorted(static_methods.items())),
            "fields": fields,
        }

    return {
        "platform": "android",
        "package": "com.tenjin:android-sdk",
        "version": version,
        "generated_from": [url],
        "min_sdk": int(re.search(r'minSdkVersion="(\d+)"', manifest).group(1)),
        "classes": classes,
    }


# ---------------------------------------------------------------------------
# ios: Objective-C headers
# ---------------------------------------------------------------------------

def collapse_parens(text):
    """Replace every top-level (...) group with a marker so types cannot confuse parsing."""
    out, depth = [], 0
    for char in text:
        if char == "(":
            if depth == 0:
                out.append("§")
            depth += 1
        elif char == ")":
            depth -= 1
        elif depth == 0:
            out.append(char)
    return "".join(out)


def objc_interfaces(header):
    """Return {class: {"selectors": {...}, "properties": [...]}} for an Objective-C header."""
    header = strip_comments(header)
    header = re.sub(r"SWIFT_CLASS_PROPERTY\((.*?;)\)", r"\1", header)
    interfaces = {}
    for match in re.finditer(r"@interface\s+(\w+)\b(.*?)@end", header, flags=re.S):
        entry = interfaces.setdefault(match.group(1), {"selectors": {}, "properties": []})
        for chunk in match.group(2).split(";"):
            chunk = chunk.strip()
            prop = re.search(r"@property\b.*?(\w+)\s*$", chunk, flags=re.S)
            if prop:
                if prop.group(1) not in entry["properties"]:
                    entry["properties"].append(prop.group(1))
                continue
            start = re.search(r"(?m)^\s*([+-])\s*\(", chunk)
            if not start:
                continue
            declaration = chunk[start.start():].strip()
            kind = declaration[0]
            collapsed = collapse_parens(declaration[1:]).lstrip("§ \t\n")
            parts = re.findall(r"(\w*):§", collapsed)
            if parts:
                selector = "".join(part + ":" for part in parts)
            else:
                selector = re.match(r"\w+", collapsed).group(0)
            info = {"kind": kind}
            if re.search(r"deprecated|NS_UNAVAILABLE|SWIFT_UNAVAILABLE", declaration):
                info["deprecated"] = True
            swift_name = re.search(r"NS_SWIFT_NAME\((\w+\([^)]*\))\)", declaration)
            if swift_name:
                info["swift_name"] = swift_name.group(1)
            available = re.search(r"API_AVAILABLE\(ios\(([\d.]+)\)\)", declaration)
            if available:
                info["ios"] = available.group(1)
            entry["selectors"][selector] = info
    return interfaces


def ios():
    pod = fetch_json("https://trunk.cocoapods.org/api/v1/pods/TenjinSDK")
    version = max((item["name"] for item in pod["versions"]), key=version_key)
    base = "https://raw.githubusercontent.com/tenjin/tenjin-ios-sdk/%s/" % version
    header_url = base + "TenjinSDK.h"
    swift_header_url = base + "TenjinSDK.xcframework/ios-arm64/TenjinSDK.framework/Headers/TenjinSDK-Swift.h"
    podspec_url = base + "TenjinSDK.podspec"

    main = objc_interfaces(fetch_text(header_url))
    swift = objc_interfaces(fetch_text(swift_header_url))
    podspec = fetch_text(podspec_url)

    types = {}
    for name in ("TJNUserProfileData", "TenjinPurchasesManager"):
        if name in swift:
            types[name] = {
                "properties": sorted(swift[name]["properties"]),
                "selectors": dict(sorted(swift[name]["selectors"].items())),
            }

    return {
        "platform": "ios",
        "package": "TenjinSDK",
        "version": version,
        "generated_from": [header_url, swift_header_url, podspec_url],
        "min_ios": re.search(r's\.platform\s*=\s*:ios,\s*"([\d.]+)"', podspec).group(1),
        "module": "TenjinSDK",
        "selectors": dict(sorted(main["TenjinSDK"]["selectors"].items())),
        "types": types,
    }


# ---------------------------------------------------------------------------
# flutter: Dart source
# ---------------------------------------------------------------------------

def dart_class_methods(source, class_name):
    start = re.search(r"class\s+%s\b[^{]*\{" % re.escape(class_name), source).end() - 1
    body = strip_comments(source[start + 1:matching(source, start, "{", "}")])

    heads, current, index, parens = [], [], 0, 0
    while index < len(body):
        char = body[index]
        if char == "(":
            parens += 1
        elif char == ")":
            parens -= 1
        if parens == 0 and char == "{":
            heads.append("".join(current))
            current = []
            index = matching(body, index, "{", "}") + 1
            continue
        if parens == 0 and body.startswith("=>", index):
            heads.append("".join(current))
            current = []
            index = body.index(";", index) + 1
            continue
        if parens == 0 and char == ";":
            current = []
            index += 1
            continue
        current.append(char)
        index += 1

    methods = {}
    for head in heads:
        deprecated = "@Deprecated" in head or "@deprecated" in head
        head = re.sub(r"@\w+(\((?:[^()]|\([^()]*\))*\))?", "", head).strip()
        if "(" not in head or "=" in head.split("(", 1)[0]:
            continue
        name = re.search(r"([\w.]+)\s*\($", head.split("(", 1)[0] + "(").group(1)
        if name.startswith("_") or "." in name or name == class_name:
            continue
        open_index = head.index("(")
        params = head[open_index + 1:matching(head, open_index, "(", ")")]
        named, positional = {}, 0
        brace = params.find("{")
        if brace != -1:
            named_text = params[brace + 1:matching(params, brace, "{", "}")]
            for item in split_top_level(named_text):
                named[re.search(r"(\w+)\s*(?:=.*)?$", item, flags=re.S).group(1)] = {
                    "required": item.startswith("required "),
                }
            params = params[:brace]
        positional = len(split_top_level(params))
        entry = {"positional": positional, "named": named}
        if deprecated:
            entry["deprecated"] = True
        methods[name] = entry
    return dict(sorted(methods.items()))


def flutter():
    meta = fetch_json("https://pub.dev/api/packages/tenjin_plugin")["latest"]
    version, url = meta["version"], meta["archive_url"]
    archive = tarfile.open(fileobj=io.BytesIO(fetch(url)), mode="r:gz")
    files = {member.name.lstrip("./"): archive.extractfile(member).read().decode("utf-8", "replace")
             for member in archive.getmembers()
             if member.isfile() and member.name.lstrip("./").endswith((".dart", ".podspec", ".gradle"))
             and not member.name.lstrip("./").startswith("example/")}

    lib_files = sorted(name[len("lib/"):] for name in files if name.startswith("lib/"))
    podspec = next(text for name, text in files.items() if name.startswith("ios/") and name.endswith(".podspec"))
    gradle = files.get("android/build.gradle", "")
    min_sdk = re.search(r"minSdk(?:Version)?\s*=?\s*(\d+)", gradle)

    return {
        "platform": "flutter",
        "package": "tenjin_plugin",
        "version": version,
        "generated_from": [url],
        "lib_files": lib_files,
        "min_ios": re.search(r"s\.platform\s*=\s*:ios,\s*'([\d.]+)'", podspec).group(1),
        "min_sdk": int(min_sdk.group(1)) if min_sdk else None,
        "class": "TenjinSDK",
        "static_members": ["instance"],
        "methods": dart_class_methods(files["lib/tenjin_sdk.dart"], "TenjinSDK"),
    }


# ---------------------------------------------------------------------------
# react-native and ionic: TypeScript definitions from npm
# ---------------------------------------------------------------------------

def react_native():
    version, url, files = npm_package("react-native-tenjin")
    package = json.loads(files["package.json"])
    types_path = package["types"].lstrip("./")
    index = files[types_path]
    subscription = files[os.path.join(os.path.dirname(types_path), "subscription.d.ts")]

    methods = {}
    for name, member in ts_members(interface_body(index, "TenjinSDK")).items():
        if member["kind"] != "method":
            continue
        params = member["params"]
        methods[name] = {
            "params": [param["name"] for param in params],
            "required": sum(1 for param in params if not param["optional"]),
        }

    subscription_params = {name: {"required": not member.get("optional", False)}
                           for name, member in ts_members(interface_body(subscription, "SubscriptionParams")).items()}

    return {
        "platform": "react-native",
        "package": "react-native-tenjin",
        "version": version,
        "generated_from": [url],
        "default_export": bool(re.search(r"export default\b", index)),
        "methods": dict(sorted(methods.items())),
        "object_params": {"subscription": dict(sorted(subscription_params.items()))},
    }


def ionic():
    version, url, files = npm_package("ionic-capacitor-tenjin")
    package = json.loads(files["package.json"])
    types_path = package["types"].lstrip("./")
    index = files[types_path]
    definitions = files[os.path.join(os.path.dirname(types_path), "definitions.d.ts")]

    methods = {}
    for name, member in ts_members(interface_body(definitions, "TenjinPlugin")).items():
        if member["kind"] != "method":
            continue
        options = None
        if member["params"]:
            option_type = member["params"][0]["type"]
            keys = {}
            for item in split_top_level(option_type.strip()[1:-1], ";"):
                key = re.match(r"(\w+)\s*(\?)?\s*:", item)
                keys[key.group(1)] = {"required": not key.group(2)}
            options = keys
        methods[name] = {"options": options}

    named_exports = []
    for group in re.findall(r"export\s*\{([^}]*)\}", index):
        named_exports.extend(item.strip() for item in group.split(",") if item.strip())

    podspec = next(text for name, text in files.items() if name.endswith(".podspec"))
    min_sdk = re.search(r"minSdkVersion[^\n]*:\s*(\d+)", files.get("android/build.gradle", ""))

    return {
        "platform": "ionic",
        "package": "ionic-capacitor-tenjin",
        "version": version,
        "generated_from": [url],
        "min_ios": re.search(r"deployment_target\s*=\s*'([\d.]+)'", podspec).group(1),
        "min_sdk": int(min_sdk.group(1)) if min_sdk else None,
        "named_exports": sorted(named_exports),
        "default_export": bool(re.search(r"export default\b", index)),
        "peer_dependencies": package.get("peerDependencies", {}),
        "methods": dict(sorted(methods.items())),
    }


# ---------------------------------------------------------------------------
# unity: C# source
# ---------------------------------------------------------------------------

def csharp_methods(source, pattern):
    methods = {}
    text = strip_comments(source)
    for match in re.finditer(pattern, text):
        name = match.group(1)
        open_index = match.end() - 1
        params = text[open_index + 1:matching(text, open_index, "(", ")")]
        arities = methods.setdefault(name, [])
        arity = len(split_top_level(params))
        if arity not in arities:
            arities.append(arity)
            arities.sort()
    return dict(sorted(methods.items()))


def unity():
    release = fetch_json("https://api.github.com/repos/tenjin/tenjin-unity-sdk/releases/latest")
    version = release["tag_name"]
    base = "https://raw.githubusercontent.com/tenjin/tenjin-unity-sdk/%s/" % version
    paths = ["package.json", "Runtime/BaseTenjin.cs", "Runtime/Tenjin.cs",
             "Runtime/AppStoreType.cs", "Runtime/TenjinObject.cs"]
    files = {path: fetch_text(base + path) for path in paths}
    package = json.loads(files["package.json"])

    base_tenjin = strip_comments(files["Runtime/BaseTenjin.cs"])
    tenjin = strip_comments(files["Runtime/Tenjin.cs"])
    tenjin_object = strip_comments(files["Runtime/TenjinObject.cs"])
    enum_body = re.search(r"enum\s+AppStoreType\s*\{(.*?)\}", strip_comments(files["Runtime/AppStoreType.cs"]), flags=re.S).group(1)

    return {
        "platform": "unity",
        "package": package["name"],
        "version": version,
        "generated_from": [base + path for path in paths],
        "min_unity": package.get("unity"),
        "BaseTenjin": {
            "methods": csharp_methods(files["Runtime/BaseTenjin.cs"],
                                      r"public\s+abstract\s+[\w<>, .\[\]]+?\s+(\w+)\s*\("),
            "properties": sorted(set(re.findall(r"public\s+\w+\s+(\w+)\s*(?:\{|$)", base_tenjin, flags=re.M))),
        },
        "Tenjin": {
            "static_methods": csharp_methods(files["Runtime/Tenjin.cs"],
                                             r"public\s+static\s+[\w<>, .\[\]]+?\s+(\w+)\s*\("),
            "nested_types": sorted(re.findall(r"public\s+delegate\s+\w+\s+(\w+)\s*\(", tenjin)),
            "static_fields": sorted(re.findall(r"public\s+static\s+[\w<>]+\s+(\w+)\s*=", tenjin)),
        },
        "AppStoreType": sorted(item.strip() for item in enum_body.split(",") if item.strip()),
        "TenjinObject": {
            "fields": sorted(re.findall(r"public\s+(?!static|class|void)[\w<>]+\s+(\w+)\s*(?:=[^;]*)?;", tenjin_object)),
            "methods": csharp_methods(files["Runtime/TenjinObject.cs"],
                                      r"public\s+(?!static|class)[\w<>]+\s+(\w+)\s*\("),
            "static_properties": sorted(re.findall(r"public\s+static\s+\w+\s+(\w+)\s*$", tenjin_object, flags=re.M)),
        },
    }


# ---------------------------------------------------------------------------

PLATFORMS = {
    "android": android,
    "ios": ios,
    "flutter": flutter,
    "react-native": react_native,
    "ionic": ionic,
    "unity": unity,
}


def main(argv):
    names = argv[1:] or list(PLATFORMS)
    unknown = [name for name in names if name not in PLATFORMS]
    if unknown:
        print("unknown platform(s): %s" % ", ".join(unknown), file=sys.stderr)
        return 2
    os.makedirs(OUT_DIR, exist_ok=True)
    for name in names:
        data = PLATFORMS[name]()
        path = os.path.join(OUT_DIR, name + ".json")
        with open(path, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=2, sort_keys=False)
            handle.write("\n")
        print("%-13s %-8s -> %s" % (name, data["version"], os.path.relpath(path, ROOT)))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
