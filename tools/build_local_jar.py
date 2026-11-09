"""Construit le plugin sans Gradle (python standard uniquement) et peut l'installer en local.

    python tools/build_local_jar.py            -> build/local/leonidas-neon-light-<version>.jar
    python tools/build_local_jar.py --install  -> + copie dans le dossier plugins du dernier IntelliJ IDEA

Les métadonnées (id, vendeur, description, notes de version) sont injectées dans plugin.xml
depuis gradle.properties, README.md et CHANGELOG.md, exactement comme le fait Gradle.
Pour le Marketplace, préférer `./gradlew buildPlugin` (zip officiel + vérifications).
"""
import argparse
import glob
import html
import os
import re
import shutil
import sys
import zipfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "src", "main", "resources")
LOCAL_ID = "local.leonidas-neon-light"


def read_properties():
    props = {}
    with open(os.path.join(ROOT, "gradle.properties"), encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                props[k.strip()] = v.strip()
    return props


def inline_md(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"&lt;(/?kbd)&gt;", r"<\1>", text)
    text = text.replace("&amp;gt;", "&gt;").replace("&amp;amp;", "&amp;")
    text = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", text)
    return re.sub(r"`(.+?)`", r"<code>\1</code>", text)


def md_to_html(lines):
    out, in_list = [], False
    for line in lines:
        s = line.strip()
        if s.startswith("- "):
            if not in_list:
                out.append("<ul>")
                in_list = True
            out.append(f"<li>{inline_md(s[2:])}</li>")
            continue
        if in_list:
            out.append("</ul>")
            in_list = False
        if s.startswith("### "):
            out.append(f"<h3>{inline_md(s[4:])}</h3>")
        elif s:
            out.append(f"<p>{inline_md(s)}</p>")
    if in_list:
        out.append("</ul>")
    return "\n".join(out)


def description():
    lines = open(os.path.join(ROOT, "README.md"), encoding="utf-8").read().splitlines()
    start = lines.index("<!-- Plugin description -->")
    end = lines.index("<!-- Plugin description end -->")
    return md_to_html(lines[start + 1:end])


def change_notes(version):
    text = open(os.path.join(ROOT, "CHANGELOG.md"), encoding="utf-8").read()
    m = re.search(rf"^## \[{re.escape(version)}\][^\n]*\n(.*?)(?=^## \[|\Z)", text, re.S | re.M)
    return md_to_html(m.group(1).splitlines()) if m else ""


def plugin_xml(p):
    plugin_id = p["pluginId"]
    if plugin_id.startswith("TODO"):
        print(f"⚠  pluginId non rempli : id local « {LOCAL_ID} » utilisé pour ce jar", file=sys.stderr)
        plugin_id = LOCAL_ID
    until = f' until-build="{p["pluginUntilBuild"]}"' if p.get("pluginUntilBuild") else ""
    vendor_attrs = "".join(
        f' {attr}="{html.escape(p[key])}"'
        for attr, key in (("email", "vendorEmail"), ("url", "vendorUrl"))
        if p.get(key) and not p[key].startswith("TODO")
    )
    meta = f"""    <id>{plugin_id}</id>
    <name>{html.escape(p["pluginName"])}</name>
    <version>{p["pluginVersion"]}</version>
    <vendor{vendor_attrs}>{html.escape(p["vendorName"])}</vendor>
    <idea-version since-build="{p["pluginSinceBuild"]}"{until}/>
    <description><![CDATA[
{description()}
    ]]></description>
    <change-notes><![CDATA[
{change_notes(p["pluginVersion"])}
    ]]></change-notes>
"""
    src = open(os.path.join(RES, "META-INF", "plugin.xml"), encoding="utf-8").read()
    return src.replace("<idea-plugin>\n", "<idea-plugin>\n" + meta, 1)


def build(p):
    out_dir = os.path.join(ROOT, "build", "local")
    os.makedirs(out_dir, exist_ok=True)
    jar = os.path.join(out_dir, f"leonidas-neon-light-{p['pluginVersion']}.jar")
    with zipfile.ZipFile(jar, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("META-INF/plugin.xml", plugin_xml(p))
        for path in glob.glob(os.path.join(RES, "**", "*"), recursive=True):
            rel = os.path.relpath(path, RES).replace(os.sep, "/")
            if os.path.isfile(path) and rel != "META-INF/plugin.xml":
                z.write(path, rel)
    return jar


def install(jar):
    roots = sorted(glob.glob(os.path.join(os.environ["APPDATA"], "JetBrains", "IntelliJIdea*")))
    if not roots:
        sys.exit("Aucun dossier de config IntelliJ IDEA trouvé dans %APPDATA%/JetBrains")
    lib = os.path.join(roots[-1], "plugins", "leonidas-neon-light", "lib")
    shutil.rmtree(os.path.dirname(lib), ignore_errors=True)
    os.makedirs(lib)
    shutil.copy2(jar, lib)
    return lib


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--install", action="store_true", help="installer dans le dernier IntelliJ IDEA (redémarrage requis)")
    args = ap.parse_args()
    props = read_properties()
    jar_path = build(props)
    print("jar :", jar_path)
    todo = [k for k, v in props.items() if v.startswith("TODO")]
    if todo:
        print("Champs encore à remplir avant publication :", ", ".join(todo))
    if args.install:
        print("installé dans :", install(jar_path), "-> redémarrer IntelliJ")
