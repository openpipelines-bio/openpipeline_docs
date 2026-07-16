#!/usr/bin/env python3
"""Add a data-flow diagram to composite workflows.

Composite workflows orchestrate other workflows/components, so the Viash
generator emits no Visualisation for them. We reconstruct the data flow from
the workflow's VDSL3 `main.nf`: each `<chan> = <src_ch> | … | <comp>.run(…)`
assignment tells us which component consumes which channel, so we can draw
arrows between the components/subworkflows exactly like the leaf-workflow
diagrams. Workflows and components are treated uniformly as nodes.

Config + main.nf are read from viash-hub (the source the packages are pulled
from). Idempotent: only `type: workflow` pages without a diagram are touched.

Usage: python3 scripts/compose_viz.py [--force] [path ...]   (default: reference)
"""

import glob
import os
import re
import sys
import urllib.request

import yaml

RAW = "https://packages.viash-hub.com/vsh"


def fetch(url):
    try:
        return urllib.request.urlopen(url, timeout=30).read().decode("utf-8")
    except Exception:
        return None


def alias_map(config_text):
    """Map the name used in main.nf (alias, else component name) → display name."""
    data = yaml.safe_load(config_text) or {}
    amap = {}
    for d in data.get("dependencies") or []:
        name = d.get("name") if isinstance(d, dict) else None
        if not name:
            continue
        disp = name.split("/")[-1]
        amap[d.get("alias") or disp] = disp
    return amap


def parse_dataflow(main_nf, amap):
    """Parse channel assignments into (nodes, edges) between components."""
    text = main_nf
    if "workflow run_wf" in text:
        text = text.split("workflow run_wf", 1)[1]
    if "\n  main:" in text:
        text = text.split("\n  main:", 1)[1]
    text = re.split(r'\n\s*emit:', text, 1)[0]

    # split into `<chan> = …` assignment segments
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

    # loop variables used in runEach/inject closures — never real components
    loopvars = {"component", "channel_in", "channel_out", "channel_out_integrated",
                "acc", "it", "ch"}

    def to_disp(names):
        return [amap.get(x.strip(), x.strip()) for x in names if x.strip()]

    producers, nodes, edges = {}, set(), set()
    has_runif, always = set(), set()   # to decide which nodes are optional
    for lhs, rhs in assigns:
        srcs = [c for c in re.findall(r'\b(\w*_ch\w*)\b', rhs) if c != lhs]
        upstream = set().union(*[producers.get(s, set()) for s in srcs]) if srcs else set()

        run_each = re.search(r'components:\s*\[([^\]]+)\]', rhs) if "runEach(" in rhs else None
        inject = re.search(r'\[([^\]\n]+)\]\.inject\s*\(', rhs)

        if run_each:
            # per-item alternatives (e.g. per-modality processing) — parallel
            comps = to_disp(run_each.group(1).split(","))
            nodes.update(comps)
            for p in upstream:
                for c in comps:
                    edges.add((p, c))
            always.update(comps)
            producers[lhs] = set(comps)
        elif inject:
            # a list folded onto a channel — applied in sequence
            comps = to_disp(inject.group(1).split(","))
            nodes.update(comps)
            for p in upstream:
                if comps:
                    edges.add((p, comps[0]))
            for a, b in zip(comps, comps[1:]):
                edges.add((a, b))
            (has_runif if "runIf" in rhs else always).update(comps)
            producers[lhs] = {comps[-1]} if comps else upstream
        else:
            runs = [m for m in re.finditer(r'(\w+)\.run\s*\(', rhs)
                    if m.group(1) not in loopvars]
            comps = []
            for i, m in enumerate(runs):
                disp = amap.get(m.group(1), m.group(1))
                end = runs[i + 1].start() if i + 1 < len(runs) else len(rhs)
                (has_runif if "runIf" in rhs[m.end():end] else always).add(disp)
                if not comps or comps[-1] != disp:   # collapse consecutive repeats
                    comps.append(disp)
            if comps:
                nodes.update(comps)
                for p in upstream:
                    edges.add((p, comps[0]))
                for a, b in zip(comps, comps[1:]):
                    edges.add((a, b))
                producers[lhs] = {comps[-1]}
            else:  # pass-through / merge — carry upstream producers forward
                producers[lhs] = upstream
    edges = {(a, b) for a, b in edges if a and b and a != b}
    optional = {n for n in nodes if n in has_runif and n not in always}
    return nodes, edges, optional


def _shape(name, nid):
    low = name.lower()
    if "split" in low:                                   # split — data diverges
        return f"{nid}[/{name}\\]"
    if low == "merge" or "concat" in low:                # combine — data converges
        return f"{nid}[\\{name}/]"
    return f'{nid}["{name}"]'


def diagram(nodes, edges, optional):
    def nid(s):
        return "c_" + re.sub(r"[^0-9a-zA-Z]", "_", s)

    lines = ["flowchart TB"]
    for n in sorted(nodes):
        lines.append("    " + _shape(n, nid(n)))
    for a, b in sorted(edges):
        lines.append(f"    {nid(a)} --> {nid(b)}")
    for n in sorted(nodes):
        if n in optional:  # optional step — dashed, muted
            lines.append(f"    style {nid(n)} fill:#f2f6f3,stroke:#8ba295,stroke-dasharray:5 3,color:#566b5f")
        else:
            lines.append(f"    style {nid(n)} fill:#e2f4e7,stroke:#2b8f52,color:#13201a")
    return "\n".join(lines)


def build(pkg, version, namespace, name):
    base = f"{RAW}/{pkg}/raw/tag/{version}/src/{namespace}/{name}"
    config_text = fetch(base + "/config.vsh.yaml")
    main_nf = fetch(base + "/main.nf")
    if not config_text or not main_nf:
        return None
    nodes, edges, optional = parse_dataflow(main_nf, alias_map(config_text))
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
    mer = build(pkg, version, namespace, name)
    if not mer:
        return False
    notes = []
    if "stroke-dasharray" in mer:
        notes.append("Dashed nodes are optional steps.")
    if "[/" in mer or "[\\" in mer:
        notes.append("Trapezoids split or combine data.")
    legend = ("\n" + "  \n".join(f"*{n}*" for n in notes) + "\n") if notes else ""
    block = "## Visualisation\n\n```{mermaid}\n" + mer + "\n```\n" + legend
    if has_diagram:  # replace the existing Visualisation section (incl. any legend lines)
        txt = re.sub(
            r'##\s*Visualisation\s*\n+```\{mermaid\}\n.*?\n```\n*(?:\*[^\n]*\*\s*\n*)*',
            lambda _m: block, txt, flags=re.S)  # lambda: keep backslashes in `block` literal
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
