#!/usr/bin/env python3
"""Write the "Run command" section of reference pages.

The generator's params.yaml example is empty, so the section instead points to
the places that explain how to make one (Viash Hub's form, the guides, the
param_list guide), then gives the local launch command and
a note on other backends and platforms. Used by the reference workflow's
post-processing step; run it directly to rewrite existing pages.

Callout titles go in the `title` attribute, not a `##` heading inside the
callout: the post-processing scripts find sections by their level-2 headings.

Idempotent: re-running rewrites the same section.

Usage: python3 scripts/run_command.py [path ...]   (default: reference)
"""

import glob
import os
import re
import sys

SECTION_RE = re.compile(r'(?m)^### Run command\n.*?(?=\n## |\Z)', re.S)
BASH_RE = re.compile(r'```bash\n.*?\n```', re.S)
VH_RE = re.compile(r'Get run instructions\]\((?P<url>[^)]*)\)')


def run_command_section(bash, vh_component):
    return (
        "### Run command\n\n"
        '::: {.callout-note appearance="simple" title="Create a params.yaml"}\n'
        "The command below reads this component's arguments from a `params.yaml` "
        "file. To create one:\n\n"
        f"- generate it with the form on [Viash Hub]({vh_component});\n"
        "- see examples of using params files in the [guides](/guides/index.qmd);\n"
        "- run several samples in one go with a "
        "[`param_list`](/guides/process-many-samples.qmd).\n"
        ":::\n\n"
        "Run locally with:\n\n"
        + bash + "\n\n"
        '::: {.callout-note appearance="simple" title="Other backends and platforms"}\n'
        "Replace `-profile docker` with `-profile podman` or `-profile singularity` "
        "depending on the desired backend. To run on Seqera Platform or through "
        "Viash Hub, see the [guides](/guides/index.qmd).\n"
        ":::\n"
    )


def replace_run_command(page, vh_component):
    """Rewrite the page's "### Run command" section around its bash block."""
    m = SECTION_RE.search(page)
    if not m:
        return page
    bash = BASH_RE.search(m.group(0))
    if not bash:
        return page
    section = run_command_section(bash.group(0), vh_component)
    rest = page[m.end():]
    if not rest.strip():
        return page[:m.start()] + section
    return page[:m.start()] + section + "\n" + rest.lstrip("\n")


def viash_hub_url(page):
    m = VH_RE.search(page)
    return m.group("url") if m else None


def process(path):
    txt = open(path, encoding="utf-8").read()
    url = viash_hub_url(txt)
    if not url:
        return False
    new = replace_run_command(txt, url)
    if new == txt:
        return False
    open(path, "w", encoding="utf-8").write(new)
    return True


def main(argv):
    targets = argv[1:] or ["reference"]
    n = 0
    for t in targets:
        files = [t] if t.endswith(".qmd") else glob.glob(f"{t}/**/*.qmd", recursive=True)
        for f in sorted(files):
            if os.path.basename(f) != "index.qmd" and process(f):
                n += 1
    print(f"[run-command] rewrote the Run command section of {n} pages")


if __name__ == "__main__":
    main(sys.argv)
