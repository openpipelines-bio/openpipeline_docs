#!/usr/bin/env python3
"""Read the package registry (data/packages.yaml).

This is the single source of truth for which OpenPipeline packages the
generation tooling operates on. Both scripts/generate_team.py and
.github/workflows/generate-reference.yml consume it through here.

Import it::

    from packages import ORG, REF, PACKAGES, github_repo, viash_hub_slug

Or query it from the shell (used by the reference workflow's bash)::

    python3 scripts/packages.py names            # space-separated package names
    python3 scripts/packages.py org
    python3 scripts/packages.py ref
    python3 scripts/packages.py viash-hub-owner
"""

import os
import sys

import yaml

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REGISTRY_PATH = os.path.join(ROOT, "data", "packages.yaml")


def load():
    with open(REGISTRY_PATH, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


REGISTRY = load()
ORG = REGISTRY.get("org", "openpipelines-bio")
REF = REGISTRY.get("ref", "main")
VIASH_HUB_OWNER = REGISTRY.get("viash_hub_owner", "vsh")
PACKAGES = REGISTRY.get("packages", [])


def github_repo(name):
    """Owner/repo slug for the GitHub source repo, e.g. openpipelines-bio/openpipeline."""
    return f"{ORG}/{name}"


def viash_hub_slug(name):
    """Owner/repo slug on packages.viash-hub.com, e.g. vsh/openpipeline."""
    return f"{VIASH_HUB_OWNER}/{name}"


if __name__ == "__main__":
    query = sys.argv[1] if len(sys.argv) > 1 else "names"
    answers = {
        "names": " ".join(PACKAGES),
        "org": ORG,
        "ref": REF,
        "viash-hub-owner": VIASH_HUB_OWNER,
    }
    if query not in answers:
        sys.exit(f"unknown query: {query!r} (expected one of {', '.join(answers)})")
    print(answers[query])
