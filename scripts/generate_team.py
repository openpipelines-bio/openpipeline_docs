#!/usr/bin/env python3
"""Generate the Team page from the openpipeline (core) author registry.

Authors are the single source of truth in
``openpipelines-bio/openpipeline/src/authors/*.yaml``. This script pulls those
files at render time and writes one ``team/<slug>/index.qmd`` per author, with
the avatar derived from each author's GitHub handle
(``https://github.com/<handle>.png``). The generated per-person folders are
git-ignored — only this script and the listing machinery (``team/index.qmd``,
``members.ejs``, ``team.css``) are tracked.

Wired as a Quarto ``pre-render`` step, so the team always reflects core.
Network cost is one GitHub API call (the tree) plus one raw fetch per author.
If the fetch fails but previously generated files exist, those are kept so an
offline ``quarto preview`` still works.
"""

import glob
import json
import os
import shutil
import sys
import urllib.request

import yaml

REPO = os.environ.get("OPENPIPELINE_REPO", "openpipelines-bio/openpipeline")
REF = os.environ.get("OPENPIPELINE_REF", "main")
TEAM_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "team"))


def gh_get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "openpipeline-docs-team-gen"})
    token = os.environ.get("GITHUB_TOKEN")
    if token and "api.github.com" in url:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as resp:
        return resp.read()


def list_author_files():
    url = f"https://api.github.com/repos/{REPO}/git/trees/{REF}?recursive=1"
    tree = json.loads(gh_get(url))["tree"]
    return sorted(
        n["path"] for n in tree
        if n["path"].startswith("src/authors/") and n["path"].endswith(".yaml")
    )


def build_links(links):
    """Map the author's link dict to the {icon, text, href} list the template renders."""
    out = []
    if not links:
        return out
    if links.get("email"):
        out.append({"icon": "bi-envelope", "text": "E-mail", "href": f"mailto:{links['email']}"})
    if links.get("github"):
        out.append({"icon": "bi-github", "text": "GitHub", "href": f"https://github.com/{links['github']}"})
    if links.get("orcid"):
        out.append({"icon": "fa-brands fa-orcid", "text": "ORCID", "href": f"https://orcid.org/{links['orcid']}"})
    if links.get("linkedin"):
        out.append({"icon": "bi-linkedin", "text": "LinkedIn", "href": f"https://www.linkedin.com/in/{links['linkedin']}"})
    return out


def fetch_authors():
    authors = []
    for path in list_author_files():
        raw = f"https://raw.githubusercontent.com/{REPO}/{REF}/{path}"
        data = yaml.safe_load(gh_get(raw)) or {}
        slug = os.path.splitext(os.path.basename(path))[0]
        authors.append((slug, data))
    return authors


def write_member(slug, data):
    info = (data or {}).get("info", {}) or {}
    links = info.get("links", {}) or {}
    github = links.get("github")
    image = f"https://github.com/{github}.png" if github else "/images/avatar.svg"

    frontmatter = {"title": data.get("name", slug), "image": image}
    orgs = info.get("organizations")
    if orgs:
        frontmatter["organizations"] = orgs
    member_links = build_links(links)
    if member_links:
        frontmatter["links"] = member_links
    frontmatter["about"] = {"template": "jolla"}

    outdir = os.path.join(TEAM_DIR, slug)
    os.makedirs(outdir, exist_ok=True)
    with open(os.path.join(outdir, "index.qmd"), "w", encoding="utf-8") as f:
        f.write("---\n")
        f.write(yaml.safe_dump(frontmatter, sort_keys=False, allow_unicode=True))
        f.write("---\n")


def main():
    try:
        authors = fetch_authors()
    except Exception as exc:  # network / API failure
        if glob.glob(os.path.join(TEAM_DIR, "*", "index.qmd")):
            print(f"[team] WARN: could not refresh authors ({exc}); keeping existing files", file=sys.stderr)
            return
        print(f"[team] ERROR: could not fetch authors and none are cached: {exc}", file=sys.stderr)
        sys.exit(1)

    # Remove previously generated person folders so removed authors disappear.
    # Only subdirectories are generated; index.qmd / members.ejs / team.css stay.
    for entry in os.listdir(TEAM_DIR):
        full = os.path.join(TEAM_DIR, entry)
        if os.path.isdir(full):
            shutil.rmtree(full)

    for slug, data in authors:
        write_member(slug, data)

    print(f"[team] generated {len(authors)} member pages from {REPO}@{REF}")


if __name__ == "__main__":
    main()
