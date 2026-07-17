#!/usr/bin/env python3
"""Move the "Example commands" section to the bottom of each reference page.

The generator emits sections in the order Info/Links, Example commands,
Argument groups, Authors (plus Visualisation on workflows). We want the run
instructions last, so the page leads with what a component *is* and *does*.

Idempotent: re-running leaves an already-last section in place.

Usage: python3 scripts/reorder_sections.py [path ...]   (default: reference)
"""

import glob
import os
import re
import sys

# The "## Example commands" section: from its heading up to the next level-2
# heading (not level-3 subsections like "### Run command") or end of file.
SECTION_RE = re.compile(r'(?m)^## Example commands\b.*?(?=\n## |\Z)', re.S)


def reorder(txt):
    m = SECTION_RE.search(txt)
    if not m:
        return txt
    block = txt[m.start():m.end()].rstrip()
    txt = txt[:m.start()] + txt[m.end():]
    return txt.rstrip() + "\n\n" + block + "\n"


def process_file(path):
    txt = open(path, encoding="utf-8").read()
    new = reorder(txt)
    if new == txt:
        return False
    open(path, "w", encoding="utf-8").write(new)
    return True


def main(argv):
    targets = argv[1:] or ["reference"]
    n = 0
    for t in targets:
        files = [t] if t.endswith(".qmd") else glob.glob(f"{t}/**/*.qmd", recursive=True)
        for f in files:
            if os.path.basename(f) != "index.qmd" and process_file(f):
                n += 1
    print(f"[reorder] moved Example commands to bottom in {n} files")


if __name__ == "__main__":
    main(sys.argv)
