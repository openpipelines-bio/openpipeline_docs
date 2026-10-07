#!/usr/bin/env python3
"""Render reference "Argument groups" and descriptions from the Viash config.

The Viash generator flattens every description to one line (pipe-table cells
and its one-line frontmatter can't hold line breaks), so markdown lists in
config descriptions arrive as run-on text, and it packs all attributes into one
comma-separated string. This rebuilds both from the resolved config that
viash-hub ships in each tag's target/ folder:

- the frontmatter `description` becomes the first paragraph on one line (for
  the title block and the catalog), and the rest of the description, with its
  markdown intact, goes in a `.ref-description` block at the top of the body;
- "## Argument groups" becomes a three-column grid (Name · Description ·
  Attributes) built from fenced divs, so cells can hold real markdown, with
  each attribute (type, required, default, example, choices, min/max,
  separator) on its own labelled line.

Idempotent: re-running rewrites the same section from the same config.

Usage: python3 scripts/render_arguments.py [path ...]   (default: reference)
"""

import glob
import json
import os
import re
import sys

import yaml

from compose_viz import RAW, fetch

LIST_ITEM = re.compile(r'^\s*([*+-]|\d+[.)])\s')
# The generator titles the section "Argument group" when there is only one.
SECTION_RE = re.compile(r'(?m)^## Argument groups?\b.*?(?=\n## |\Z)', re.S)


def markdown(text):
    """Config description → markdown pandoc renders as written.

    Pandoc only starts a list after a blank line, which config authors often
    leave out ("Alignment by:\\n* a"), so add one where a list begins. An
    unindented line right after a list would be folded into its last item, so
    end the list there with a blank line too.
    """
    lines = (text or "").strip().split("\n")
    out, in_list = [], False
    for ln in lines:
        ln = ln.rstrip()
        prev_text = bool(out) and bool(out[-1].strip())
        if LIST_ITEM.match(ln):
            if prev_text and not in_list:
                out.append("")
            in_list = True
        elif ln and not ln[0].isspace():
            if prev_text and in_list:
                out.append("")
            in_list = False
        out.append(ln)
    return "\n".join(out).strip()


def format_value(v):
    """A config value as inline code: strings quoted, booleans lowercase."""
    if isinstance(v, bool):
        s = "true" if v else "false"
    elif isinstance(v, str):
        s = json.dumps(v, ensure_ascii=False)
    else:
        s = str(v)
    return f"`` {s} ``" if "`" in s else f"`{s}`"


def _values(v):
    vs = v if isinstance(v, list) else [v]
    return ", ".join(format_value(x) for x in vs)


def type_label(arg):
    t = f"`{arg.get('type', '')}`"
    return f"List of {t}" if arg.get("multiple") else t


def attributes(arg):
    """One labelled line per attribute, as separate markdown paragraphs."""
    head = type_label(arg)
    if arg.get("required"):
        head += " [required]{.arg-required}"
    lines = [head]
    for key, label in (("default", "Default"), ("example", "Example"), ("choices", "Choices")):
        if arg.get(key) not in (None, []):
            lines.append(f"[{label}]{{.arg-key}} {_values(arg[key])}")
    for key, label in (("min", "Min"), ("max", "Max")):
        if arg.get(key) is not None:
            lines.append(f"[{label}]{{.arg-key}} {format_value(arg[key])}")
    if arg.get("multiple") and arg.get("multiple_sep"):
        lines.append(f"[Separator]{{.arg-key}} {format_value(arg['multiple_sep'])}")
    return "\n\n".join(lines)


def _cell(cls, role, content):
    return f'::: {{.{cls} role="{role}"}}\n{content}\n:::\n'


def argument_row(arg):
    return (
        ':::: {.arg-row role="row"}\n'
        + _cell("arg-name", "cell", f"`{arg['name']}`")
        + _cell("arg-desc", "cell", markdown(arg.get("description")))
        + _cell("arg-attrs", "cell", attributes(arg))
        + "::::\n"
    )


