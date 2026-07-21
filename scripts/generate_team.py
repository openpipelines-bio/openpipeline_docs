#!/usr/bin/env python3
"""Generate the Team page (team/index.qmd).

Two independent sources — no merging:

* **Code contributors** — the author files in each package repo's `src/authors/`
  (fetched from GitHub across the whole ecosystem), rendered minimally
  (name + github/orcid/linkedin). A person who contributes to more than one
  package is listed once, with their links unioned.
* **Package maintainers / advisors / sponsors** — this repo's
  ``data/members/*.yaml`` overlay, which carries the non-code / time-sensitive
  fields. Grouping is via each file's ``team.groups`` (+ ``team.role``).

Field visibility:
  email         -> package maintainers only
  organization  -> package maintainers, advisors, sponsors (never code contributors)

Run:  python scripts/generate_team.py
The set of source repos comes from the package registry (data/packages.yaml,
read via scripts/packages.py).
"""

import glob
import html
import json
import os
import sys
import urllib.error
import urllib.request

import yaml

# The package registry (data/packages.yaml) is the single source of truth for
# which repos to pull author files from — see scripts/packages.py.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from packages import ORG, PACKAGES, REF  # noqa: E402

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
OVERLAY_DIR = os.path.join(ROOT, "data", "members")
OUT = os.path.join(ROOT, "team", "index.qmd")
AVATAR = "/images/avatar.svg"


