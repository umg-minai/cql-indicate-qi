import glob
import re
from pathlib import Path
from typing import Dict, List

from terminology_from_data_dictionary.model import Output
from utilities import make_concept_set_url, make_athena_url


def maybe_truncate(string, max_length=40):
    return string if len(string) <= max_length else string[:max_length - 1] + "…"


def format_markdown_link(title: str, url: str):
    return f"[{title}]({url})"


def format_concept_id_for_markdown(concept_id: int):
    label = str(concept_id)
    url = make_athena_url(concept_id)
    return format_markdown_link(label, url) if url else label


def format_markdown_table(outputs: List[Output]):
    header = ["Concept ID", "Concept Name", "Descendants", "DD Concept Set"]
    rows = []
    widths = [0]*len(header)

    def add_row(*values):
        row = []
        for i, value in enumerate(values):
            content = str(value)
            row.append(content)
            widths[i] = max(widths[i], len(content))
        rows.append(row)

    add_row(*header)
    for i, output in enumerate(outputs): #sorted(outputs, key=lambda x: x.concept_sets[0].name)):
        add_row()
        for concept in sorted(output.concepts, key=lambda x: x.name.lower()):
            concept_set = concept.concept_set
            if concept_set:
                concept_set_cell = (format_markdown_link(f"{concept_set.name} ({str(concept_set.concept_set_id)})",
                                                        make_concept_set_url(concept_set.concept_set_id))
                                    + f" v{concept_set.concept_set.get("version")}")
            else:
                concept_set_cell = "Added by UMG"
            add_row(format_concept_id_for_markdown(concept.concept_id),
                    maybe_truncate(concept.name),
                    "yes" if concept.descendants else "no",
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


def update_markdown_file(outputs: Dict[str, Output], markdown_file: Path):
    print(f"Processing {markdown_file}")
    old_text = markdown_file.read_text()
    text = old_text
    done = set()
    match_count = 0
    while True:
        key, match = None, None
        for maybe_match in re.finditer("<!-- inject:([a-zA-Z,]+) -->\n(\\|[^\n]*\n)*", text, re.MULTILINE):
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
        for output_name in re.split(",", key):
            output = outputs.get(output_name, None)
            if not output:
                known = ', '.join(outputs.keys())
                raise RuntimeError(f"Markdown file {markdown_file} references mapping '{output_name}' which is not defined. Known mappings are {known}")
            table_outputs.append(output)
        table = format_markdown_table(table_outputs)
        text = (text[0:match.start(0)]
                + f"<!-- inject:{key} -->\n"
                + table
                + text[match.end(0)-1:])
    if match_count > 0:
        print(f"  {match_count} matches: {', '.join(sorted(done))}")
        if text == old_text:
            print(f"  File unchanged")
        else:
            markdown_file.write_text(text)
            print(f"  File updated")


def update_markdown_files(output: Dict[str, Output], markdown_directory: Path):
    markdown_files = glob.glob("*.md", root_dir=markdown_directory)
    for markdown_file in sorted(markdown_files):
        update_markdown_file(output, markdown_directory / markdown_file)

