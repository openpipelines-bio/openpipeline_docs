"""Tests for scripts/render_arguments.py (reference argument tables + descriptions)."""

import os
import sys

import yaml

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))

import render_arguments as ra  # noqa: E402


def test_format_value_quotes_strings_and_lowercases_booleans():
    assert ra.format_value("auto") == '`"auto"`'
    assert ra.format_value(3000) == "`3000`"
    assert ra.format_value(0.5) == "`0.5`"
    assert ra.format_value(True) == "`true`"
    assert ra.format_value(False) == "`false`"


def test_type_label_marks_multiple_as_list():
    assert ra.type_label({"type": "file", "multiple": False}) == "`file`"
    assert ra.type_label({"type": "file", "multiple": True}) == "List of `file`"


def test_attributes_lists_each_attribute_on_its_own_labelled_line():
    arg = {
        "type": "file",
        "name": "--input",
        "required": True,
        "multiple": True,
        "multiple_sep": ";",
        "example": ["a.fastq.gz", "b.fastq.gz"],
    }
    out = ra.attributes(arg)
    assert "List of `file`" in out
    assert "[required]{.arg-required}" in out
    assert '[Example]{.arg-key} `"a.fastq.gz"`, `"b.fastq.gz"`' in out
    assert '[Separator]{.arg-key} `";"`' in out


def test_attributes_shows_default_choices_and_range():
    arg = {
        "type": "string",
        "name": "--mode",
        "required": False,
        "multiple": False,
        "multiple_sep": ";",
        "default": ["auto"],
        "choices": ["auto", "manual"],
    }
    out = ra.attributes(arg)
    assert "[required]" not in out
    assert '[Default]{.arg-key} `"auto"`' in out
    assert '[Choices]{.arg-key} `"auto"`, `"manual"`' in out
    # separator only matters for list arguments
    assert "Separator" not in out

    num = {"type": "double", "name": "--frac", "min": 0, "max": 1, "multiple": False}
    out = ra.attributes(num)
    assert "[Min]{.arg-key} `0`" in out
    assert "[Max]{.arg-key} `1`" in out


def test_argument_row_keeps_markdown_lists_in_the_description():
    arg = {
        "type": "string",
        "name": "--chemistry",
        "description": "Assay configuration.\n- auto: autodetect mode\n- threeprime: Single Cell 3'\n",
        "default": ["auto"],
        "multiple": False,
    }
    out = ra.argument_row(arg)
    assert "`--chemistry`" in out
    assert "Assay configuration.\n\n- auto: autodetect mode\n- threeprime: Single Cell 3'" in out


def test_argument_groups_section_renders_heading_description_and_rows():
    config = {
        "argument_groups": [
            {
                "name": "Inputs",
                "description": "Input arguments.",
                "arguments": [{"type": "file", "name": "--input", "required": True}],
            },
            {"name": "Empty", "arguments": []},
        ]
    }
    out = ra.argument_groups_section(config)
    # only one group has arguments, so the heading is singular
    assert out.startswith("## Argument group\n")
    assert "### Inputs\n\nInput arguments.\n" in out
    assert "`--input`" in out
    assert ".arg-table" in out
    # groups with no arguments are skipped
    assert "### Empty" not in out


def test_replace_section_swaps_only_the_argument_groups_section():
    page = (
        "---\ntitle: x\n---\n\n## Visualisation\n\nviz\n\n"
        "## Argument groups\n\nOLD\n\n### Inputs\n\nold table\n\n"
        "## Authors\n\nme\n"
    )
    out = ra.replace_section(page, "## Argument groups\n\nNEW\n")
    assert "OLD" not in out and "old table" not in out
    assert "## Visualisation\n\nviz" in out
    assert "## Argument groups\n\nNEW\n\n## Authors\n\nme" in out


def test_single_group_uses_singular_heading_and_is_replaced():
    config = {"argument_groups": [{"name": "Arguments", "arguments": [{"type": "file", "name": "--input"}]}]}
    section = ra.argument_groups_section(config)
    assert section.startswith("## Argument group\n")
    page = "## Argument group\n\n### Arguments\n\nOLD\n\n## Authors\n"
    out = ra.replace_section(page, section)
    assert "OLD" not in out and "`--input`" in out and out.endswith("## Authors\n")