def gh(url):
    req = urllib.request.Request(url, headers={"User-Agent": "op-docs-team-gen"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def contributor_key(person):
    """Identity used to dedupe across packages: GitHub handle if present
    (case-insensitive), else the name."""
    handle = links_of(person).get("github")
    return handle.lower() if handle else (person.get("name") or "").strip().lower()


def merge_contributor(people, person):
    """Add a person, or union their links into an already-seen entry."""
    key = contributor_key(person)
    if not key:
        return
    if key not in people:
        people[key] = person
        return
    kept = people[key]
    info = kept.get("info")
    if not isinstance(info, dict):
        info = kept["info"] = {}
    links = info.get("links")
    if not isinstance(links, dict):
        links = info["links"] = {}
    for name, value in links_of(person).items():
        links.setdefault(name, value)


def fetch_code_contributors():
    """Author files in every package repo's src/authors, merged across the whole
    ecosystem (name + links only). Repos without an authors dir are skipped."""
    people = {}
    for repo in PACKAGES:
        try:
            listing = json.loads(gh(f"https://api.github.com/repos/{ORG}/{repo}/contents/src/authors?ref={REF}"))
        except urllib.error.HTTPError as e:
            if e.code == 404:
                continue  # this package ships no src/authors/
            raise
        for entry in listing:
            if not entry["name"].endswith(".yaml"):
                continue
            raw = gh(f"https://raw.githubusercontent.com/{ORG}/{repo}/{REF}/src/authors/{entry['name']}")
            merge_contributor(people, yaml.safe_load(raw) or {})
    return list(people.values())


def links_of(person):
    return ((person.get("info") or {}).get("links") or {})


def avatar_for(person):
    handle = links_of(person).get("github")
    return f"https://github.com/{handle}.png" if handle else AVATAR


def render_links(person, allow_email):
    links = links_of(person)
    out = []
    if allow_email and links.get("email"):
        out.append(("bi-envelope", "E-mail", "mailto:" + links["email"]))
    if links.get("github"):
        out.append(("bi-github", "GitHub", "https://github.com/" + links["github"]))
    if links.get("orcid"):
        out.append(("orcid", "ORCID", "https://orcid.org/" + str(links["orcid"])))
    if links.get("linkedin"):
        out.append(("bi-linkedin", "LinkedIn", "https://www.linkedin.com/in/" + links["linkedin"]))
    return out


def card(person, *, team_role=None, show_org=False, allow_email=False):
    info = person.get("info") or {}
    name = person["name"]
    out = ['  <div class="people-person">']
    out.append(f'    <img loading="lazy" class="avatar avatar-circle" src="{avatar_for(person)}" alt="{html.escape(name)}" />')
    out.append('    <div class="portrait-title">')
    out.append(f'      <h4>{html.escape(name)}</h4>')
    if team_role:
        out.append(f'      <h6 class="team-role"><i>{html.escape(team_role)}</i></h6>')
    if show_org:
        for org in info.get("organizations") or []:
            role = html.escape(org.get("role", "") or "")
            nm, href = org.get("name"), org.get("href")
            if nm:
                link = f'<a href="{href}">{html.escape(nm)}</a>' if href else html.escape(nm)
                txt = f"{role} at {link}" if role else link
            else:
                txt = role
            if txt:
                out.append(f"      <h6><i>{txt}</i></h6>")
    lnks = render_links(person, allow_email)
    if lnks:
        out.append('      <div class="network">')
        for icon, text, href in lnks:
            inner = (f'<i class="bi {icon}"></i>' if icon.startswith("bi-")
                     else f'<span class="link-text">{html.escape(text)}</span>')
            out.append(f'        <a class="network-icon" href="{href}" title="{html.escape(text)}">{inner}</a>')
        out.append("      </div>")
    out.append("    </div>")
    out.append("  </div>")
    return "\n".join(out)


def section(title, cards):
    body = "\n".join(cards)
    return f'## {title}\n\n```{{=html}}\n<div class="people-widget justify-content-evenly">\n{body}\n</div>\n```\n'


def main():
    # overlay (this repo) — maintainers / advisors / sponsors
    overlay = [yaml.safe_load(open(f)) or {} for f in sorted(glob.glob(os.path.join(OVERLAY_DIR, "*.yaml")))]

    def groups(p):
        return (p.get("team") or {}).get("groups") or []

    def role(p):
        return (p.get("team") or {}).get("role")

    maintainers = [p for p in overlay if "maintainer" in groups(p)]
    advisors = [p for p in overlay if "advisor" in groups(p)]
    sponsors = [p for p in overlay if "sponsor" in groups(p)]

    # maintainers: managers first, then maintainers, alphabetical within each
    maintainers.sort(key=lambda p: (0 if "manager" in (role(p) or "").lower() else 1, p["name"].lower()))
    advisors.sort(key=lambda p: p["name"].lower())
    sponsors.sort(key=lambda p: p["name"].lower())

    # code contributors (code repo) — minimal
    contributors = fetch_code_contributors()
    contributors.sort(key=lambda p: p["name"].lower())

    sections = [
        section("Package maintainers",
                [card(p, team_role=role(p), show_org=True, allow_email=True) for p in maintainers]),
        section("Code contributors",
                [card(p, show_org=False, allow_email=False) for p in contributors]),
        section("Scientific advisors",
                [card(p, show_org=True, allow_email=False) for p in advisors]),
        section("Project sponsors",
                [card(p, show_org=True, allow_email=False) for p in sponsors]),
    ]

    frontmatter = (
        "---\n"
        'pagetitle: "Team — OpenPipeline"\n'
        'title: "Team"\n'
        'description: "The people building and maintaining OpenPipeline."\n'
        "toc: false\n"
        "page-layout: full\n"
        "anchor-sections: false\n"
        "css: team.css\n"
        "---\n\n"
        "<!-- Generated by scripts/generate_team.py — do not hand-edit.\n"
        "     Code contributors come from each package repo's src/authors/;\n"
        "     maintainers, advisors and sponsors come from data/members/.\n"
        "     See design/team-authorship.md. -->\n\n"
    )

    with open(OUT, "w", encoding="utf-8") as f:
        f.write(frontmatter + "\n".join(sections))

    print(f"wrote {OUT}")
    print(f"  {len(maintainers)} package maintainers, {len(contributors)} code contributors, "
          f"{len(advisors)} advisors, {len(sponsors)} sponsors  "
          f"(code from {len(PACKAGES)} repos @{REF}: {', '.join(PACKAGES)})")


if __name__ == "__main__":
    main()
