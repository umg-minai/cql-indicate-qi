import copy
import datetime
import pathlib
import sys
from typing import List

sys.path.append(pathlib.Path(__file__).parent.parent.as_posix())
from data_dictionary import load_resolved_concept_sets, load_concept_set_versions, load_project, store_project
from cql import retrieve_used_concepts
from analysis import concept_set_usage


UI_URL = "https://indicate-eu.github.io/data-dictionary"


def format_concept_set(concept_set_id, concept_set_name, concept_set_version):
    return f"\033]8;;{UI_URL}/#/concept-sets?id={concept_set_id}\033\\{concept_set_name} ({concept_set_id})\033]8;;\033\\" \
        + f"; version {concept_set_version}"


def format_concept_set_via_id(concept_set_id, all_concept_sets, concept_set_version):
    concept_set = all_concept_sets[concept_set_id]
    concept_set_name = concept_set.get('name')
    return format_concept_set(concept_set_id, concept_set_name, concept_set_version)


def update():
    project_id = 5

    used_concepts = retrieve_used_concepts()
    all_concept_sets = load_resolved_concept_sets()[0]
    versions = load_concept_set_versions()
    project = load_project(project_id)

    def get_latest_version(concept_set_id):
        cs_versions = versions.get(str(concept_set_id), {})
        if not cs_versions:
            return None
        # Sort versions semantically; the last one is the latest.
        return sorted(cs_versions.keys(), key=lambda v: list(map(int, v.split("."))))[-1]

    used_concept_sets, _ = concept_set_usage(used_concepts, list(all_concept_sets.values()))

    any_change = False
    all_project_concept_sets = {}
    for group in project.get("groups", []):
        for group_concept_set in group.get("conceptSets", []):
            group_concept_set_id = group_concept_set.get("id")
            all_project_concept_sets[group_concept_set_id] = group_concept_set
    unused_project_concept_sets = copy.copy(all_project_concept_sets)

    used_project_concept_sets = {}
    new_project_concept_sets = {}
    for used_concept_set in used_concept_sets:
        used_concept_set_id = used_concept_set.get("conceptSetId")
        referenced_concept_set = all_project_concept_sets.get(used_concept_set_id, None)
        if referenced_concept_set:
            if not used_concept_set_id in used_project_concept_sets:
                used_project_concept_sets[used_concept_set_id] = referenced_concept_set
            del(unused_project_concept_sets[used_concept_set_id])
        else:
            using_libraries = set()
            for used_concept in used_concept_set.get("used_concepts").values():
                for using_library in used_concept.get("usingLibraries", []):
                    using_libraries.add(using_library)
            print(f"New in CQL '{used_concept_set.get("name")}' ({used_concept_set_id}) in {used_concept_set.get("category")}::{used_concept_set.get("subcategory")} libraries {using_libraries}")
            new_project_concept_sets[used_concept_set_id] = {"id": used_concept_set_id,
                                                             "version": get_latest_version(used_concept_set_id)}
            any_change = True

    updated_project_concept_sets = {}
    for concept_set_id, concept_set in used_project_concept_sets.items():
        latest_version = get_latest_version(concept_set_id)
        if not concept_set['version'] == latest_version:
            concept_set['version'] = latest_version
            updated_project_concept_sets[concept_set_id] = concept_set
            any_change = True

    def format_concept_set_changes(concept_sets, color, symbol, heading):
        if concept_sets:
            print(f"\033[{color}m{heading}\033[0m")
            for concept_set in concept_sets:
                concept_set_id      = concept_set.get('id')
                concept_set_version = concept_set.get('version')
                print(f"\033[{color}m{symbol}\033[0m {format_concept_set_via_id(concept_set_id, all_concept_sets, concept_set_version)}")

    format_concept_set_changes(unused_project_concept_sets.values(), 31, '-',
                               'Unused concept sets (will be removed from project)')
    format_concept_set_changes(new_project_concept_sets.values(), 32, '+',
                               'New concept sets (will be added to project)')
    format_concept_set_changes(updated_project_concept_sets.values(), 35, '~',
                               'Updated concept sets')

    if any_change or unused_project_concept_sets:
        total_count = 0
        for group in project.get("groups", []):
            group_concept_sets: List = group.get("conceptSets", [])
            new_group_concept_sets = []
            for concept_set in group_concept_sets:
                concept_set_id = concept_set.get("id", None)
                if not concept_set_id in unused_project_concept_sets:
                    new_group_concept_sets.append(concept_set)
                    total_count += 1
            if group.get("id") == "group-default":
                new_group_concept_sets += new_project_concept_sets.values()
                total_count += 1
            group['conceptSets'] = new_group_concept_sets
        print(f"Total concepts after update: {total_count}")

        # Update metadata.
        today = datetime.date.today().isoformat()
        project["modifiedDate"] = today

        store_project(project_id, project)
    else:
        print(f"\033[2mNo changes\033[0m")


if __name__ == '__main__':
    update()
