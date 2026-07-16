#!/usr/bin/env python3
"""Add a data-flow diagram to composite workflows.

Composite workflows orchestrate other workflows/components, so the Viash
generator emits no Visualisation for them. We reconstruct the data flow from
the workflow's VDSL3 `main.nf`: each `<chan> = <src_ch> | … | <comp>.run(…)`
assignment tells us which component consumes which channel.

Nodes are identified by their full dependency path. **Private** subworkflows
(ones with no reference page of their own, so a user can't drill into them) are
recursively **inlined** — their steps are spliced into the parent graph. Public
subworkflows and leaf components stay as single nodes (users can click through).

Config + main.nf are read from viash-hub. Idempotent: only `type: workflow`
pages without a diagram are touched.

Usage: python3 scripts/compose_viz.py [--force] [path ...]   (default: reference)
"""

import glob
import os
import re
import sys
import urllib.request

import yaml

RAW = "https://packages.viash-hub.com/vsh"
LOOPVARS = {"component", "channel_in", "channel_out", "channel_out_integrated", "acc", "it", "ch"}
_CACHE = {}


def fetch(url):
    if url in _CACHE:
        return _CACHE[url]
    try:
        out = urllib.request.urlopen(url, timeout=30).read().decode("utf-8")
    except Exception:
        out = None
    _CACHE[url] = out
    return out


def leaf(full):
    return full.split("/")[-1]


def depmap(config_text):
    """call name used in main.nf (alias, else component name) → (full path, external?)."""
    data = yaml.safe_load(config_text) or {}
    out = {}
    for d in data.get("dependencies") or []:
        name = d.get("name") if isinstance(d, dict) else None
        if not name:
            continue
        out[d.get("alias") or name.split("/")[-1]] = (name, bool(d.get("repository")))
    return out


def parse_dataflow(main_nf, dmap):
    """Parse channel assignments into (nodes, edges, optional, external), full paths."""
    text = main_nf
    if "workflow run_wf" in text:
        text = text.split("workflow run_wf", 1)[1]
    if "\n  main:" in text:
        text = text.split("\n  main:", 1)[1]
    text = re.split(r'\n\s*emit:', text, 1)[0]

    assigns, cur, lhs = [], [], None
    for line in text.splitlines():
        m = re.match(r'\s*(\w*_ch\w*)\s*=', line)
        if m:
            if lhs:
                assigns.append((lhs, "\n".join(cur)))
            lhs, cur = m.group(1), [line]
        elif lhs:
            cur.append(line)
    if lhs:
        assigns.append((lhs, "\n".join(cur)))

    external = set()

    def resolve_call(name):
        full, ext = dmap.get(name, (name, False))
        if ext:
            external.add(full)
        return full

    def to_full(names):
        return [resolve_call(x.strip()) for x in names if x.strip()]

    producers, nodes, edges = {}, set(), set()
    has_runif, always = set(), set()
    for lhs, rhs in assigns:
        srcs = [c for c in re.findall(r'\b(\w*_ch\w*)\b', rhs) if c != lhs]
        upstream = set().union(*[producers.get(s, set()) for s in srcs]) if srcs else set()
        run_each = re.search(r'components:\s*\[([^\]]+)\]', rhs) if "runEach(" in rhs else None
        inject = re.search(r'\[([^\]\n]+)\]\.inject\s*\(', rhs)

        if run_each:
            comps = to_full(run_each.group(1).split(","))
            nodes.update(comps)
            for p in upstream:
                for c in comps:
                    edges.add((p, c))
            always.update(comps)
            producers[lhs] = set(comps)
        elif inject:
            comps = to_full(inject.group(1).split(","))
            nodes.update(comps)
            for p in upstream:
                if comps:
                    edges.add((p, comps[0]))
            for a, b in zip(comps, comps[1:]):
                edges.add((a, b))
            (has_runif if "runIf" in rhs else always).update(comps)
            producers[lhs] = {comps[-1]} if comps else upstream
        else:
            runs = [m for m in re.finditer(r'(\w+)\.run\s*\(', rhs) if m.group(1) not in LOOPVARS]
            comps = []
            for i, m in enumerate(runs):
                full = resolve_call(m.group(1))
                end = runs[i + 1].start() if i + 1 < len(runs) else len(rhs)
                (has_runif if "runIf" in rhs[m.end():end] else always).add(full)
                if not comps or comps[-1] != full:
                    comps.append(full)
            if comps:
                nodes.update(comps)
                for p in upstream:
                    edges.add((p, comps[0]))
                for a, b in zip(comps, comps[1:]):
                    edges.add((a, b))
                producers[lhs] = {comps[-1]}
            else:
                producers[lhs] = upstream
    edges = {(a, b) for a, b in edges if a and b and a != b}
    optional = {n for n in nodes if n in has_runif and n not in always}
    return nodes, edges, optional, external