def test_replace_section_at_end_of_file():
    page = "---\ntitle: x\n---\n\n## Argument groups\n\nOLD\n"
    assert ra.replace_section(page, "## Argument groups\n\nNEW\n").endswith("NEW\n")


def test_split_description_takes_the_first_paragraph_as_a_one_line_summary():
    summary, rest = ra.split_description("Sort reads\nby name.\n\nMore detail.\n* a\n")
    assert summary == "Sort reads by name."
    assert rest == "More detail.\n\n* a"
    assert ra.split_description("Just one line.") == ("Just one line.", "")


def test_set_description_writes_the_summary_and_keeps_other_fields():
    page = '---\ntitle: "x"\ndescription: "Flat * a * b"\ntype: "module"\n---\n\nbody\n'
    out = ra.set_description(page, "Alignment by:")
    fm = yaml.safe_load(out.split("---\n")[1])
    assert fm == {"title": "x", "description": "Alignment by:", "type": "module"}
    assert out.endswith("\n\nbody\n")


def test_set_body_description_goes_before_the_first_section_and_is_replaceable():
    page = '---\ntitle: "x"\n---\n\n::: {.column-margin}\ninfo\n:::\n\n## Argument groups\n\nargs\n'
    out = ra.set_body_description(page, "More.\n\n* a")
    assert ":::\n\n::: {.ref-description}\nMore.\n\n* a\n:::\n\n## Argument groups" in out
    again = ra.set_body_description(out, "Other.")
    assert "More." not in again and "::: {.ref-description}\nOther.\n:::" in again
    # no remaining text → no block
    assert ".ref-description" not in ra.set_body_description(out, "")


def test_set_description_keeps_single_line_as_quoted_string():
    page = '---\ntitle: "x"\ndescription: "old"\n---\n'
    out = ra.set_description(page, 'Say "hi".')
    assert 'description: "Say \\"hi\\"."' in out


def test_markdown_inserts_blank_line_before_a_list():
    # Pandoc only starts a list after a blank line; config authors often omit it.
    assert ra.markdown("Intro:\n* a\n* b\n") == "Intro:\n\n* a\n* b"
    assert ra.markdown("Intro:\n\n- a\n") == "Intro:\n\n- a"
    assert ra.markdown("  plain  \n") == "plain"


def test_markdown_ends_a_list_at_an_unindented_line():
    # An unindented line after a list is a new paragraph, not part of the last
    # item; indented lines stay continuations of their item.
    text = "Modes:\n- a\n  note on a\n- b\nSee the docs.\n"
    assert ra.markdown(text) == "Modes:\n\n- a\n  note on a\n- b\n\nSee the docs."


def test_set_body_description_replaces_the_generators_own_description_text():
    # The generator puts every description line after the first in the body,
    # between the Info/Links margin block and the first section.
    page = (
        '---\ntitle: "x"\n---\n\n::: {.column-margin}\ninfo\n:::\n\n'
        "Second line from the generator.\n\n\n## Argument groups\n\nargs\n"
    )
    out = ra.set_body_description(page, "More.")
    assert "Second line from the generator." not in out
    assert "info\n:::\n\n::: {.ref-description}\nMore.\n:::\n\n## Argument groups" in out
    # nothing left to show → the generator's text still goes
    out = ra.set_body_description(page, "")
    assert "Second line" not in out
    assert "info\n:::\n\n## Argument groups" in out


def test_process_page_is_idempotent():
    page = (
        '---\ntitle: "x"\ndescription: "flat"\n---\n\n'
        "## Argument groups\n\nOLD\n\n## Authors\n\nme\n"
    )
    config = {
        "description": "Desc.\n\n- a\n",
        "argument_groups": [{"name": "Inputs", "arguments": [{"type": "file", "name": "--input"}]}],
    }
    once = ra.process_page(page, config)
    assert 'description: "Desc."' in once
    assert "::: {.ref-description}\n- a\n:::" in once
    assert ra.process_page(once, config) == once
