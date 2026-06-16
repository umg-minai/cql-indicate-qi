import json
import pathlib
import subprocess
import sys

sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())
import data_dictionary.load

UI_URL = "https://indicate-eu.github.io/data-dictionary"
PROJECT_INFO_URL = "https://github.com/indicate-eu/data-dictionary/blob/main/projects/5.json"

ATHENA_URL = "https://athena.ohdsi.org"

def retrieve_cql_data():
    print("Collecting used concepts from CQL libraries")
    try:
        process = subprocess.run(['java',
                                  '-jar', '../cql-on-omop.jar',
                                  'terminology', '--resolve-concepts',
                                  '--omop-version', 'v5.4',
                                  '-p', '5432', '-u', 'postgres', '--password', 'yourpassword', '-d', 'ohdsi',
                                  '-I', '../../cql/',
                                  'Main'],
                                  capture_output=True,
                                  text=True)
        output = process.stdout
        if process.returncode != 0:
            error = process.stderr
            print(f"Error running cql-on-omop program: \n{error}{output}")
            return None

        # Assuming the Java program outputs valid JSON
        try:
            data = json.loads(output)
            return data
        except json.JSONDecodeError as e:
            print(f"Error decoding JSON: {e}")
            return None
    except subprocess.CalledProcessError as e:
        print(f"Error running cql-on-omop program: {e}")
        return None

# These concepts are described in INDICATE's general mapping
# recommendations rather than specific concept sets.
IGNORED_CONCEPT_IDS = {
    8532,  # FEMALE
    8507,  # MALE
    32037, # Intensive Care
}

def format_concept_set(concept_set_id, concept_set_name):
    return f"\033]8;;{UI_URL}/#/concept-sets?id={concept_set_id}\033\\{concept_set_name} ({concept_set_id})\033]8;;\033\\"

def format_concept(concept_id, concept_name):
    label = concept_name or '«no name»'
    if concept_id < 2000000000:
        return f"\033]8;;{ATHENA_URL}/search-terms/terms/{concept_id}\033\\{label} ({concept_id})\033]8;;\033\\"
    else:
        return f"{label} ({concept_id}, custom concept)"

def synchronize():
    cql_data = retrieve_cql_data()
    all_concept_sets = data_dictionary.load.load_resolved_concept_sets()[0]
    all_concept_sets = list(all_concept_sets.values())
    concept_id_to_concept_set = dict()
    for concept_set in all_concept_sets:
        for concept in concept_set.get('resolvedConcepts', []):
            concept_id = concept.get('conceptId')
            if concept_id in concept_id_to_concept_set:
                concept_id_to_concept_set[concept_id].append(concept_set)
            else:
                concept_id_to_concept_set[concept_id] = [ concept_set ]
    used_concept_sets = []
    unmapped_concepts = []
    for concept in cql_data:
        concept_id = int(concept.get("id"))
        if concept_id in IGNORED_CONCEPT_IDS:
            continue
        found = False
        for concept_set in concept_id_to_concept_set.get(concept_id, {}):
            found = True
            if not any( old_concept_set for old_concept_set in used_concept_sets
                        if old_concept_set.get("conceptSetId") == concept_set.get("conceptSetId") ):
                used_concept_sets.append(concept_set)
            used_concepts = None
            if not 'used_concepts' in concept_set:
                used_concepts = set()
                concept_set["used_concepts"] = used_concepts
            else:
                used_concepts = concept_set.get("used_concepts")
            used_concepts.add(concept_id)
        if not found:
            unmapped_concepts.append(concept)

    print(f"\033[1mThe CQL libraries use {len(used_concept_sets)} of {len(all_concept_sets)} concept sets\033[0m")
    for concept_set in sorted(used_concept_sets, key=lambda concept_set: concept_set.get("name")):
        concept_set_id        = concept_set.get("conceptSetId")
        concept_set_name      = concept_set.get('name')
        all_concepts          = concept_set.get('resolvedConcepts')
        used_concepts         = concept_set.get("used_concepts", set())
        unreferenced_concepts = [ item
                                  for item in all_concepts
                                  if not item.get("conceptId", None) in used_concepts ]
        print(f"* {format_concept_set(concept_set_id, concept_set_name)}, {len(all_concepts)} concept(s)")
        if unreferenced_concepts:
            print(f"  \033[33mThe following {len(unreferenced_concepts)} concept(s) of {len(all_concepts)} total concept(s) are not referenced by any CQL library:\033[0m")
            limit = 5
            for concept in sorted(unreferenced_concepts, key=lambda concept: concept.get("conceptName"))[:limit]:
                concept_id   = concept.get("conceptId")
                concept_name = concept.get("conceptName")
                print(f"  * {format_concept(concept_id, concept_name)}")
            if len(unreferenced_concepts) > limit:
                print(f"  … {len(unreferenced_concepts) - limit} more")

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