def _substitute(nodes, edges, s, sub_nodes, sub_edges):
    """Replace node `s` with subgraph (sub_nodes, sub_edges), rewiring s's edges."""
    into = [a for (a, b) in edges if b == s]
    outof = [b for (a, b) in edges if a == s]
    entries = {x for x in sub_nodes if x not in {b for _, b in sub_edges}} or set(sub_nodes)
    exits = {x for x in sub_nodes if x not in {a for a, _ in sub_edges}} or set(sub_nodes)
    edges.difference_update({(a, b) for (a, b) in edges if a == s or b == s})
    nodes.discard(s)
    nodes.update(sub_nodes)
    edges.update(sub_edges)
    for a in into:
        for e in entries:
            edges.add((a, e))
    for b in outof:
        for x in exits:
            edges.add((x, b))


def resolve(pkg, version, full, root, visited):
    cfg = fetch(f"{RAW}/{pkg}/raw/tag/{version}/src/{full}/config.vsh.yaml")
    main = fetch(f"{RAW}/{pkg}/raw/tag/{version}/src/{full}/main.nf")
    if not cfg or not main:
        return set(), set(), set()
    nodes, edges, optional, external = parse_dataflow(main, depmap(cfg))
    for n in list(nodes):
        if n in visited or n in external:
            continue                                   # avoid cycles / external → keep node
        if os.path.exists(f"{root}/{n}.qmd"):
            continue                                   # public (has a page) → keep node
        submain = fetch(f"{RAW}/{pkg}/raw/tag/{version}/src/{n}/main.nf")
        if not submain or "run_wf" not in submain:
            continue                                   # leaf component → keep node
        sn, se, so = resolve(pkg, version, n, root, visited | {full})
        if not sn:
            continue
        _substitute(nodes, edges, n, sn, se)
        optional |= so
    return nodes, edges, optional


def _shape(full, nid):
    low = leaf(full).lower()
    lbl = leaf(full)
    if "split" in low:
        return f"{nid}[/{lbl}\\]"
    if low == "merge" or "concat" in low:
        return f"{nid}[\\{lbl}/]"
    return f'{nid}["{lbl}"]'


def diagram(nodes, edges, optional):
    def nid(s):
        return "c_" + re.sub(r"[^0-9a-zA-Z]", "_", s)

    lines = ["flowchart TB"]
    for n in sorted(nodes):
        lines.append("    " + _shape(n, nid(n)))
    for a, b in sorted(edges):
        lines.append(f"    {nid(a)} --> {nid(b)}")
    for n in sorted(nodes):
        if n in optional:
            lines.append(f"    style {nid(n)} fill:#f2f6f3,stroke:#8ba295,stroke-dasharray:5 3,color:#566b5f")
        else:
            lines.append(f"    style {nid(n)} fill:#e2f4e7,stroke:#2b8f52,color:#13201a")
    return "\n".join(lines)


def build(pkg, version, namespace, name, root=None):
    root = root or f"reference/{pkg}/{version}"
    nodes, edges, optional = resolve(pkg, version, f"{namespace}/{name}", root, set())
    if not nodes:
        return None
    return diagram(nodes, edges, optional)


def process(path, force=False):
    txt = open(path, encoding="utf-8").read()
    has_diagram = "```{mermaid}" in txt
    if has_diagram and not force:
        return False
    if not re.search(r'(?m)^type:\s*"?workflow"?', txt):
        return False
    parts = path.split("/")  # reference/<pkg>/<version>/<namespace...>/<name>.qmd
    pkg, version = parts[1], parts[2]
    namespace = "/".join(parts[3:-1])
    name = parts[-1][:-4]
    mer = build(pkg, version, namespace, name, root=f"reference/{pkg}/{version}")
    if not mer:
        return False
    notes = []
    if "stroke-dasharray" in mer:
        notes.append("Dashed nodes are optional steps.")
    if "[/" in mer or "[\\" in mer:
        notes.append("Trapezoids split or combine data.")
    legend = ("\n" + "  \n".join(f"*{n}*" for n in notes) + "\n") if notes else ""
    block = "## Visualisation\n\n```{mermaid}\n" + mer + "\n```\n" + legend
    if has_diagram:
        txt = re.sub(
            r'##\s*Visualisation\s*\n+```\{mermaid\}\n.*?\n```\n*(?:\*[^\n]*\*\s*\n*)*',
            lambda _m: block, txt, flags=re.S)
    else:
        txt = txt.rstrip() + "\n\n" + block
    open(path, "w", encoding="utf-8").write(txt)
    return True


def main(argv):
    args = argv[1:]
    force = "--force" in args
    targets = [a for a in args if a != "--force"] or ["reference"]
    n = 0
    for t in targets:
        files = [t] if t.endswith(".qmd") else glob.glob(f"{t}/**/*.qmd", recursive=True)
        for f in files:
            if os.path.basename(f) != "index.qmd" and process(f, force=force):
                n += 1
    print(f"[compose] wrote data-flow diagrams for {n} composite workflows")


if __name__ == "__main__":
    main(sys.argv)
