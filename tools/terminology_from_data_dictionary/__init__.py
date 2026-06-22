import pprint
import json
import pathlib
import sys

sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())
import data_dictionary.load


def generate_library_for_category(concept_sets,
                                  category,
                                  subcategory,
                                  library_name,
                                  concept_definition_name,
                                  repository_url,
                                  commit):
    """Generates a CQL library for a specific drug category."""

    def is_matching_concept_set(concept_set):
        metadata = concept_set.get("metadata", {})
        en = metadata.get("translations", {}).get("en", {})
        return not metadata.get('reviewStatus') == 'deprecated' \
            and en.get("category") == category \
            and en.get("subcategory") == subcategory
    relevant_concept_sets = [concept_set for concept_set in concept_sets if is_matching_concept_set(concept_set)]

    write_drugs_to_file(relevant_concept_sets,
                        f"../../cql/{library_name}.cql",
                        library_name,
                        concept_definition_name,
                        repository_url,
                        commit)


def write_drugs_to_file(concept_sets,
                        filename,
                        library_name,
                        concept_definition_name,
                        repository_url,
                        commit):
    """Writes drug concepts to a CQL file."""
    print(f"Writing {len(concept_sets)} concept sets to {filename}")
    concept_sets_sorted = sorted(concept_sets, key=lambda concept_set: concept_set.get("name"))
    concept_sets_comments = "// Concept set(s)\n"
    for concept_set in concept_sets_sorted:
        concept_set_name = concept_set.get("name")
        concept_set_size = len(concept_set.get("expression", {}).get("items"))
        concept_set_modification_date = concept_set.get("modifiedDate")
        concept_sets_comments += f"// * {concept_set_name} ({concept_set_size} direct entries) [modified {concept_set_modification_date}]\n"
    with open(filename, 'w') as file:
        file.write(f"""// This file has been generated automatically from
// commit {commit} or {repository_url}
{concept_sets_comments}
// Do not edit

library "{library_name}"

include IndicateQiElements called E

""")
        entries = {}
        for concept_set in concept_sets_sorted:
            items = concept_set.get("expression", {}).get("items")
            for item in items:
                concept = item.get("concept")
                concept_id = concept.get("conceptId")
                concept_name = concept.get("conceptName")
                include_descendants = item.get("includeDescendants")
                entries[concept_name] = (concept_id, include_descendants)

        for concept_name, (concept_id, include_descendants) in sorted(entries.items(), key=lambda x: x[0].lower()):
            system = 'E."OMOPSV Hierarchy"' if include_descendants else 'E.OMOPSV'
            file.write(f"code \"{concept_name}\": '{concept_id}' from {system}\n")

        file.write(f"\nconcept \"{concept_definition_name}\": {{")
        is_first = True
        for concept_name in sorted(entries.keys(), key=lambda x: x.lower()):
            if is_first:
                is_first = False
            else:
                file.write(",")
            file.write(f"\n  \"{concept_name}\"")
        file.write("\n}\n")


def main():
    """Main function to fetch data and generate libraries."""
    concept_sets, repository_url, commit \
        = data_dictionary.load.load_concept_sets()

    generate_library_for_category(concept_sets.values(),
                                  "Medications",
                                  "Other drugs",
                                  'InsulinDrugs',
                                  'Insulin Drugs',
                                  repository_url,
                                  commit)

    generate_library_for_category(concept_sets.values(),
                                  "Medications",
                                  'Anticoagulants',
                                  'AnticoagulationDrugs',
                                  'Anticoagulation Drugs',
                                  repository_url,
                                  commit)

    return None


if __name__ == "__main__":
    main()
