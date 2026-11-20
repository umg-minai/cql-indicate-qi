import glob
import re
from pathlib import Path
from typing import Callable, List

from terminology_from_data_dictionary.model import Output
from utilities import make_concept_set_url, make_athena_url, maybe_truncate


def naive_markdown_escape(string: str):
    return string.replace("[", "\\[").replace("]", "\\]")


def format_markdown_link(title: str, url: str):
    return f"[{naive_markdown_escape(title)}]({url})"


def format_concept_id_for_markdown(concept_id: int):
    label = str(concept_id)
    url = make_athena_url(concept_id)
    return format_markdown_link(label, url) if url else label


def format_concept_set_for_markdown(concept_set_id: int, concept_set_name: str, concept_set_version: str, max_width=80):
    id_string = str(concept_set_id)
    label = (maybe_truncate(concept_set_name, max_length=max_width - (len(id_string) + 3))
             + f" ({id_string})")
    url = make_concept_set_url(concept_set_id)
    link = format_markdown_link(label, url)
    return f"{link} v{concept_set_version}"


def concept_sort_key(concept):
    # Concepts with a priority come first, in priority order; the rest by name.
    has_priority = concept.priority is not None
    return (not has_priority, concept.priority if has_priority else 0, concept.name.lower())


def format_markdown_table(outputs: List[Output]):
    header = ["Priority", "Concept ID", "Descendants", "Vocabulary", "Concept Name", "Concept Code", "DD Concept Set"]
    rows = []
    widths = [0] * len(header)

    def add_row(*values):
        row = []
        for i, value in enumerate(values):
            content = str(value)
            row.append(content)
            widths[i] = max(widths[i], len(content))
        rows.append(row)

    add_row(*header)
    for i, output in enumerate(outputs):
        add_row()
        for concept in sorted(output.concepts, key=concept_sort_key):
            concept_set = concept.concept_set
            if concept_set:
                concept_set_cell = format_concept_set_for_markdown(concept_set.concept_set_id,
                                                                   concept_set.name,
                                                                   concept_set.concept_set.get("version"),
                                                                   max_width=40)
            else:
                concept_set_cell = "Added by UMG"
            add_row(concept.priority if concept.priority is not None else "",
                    format_concept_id_for_markdown(concept.concept_id),
                    "yes" if concept.descendants else "no",
                    concept.vocabulary,
                    naive_markdown_escape(maybe_truncate(concept.name, max_length=40)),
                    concept.concept_code,
                    concept_set_cell)

    lines = []
    for row in rows:
        line = "|"
        if row:
            for cell, width in zip(row, widths):
                line += " " + cell + " " * (width - len(cell)) + " |"
        else:
            line += "|".join("---" + " " * (width + 2 - 3) for width in widths) + "|"
        lines.append(line)

    return "\n".join(lines)


def update_markdown_file(resolve_name: Callable[[str], Output], markdown_file: Path):
    print(f"Processing {markdown_file}")
    old_text = markdown_file.read_text()
    text = old_text
    done = set()
    match_count = 0
    while True:
        key, match = None, None
        for maybe_match in re.finditer(r"<!-- inject:(.+?) -->\n(\|[^\n]*\n)*", text, re.MULTILINE):
            maybe_key = maybe_match.group(1)
            if maybe_key in done:
                continue
            else:
                done.add(maybe_key)
                key, match = maybe_key, maybe_match
                break
        if not key:
            break
        match_count += 1
        table_outputs = []
        for concept_set_name in re.split(r'\|', key):
            concept_set_name = concept_set_name.strip()
            output = resolve_name(concept_set_name)
            table_outputs.append(output)
        table = format_markdown_table(table_outputs)
        text = (text[0:match.start(0)]
                + f"<!-- inject:{key} -->\n"
                + table
                + text[match.end(0) - 1:])
    if match_count > 0:
        print(f"  {match_count} matches: {', '.join(sorted(done))}")
        if text == old_text:
            print(f"  File unchanged")
        else:
            markdown_file.write_text(text)
            print(f"  File updated")


def update_markdown_files(resolve_name: Callable[[str], Output], markdown_directory: Path):
    markdown_files = glob.glob("*.md", root_dir=markdown_directory)
    for markdown_file in sorted(markdown_files):
        update_markdown_file(resolve_name, markdown_directory / markdown_file)
