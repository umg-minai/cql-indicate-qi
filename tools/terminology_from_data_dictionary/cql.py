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