HEADER_ROW = (
    ':::: {.arg-row .arg-head role="row"}\n'
    + _cell("arg-name", "columnheader", "Name")
    + _cell("arg-desc", "columnheader", "Description")
    + _cell("arg-attrs", "columnheader", "Attributes")
    + "::::\n"
)


def argument_groups_section(config):
    parts = []
    for group in config.get("argument_groups") or []:
        args = group.get("arguments") or []
        if not args:
            continue
        block = f"### {group['name']}\n\n"
        desc = markdown(group.get("description"))
        if desc:
            block += desc + "\n\n"
        block += ('::::: {.arg-table role="table"}\n' + HEADER_ROW
                  + "".join(argument_row(a) for a in args) + ":::::\n")
        parts.append(block)
    if not parts:
        return ""
    heading = "Argument groups" if len(parts) > 1 else "Argument group"
    return f"## {heading}\n\n" + "\n".join(parts)


def replace_section(page, section):
    """Swap the page's "## Argument group(s)" section (up to the next level-2
    heading) for `section`; an empty `section` removes it."""
    m = SECTION_RE.search(page)
    if not m:
        return page
    if not section:
        return page[:m.start()] + page[m.end():].lstrip("\n")
    return page[:m.start()] + section.rstrip() + "\n" + page[m.end():]


def split_description(desc):
    """Config description → (one-line summary, remaining markdown).

    Quarto's title block and the catalog table show `description` as one line
    of inline text, so only the first paragraph goes there; the rest (more
    paragraphs, lists) is rendered in the page body.
    """
    paras = markdown(desc).split("\n\n", 1)
    summary = " ".join(paras[0].split())
    rest = paras[1].strip() if len(paras) > 1 else ""
    return summary, rest


def set_description(page, summary):
    """Write `summary` as the one-line frontmatter description."""
    end = page.index("\n---\n", 4)
    fm, body = page[4:end].split("\n"), page[end:]
    value = ["description: " + json.dumps(summary, ensure_ascii=False)]
    out, i, placed = [], 0, False
    while i < len(fm):
        if fm[i].startswith("description:"):
            i += 1
            # skip the rest of a block-scalar value (indented or blank lines)
            while i < len(fm) and (fm[i].startswith(" ") or fm[i] == ""):
                i += 1
            out.extend(value)
            placed = True
            continue
        out.append(fm[i])
        i += 1
    if not placed:
        out.extend(value)
    return "---\n" + "\n".join(out) + body


BODY_DESC_RE = re.compile(r'::: \{\.ref-description\}\n.*?\n:::\n\n?', re.S)


def set_body_description(page, rest):
    """Put `rest` (the description after its first paragraph) in a
    `.ref-description` block right before the page's first section."""
    page = BODY_DESC_RE.sub("", page)
    if not rest:
        return page
    block = "::: {.ref-description}\n" + rest + "\n:::\n\n"
    m = re.search(r'(?m)^## ', page)
    if not m:
        return page.rstrip() + "\n\n" + block
    return page[:m.start()] + block + page[m.start():]


def process_page(page, config):
    if config.get("description"):
        summary, rest = split_description(config["description"])
        page = set_body_description(set_description(page, summary), rest)
    return replace_section(page, argument_groups_section(config))


def fetch_config(pkg, version, namespace, name):
    for runner in ("nextflow", "executable"):
        txt = fetch(f"{RAW}/{pkg}/raw/tag/{version}/target/{runner}/{namespace}/{name}/.config.vsh.yaml")
        if txt:
            return yaml.safe_load(txt)
    return None


def process(path):
    parts = path.split("/")  # reference/<pkg>/<version>/<namespace...>/<name>.qmd
    pkg, version = parts[1], parts[2]
    namespace, name = "/".join(parts[3:-1]), parts[-1][:-4]
    config = fetch_config(pkg, version, namespace, name)
    if config is None:
        print(f"[arguments] no config found for {path}", file=sys.stderr)
        return False
    txt = open(path, encoding="utf-8").read()
    new = process_page(txt, config)
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
    print(f"[arguments] rendered argument groups + descriptions for {n} pages")


if __name__ == "__main__":
    main(sys.argv)
