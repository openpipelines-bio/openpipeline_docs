"""Tests for scripts/run_command.py (the reference "Run command" section)."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import run_command as rc  # noqa: E402

BASH = "```bash\nnextflow run openpipelines-bio/openpipeline \\\n  -params-file params.yaml\n```"
VH = "https://www.viash-hub.com/packages/openpipeline/v4.2.0/components/mapping/cellranger_count"


def test_section_points_to_viash_hub_and_the_guides_in_a_callout():
    out = rc.run_command_section(BASH, VH)
    assert out.startswith("### Run command\n")
    assert '::: {.callout-note appearance="simple" title="Create a params.yaml"}' in out
    assert f"]({VH})" in out
    assert "see examples of using params files in the [guides](/guides/index.qmd)" in out
    assert "running-pipelines" not in out
    assert "](/guides/process-many-samples.qmd)" in out
    assert BASH in out
    # the params.yaml note comes before the command that uses it
    assert out.index(VH) < out.index(BASH)


def test_section_keeps_backend_and_platform_note_after_the_command():
    out = rc.run_command_section(BASH, VH)
    note = out.index("-profile podman")
    assert note > out.index(BASH)


def test_replace_swaps_an_existing_run_command_section():
    page = (
        "## Example commands\n\n### View help\n\nhelp\n\n"
        "### Run command\n\nOLD intro\n\nRun locally with:\n\n" + BASH + "\n\nOLD note\n"
    )
    out = rc.replace_run_command(page, VH)
    assert "OLD" not in out
    assert "### View help\n\nhelp\n\n### Run command\n" in out
    assert out.count(BASH) == 1
    assert rc.replace_run_command(out, VH) == out


def test_replace_stops_at_the_next_level_two_heading():
    page = "### Run command\n\nRun locally with:\n\n" + BASH + "\n\nold\n\n## Authors\n\nme\n"
    out = rc.replace_run_command(page, VH)
    assert out.endswith("\n\n## Authors\n\nme\n")
    assert "old" not in out


def test_viash_hub_url_is_read_from_the_page_links():
    page = ("[![](/images/viash-hub-logo.svg){.vh-icon} Get run instructions](" + VH + ")\n")
    assert rc.viash_hub_url(page) == VH
