#!/usr/bin/env python3
"""Pre-render step: build ``reference/versions.json`` for the per-page version
switcher.

Scans ``reference/<package>/<version>/`` and records, per package, which
component pages (``namespace/name``, no extension) exist in each version. The
switcher script (``reference-versions.html``) reads this at page load to offer
version links for the component currently being viewed, listing only the
versions in which that component actually exists.

Regenerated on every render, so it always matches the folders present. The
reference pages themselves are auto-generated and frozen, which is why the
switcher is driven by this external manifest rather than baked into each page.
"""
import glob
import json
import os
import re

REF = "reference"
VERSION_DIR = re.compile(r"^v?\d+\.\d+")


def version_key(v):
    return [int(x) for x in re.findall(r"\d+", v)]


def main():
    manifest = {}
    if not os.path.isdir(REF):
        return
    for pkg in sorted(os.listdir(REF)):
        pkg_dir = os.path.join(REF, pkg)
        if not os.path.isdir(pkg_dir):
            continue
        versions = {}
        for ver in os.listdir(pkg_dir):
            vdir = os.path.join(pkg_dir, ver)
            if not os.path.isdir(vdir) or not VERSION_DIR.match(ver):
                continue
            comps = []
            for f in glob.glob(os.path.join(vdir, "**", "*.qmd"), recursive=True):
                rel = os.path.relpath(f, vdir)[:-4]  # strip ".qmd"
                if os.path.basename(rel) == "index":
                    continue
                comps.append(rel)
            if comps:
                versions[ver] = sorted(comps)
        if not versions:
            continue
        latest = sorted(versions.keys(), key=version_key)[-1]
        manifest[pkg] = {"latest": latest, "versions": versions}
    with open(os.path.join(REF, "versions.json"), "w", encoding="utf-8") as fh:
        json.dump(manifest, fh)
    print(f"wrote {REF}/versions.json for {len(manifest)} package(s)")


if __name__ == "__main__":
    main()
