import re
from pathlib import Path

from provenance import generation_stamp
from terminology_from_data_dictionary.model import Output


def write_cql_library_to_file(output: Output, filename, library_name, concept_definition_name):
    """Writes drug concepts to a CQL file."""
    print(f"Writing {len(output.concept_sets)} concept sets to {filename}")
    concept_sets_sorted = sorted(output.concept_sets, key=lambda x: x.name)
    concept_sets_comments = "// Concept set(s)\n"
    for concept_set in concept_sets_sorted:
        concept_set_name = concept_set.name
        concept_set_size = len(concept_set.expression)
        concept_set_modification_date = concept_set.concept_set.get("modifiedDate")
        concept_sets_comments += f"// * {concept_set_name} ({concept_set_size} direct entries) [modified {concept_set_modification_date}]\n"

    stamp = "".join(f"// {line}\n" for line in generation_stamp())
    with open(filename, 'w') as file:
        file.write(f"""// This file has been generated automatically
{stamp}//
{concept_sets_comments}
// Do not edit

library "{library_name}"

include IndicateQiElements called E

""")
        # Write individual codes
        sorted_concepts = sorted(output.concepts, key=lambda x: x.name.lower())
        max_length = max( len(concept_output.name) for concept_output in sorted_concepts )
        for concept_output in sorted_concepts:
            padded_name = f'"{concept_output.name}":' + ' '*(max_length - len(concept_output.name))
            system = 'E."OMOPSV Hierarchy"' if concept_output.descendants else 'E.OMOPSV'
            file.write(f"code {padded_name} '{concept_output.concept_id}' from {system}\n")
        # Write concept
        concept_lines =  ',\n  '.join( f'"{concept_output.name}"'
                                       for concept_output in sorted_concepts )
        file.write(f"""
concept "{concept_definition_name}": {{
  {concept_lines}
}}
""")


def write_cql_library(output: Output, cql_directory: Path, library_name: str, concept_definition_name):
    filename = cql_directory /  f"{library_name}.cql"
    write_cql_library_to_file(output, filename, library_name, concept_definition_name)


def cql_library_name(concept_set_name: str) -> str:
    """Turn a concept set name into a name for a CQL library and its file.

    Everything that is not a letter or a digit (spaces, commas, brackets, ...) is removed and every
    word starts with a capital letter, for example "Glucose in blood" becomes "GlucoseInBlood"."""
    concept_set_name = re.sub(r"['’]", "", concept_set_name)  # "A's" becomes "As", not "A S"
    words = re.findall(r"[A-Za-z0-9]+", concept_set_name)
    name = "".join(word[0].upper() + word[1:] for word in words)
    if not name:
        raise RuntimeError(f"Cannot make a CQL library name from the concept set name '{concept_set_name}'")
    return name


def check_cql_library_names(concept_set_names):
    """Return a dict from library name to concept set name. Raise an error if two concept sets would get the same library name."""
    names = dict()
    for concept_set_name in concept_set_names:
        library_name = cql_library_name(concept_set_name)
        if library_name in names and names[library_name] != concept_set_name:
            raise RuntimeError(f"The concept sets '{names[library_name]}' and '{concept_set_name}' both give the CQL library name {library_name}")
        names[library_name] = concept_set_name
    return names
