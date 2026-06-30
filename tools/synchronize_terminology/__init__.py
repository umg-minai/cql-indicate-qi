import json
import pathlib
import sys

sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())
from data_dictionary import load_resolved_concept_sets
from cql import retrieve_used_concepts
from analysis import concept_set_usage

UI_URL = "https://indicate-eu.github.io/data-dictionary"
PROJECT_INFO_URL = "https://github.com/indicate-eu/data-dictionary/blob/main/projects/5.json"

ATHENA_URL = "https://athena.ohdsi.org"


def format_concept_set(concept_set_id, concept_set_name):
    return f"\033]8;;{UI_URL}/#/concept-sets?id={concept_set_id}\033\\{concept_set_name} ({concept_set_id})\033]8;;\033\\"


def format_concept(concept_id, concept_name):
    label = concept_name or '«no name»'
    if len(label) > 80:
        label = label[:80] + '…'
    if concept_id < 2000000000:
        return f"\033]8;;{ATHENA_URL}/search-terms/terms/{concept_id}\033\\{label} ({concept_id})\033]8;;\033\\"
    else:
        return f"{label} ({concept_id}, custom concept)"


def synchronize():
    all_concept_sets = load_resolved_concept_sets()[0]
    all_concept_sets = list(all_concept_sets.values())
    # For concepts that are used in CQL libraries (modulo imperfect
    # precision of the analysis), find the data dictionary concept
    # sets in which the concepts are defined.
    used_concept_sets = retrieve_used_concepts()
    used_concept_sets, unmapped_concepts \
        = concept_set_usage(used_concept_sets, all_concept_sets)

    print(f"\033[1mThe CQL libraries use {len(used_concept_sets)} of {len(all_concept_sets)} concept sets\033[0m")
    for concept_set in sorted(used_concept_sets, key=lambda concept_set: concept_set.get("name")):
        concept_set_id        = concept_set.get("conceptSetId")
        concept_set_name      = concept_set.get('name')
        all_concepts          = concept_set.get('resolvedConcepts')
        used_concepts         = concept_set.get("used_concepts", dict())
        unreferenced_concepts = [ item
                                  for item in all_concepts
                                  if not item.get("conceptId", None) in used_concepts.keys() ]
        deprecated            = concept_set.get("deprecated")
        if deprecated:
            print("\033[31m", end='')
        print(f"* {format_concept_set(concept_set_id, concept_set_name)}, {len(all_concepts)} concept(s)")
        if deprecated:
            print("\033[0m", end='')
        def map_with_limit(collection, function, limit=5):
            for element in collection[:limit]:
                function(element)
            if len(collection) > limit:
                print(f"  … {len(collection) - limit} more")
        if unreferenced_concepts:
            print(f"  \033[33mThe following {len(unreferenced_concepts)} concept(s) of {len(all_concepts)} total concept(s) are not referenced by any CQL library:\033[0m")
            def print_unreferenced(concept):
                concept_id   = concept.get("conceptId")
                concept_name = concept.get("conceptName")
                print(f"  * {format_concept(concept_id, concept_name)}")
            map_with_limit(
                sorted(unreferenced_concepts, key=lambda concept: concept.get("conceptName")),
                print_unreferenced)
        if deprecated or unreferenced_concepts:
            print(f"  \033[1mUsed by the following {len(used_concepts)} concept(s)")
            def print_used(concept):
                concept_id      = int(concept.get('id'))
                concept_name    = concept.get('name')
                using_libraries = concept.get("usingLibraries", [])
                print(f"  * {', '.join(using_libraries)}: {format_concept(concept_id, concept_name)}")
            map_with_limit(
                sorted(used_concepts.values(), key=lambda concept: concept.get("name")),
                print_used)
            print("\033[0m", end="")

    print(f"\n\033[1mJSON-formatted for updating \033]8;;{PROJECT_INFO_URL}\033\\{PROJECT_INFO_URL}\033]8;;\033\\:\033[0m")
    print(f"  {json.dumps(sorted( concept_set.get('conceptSetId') for concept_set in used_concept_sets))}")

    if unmapped_concepts:
        print(f"\n\033[33mThe following {len(unmapped_concepts)} concept(s) are used by CQL libraries but are not contained in any concept set:\033[0m")
        for concept in sorted(unmapped_concepts, key=lambda x: x.get("name") or ""):
            concept_id   = int(concept.get('id'))
            concept_name = concept.get('name')
            print(f"* {format_concept(concept_id, concept_name)}")

    return used_concept_sets


if __name__ == '__main__':
    synchronize()
