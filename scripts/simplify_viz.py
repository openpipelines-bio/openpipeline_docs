#!/usr/bin/env python3
"""Simplify the auto-generated workflow Visualisation mermaid diagrams.

The Viash/Nextflow generator emits a node for every channel operation
(Channel.fromList, filter, cross, concat, branch, Output, …), which makes the
diagram unreadable. This rewrites each generated diagram to show only the Viash
**component** nodes, contracting edges through the plumbing so the data flow
between components is preserved. Where a contracted path crosses a meaningful
channel op, the edge is labelled (concat→concatenate, branch→split, mix→merge).

Idempotent: only diagrams still in the generated form (containing
`Channel.fromList` / per-node `style` lines) are rewritten.

Usage: python3 scripts/simplify_viz.py [path ...]   (default: reference)
"""

import glob
import os
import re
import sys

# Nextflow/DSL channel operations the generator emits as nodes. These are
# per-component channel bookkeeping (not meaningful data flow), so they are
# contracted away — edges are routed through them. Real data-flow steps
# (concatenate_h5mu, merge, split_modalities, …) are actual components and stay.
DROP = {
    "cross", "filter", "concat", "branch", "mix", "Channel.fromList", "Output",
    "map", "join", "groupTuple", "combine", "set", "view", "flatMap",
}

NODE_RE = re.compile(r'^\s*(v\d+)[\(\[\{]+"?(.*?)"?[\)\]\}]+\s*$')
EDGE_RE = re.compile(r'^\s*(v\d+)\s*--+>(?:\|[^|]*\|)?\s*(v\d+)\s*$')


def _transitive_reduction(keep, edges):
    """Drop edge a->b when b is still reachable from a via a longer path."""
    adj = {n: set() for n in keep}
    for a, b in edges:
        adj[a].add(b)

    def reachable(s, t):
        stack, seen = list(adj[s]), set()
        while stack:
            n = stack.pop()
            if n == t:
                return True
            if n in seen:
                continue
            seen.add(n)
            stack.extend(adj[n])
        return False

    for a, b in sorted(edges):
        adj[a].discard(b)
        if not reachable(a, b):   # no alternative path — keep it
            adj[a].add(b)
    return {(a, b) for a in adj for b in adj[a]}


def simplify_mermaid(src):
    nodes, edges = {}, []
    for line in src.splitlines():
        if line.strip().startswith("style "):
            continue
        m = EDGE_RE.match(line)
        if m:
            edges.append((m.group(1), m.group(2)))
            continue
        m = NODE_RE.match(line)
        if m:
            nodes[m.group(1)] = m.group(2).strip()

    # keep = components (anything not plumbing) + meaningful junctions
    keep = {n for n, lbl in nodes.items() if lbl not in DROP}
    succ = {}
    for a, b in edges:
        succ.setdefault(a, []).append(b)

    # route edges between kept nodes, contracting through DROP-only paths
    kept_edges = set()
    for k in keep:
        stack, seen = list(succ.get(k, [])), set()
        while stack:
            n = stack.pop()
            if n in keep:
                if n != k:
                    kept_edges.add((k, n))
                continue
            if n in seen:
                continue
            seen.add(n)
            stack.extend(succ.get(n, []))

    if not keep:
        return None
    kept_edges = _transitive_reduction(keep, kept_edges)

    lines = ["flowchart TB"]
    for n in sorted(keep):
        lbl = nodes[n].replace('"', "'")
        lines.append(f'    {n}["{lbl}"]')
    for a, b in sorted(kept_edges):
        lines.append(f'    {a} --> {b}')
    for n in sorted(keep):  # per-node style (the generator's proven approach)
        lines.append(f'    style {n} fill:#e2f4e7,stroke:#2b8f52,color:#13201a')
    return "\n".join(lines)


def process_file(path):
    txt = open(path, encoding="utf-8").read()
    changed = False

    def repl(m):
        nonlocal changed
        body = m.group(1)
        if "Channel.fromList" not in body:
            return m.group(0)  # not the generated form — leave it
        new = simplify_mermaid(body)
        if not new:
            return m.group(0)
        changed = True
        return "```{mermaid}\n" + new + "\n```"

    txt = re.sub(r'```\{mermaid\}\n(.*?)\n```', repl, txt, flags=re.S)
    if changed:
        open(path, "w", encoding="utf-8").write(txt)
    return changed


def main(argv):
    targets = argv[1:] or ["reference"]
    n = 0
    for t in targets:
        files = [t] if t.endswith(".qmd") else glob.glob(f"{t}/**/*.qmd", recursive=True)
        for f in files:
            if process_file(f):
                n += 1
    print(f"[viz] simplified diagrams in {n} files")


if __name__ == "__main__":
    main(sys.argv)
