import pathlib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml

from data_dictionary import load_concept_sets, load_resolved_concept_sets
from terminology_from_data_dictionary.model import Configuration, ConceptSetMapping, CategoryMapping, \
    OMOPConceptReference, PriorityEntry, Output, ConceptOutput, ConceptSetInfo
from terminology_from_data_dictionary.cql import write_cql_library
from terminology_from_data_dictionary.markdown import update_markdown_files, concept_sort_key
from terminology_from_data_dictionary.project import load_project_concept_sets
from utilities import format_concept_for_terminal


@dataclass
class Context:
    concept_sets: Dict[int, Dict]
    resolved_concept_sets: Dict[int, Dict]
    repository_url: str
    commit: str
    # concept_id -> (vocabulary, concept code); used for concepts added via "include"
    concept_details: Dict[int, tuple] = field(init=False, default_factory=dict)

    def __post_init__(self):
        for concept_set in self.concept_sets.values():
            for item in concept_set.get("expression", {}).get("items", []):
                concept = item.get("concept", {})
                self.concept_details[concept.get("conceptId")] = (concept.get("vocabularyId", ""),
                                                                  concept.get("conceptCode", ""))
        for resolved in self.resolved_concept_sets.values():
            for concept in resolved.get("resolvedConcepts", []):
                self.concept_details.setdefault(concept.get("conceptId"),
                                                (concept.get("vocabularyId", ""),
                                                 concept.get("conceptCode", "")))


def compute_output(context: Context,
                   concept_sets: List[ConceptSetInfo],
                   include: List[OMOPConceptReference],
                   exclude: List[OMOPConceptReference],
                   priorities: Optional[List[PriorityEntry]] = None,
                   only: Optional[List[OMOPConceptReference]] = None):
    concepts: Dict[int, ConceptOutput] = dict()
    use_expressions = True
    if exclude or only:
        use_expressions = False
    else:
        for request in concept_sets:
            if not use_expressions:
                break
            items = request.expression
            for item in items:
                if item.get("isExcluded"):
                    use_expressions = False
                    break

    if use_expressions:
        for request in concept_sets:
            items = request.expression
            for item in items:
                concept = item.get("concept")
                concept_id = concept.get("conceptId")
                concept_name = concept.get("conceptName")
                include_descendants = item.get("includeDescendants")
                concepts[concept_id] = ConceptOutput(request, concept_id, concept_name, include_descendants,
                                                     concept.get("vocabularyId", ""),
                                                     concept.get("conceptCode", ""))
    else:
        print("  Using resolved concept set because of exclusions or restriction")
        for request in concept_sets:
            resolved_concepts = request.resolved_concepts
            for resolved_concept in resolved_concepts:
                concept_id = resolved_concept.get("conceptId")
                concept_name = resolved_concept.get("conceptName")
                concepts[concept_id] = ConceptOutput(request, concept_id, concept_name, False,
                                                     resolved_concept.get("vocabularyId", ""),
                                                     resolved_concept.get("conceptCode", ""))

    if only:
        selected: Dict[int, ConceptOutput] = dict()
        for entry in only:
            concept_id = entry.concept_id
            if concept_id not in concepts:
                raise RuntimeError(f"Concept {format_concept_for_terminal(concept_id, entry.name)} listed under 'only' is not present in concept set(s)")
            elif not entry.name == concepts[concept_id].name:
                actual = concepts[concept_id]
                raise RuntimeError(f"Name of concept {format_concept_for_terminal(concept_id, entry.name)} listed under 'only' does not match name of {format_concept_for_terminal(actual.concept_id, actual.name)} in concept set")
            else:
                concepts[concept_id].descendants = entry.descendants
                selected[concept_id] = concepts[concept_id]
        print(f"  Restricted to {len(selected)} of {len(concepts)} concepts")
        concepts = selected

    for included in include:
        concept_id = included.concept_id
        if concept_id in concepts:
            raise RuntimeError(f"Explicitly included concept {format_concept_for_terminal(concept_id, included.name)} is present in concept set(s)")
        else:
            print(f"  Including additional concept {format_concept_for_terminal(concept_id, included.name)}")
            vocabulary, concept_code = context.concept_details.get(concept_id, ("", ""))
            concepts[concept_id] = ConceptOutput(None, concept_id, included.name, included.descendants,
                                                 vocabulary, concept_code)
    for excluded in exclude:
        if excluded.descendants:
            raise RuntimeError(f"Excluding concepts with descendants is not implemented")
        concept_id = excluded.concept_id
        if concept_id not in concepts:
            raise RuntimeError(f"Explicitly excluded concept {format_concept_for_terminal(concept_id, excluded.name)} is not present in concept set(s)")
        elif not excluded.name == concepts[concept_id].name:
            concept_set_concept = concepts[concept_id]
            raise RuntimeError(f"Name of explicitly excluded concept {format_concept_for_terminal(concept_id, excluded.name)} does not match name of {format_concept_for_terminal(concept_set_concept.concept_id, concept_set_concept.name)} in concept set")
        else:
            print(f"  Excluding concept {format_concept_for_terminal(concept_id, excluded.name)}")
            del concepts[concept_id]

    for entry in (priorities or []):
        concept_id = entry.concept_id
        if concept_id not in concepts:
            raise RuntimeError(f"Priority entry for concept {format_concept_for_terminal(concept_id, entry.name)} is not present in concept set(s)")
        elif not entry.name == concepts[concept_id].name:
            actual = concepts[concept_id]
            raise RuntimeError(f"Name of priority entry {format_concept_for_terminal(concept_id, entry.name)} does not match name of {format_concept_for_terminal(actual.concept_id, actual.name)} in concept set")
        else:
            concepts[concept_id].priority = entry.priority

    return Output(concept_sets,
                  list(sorted(concepts.values(), key=lambda x: x.name)),
                  context.repository_url,
                  context.commit)


def make_generation_request(context: Context, concept_set_id: int):
    return ConceptSetInfo(context.concept_sets[concept_set_id],
                          context.resolved_concept_sets[concept_set_id])


def resolve_concept_set_name(context: Context, name: str):
    """Look up a concept set by exact name in the data dictionary. Raises RuntimeError if not found."""
    for cs_id, cs in context.concept_sets.items():
        if cs.get('name') == name:
            return make_generation_request(context, cs_id)
    raise RuntimeError(f"Concept set with name '{name}' not found in data dictionary.")


def resolve_concept_set_names(context: Context, concept_set_names: List[str]):
    return [resolve_concept_set_name(context, name) for name in concept_set_names]


def resolve_categories(context: Context, category, subcategory):
    def is_matching_concept_set(concept_set):
        metadata = concept_set.get("metadata", {})
        en = metadata.get("translations", {}).get("en", {})
        return not metadata.get('reviewStatus') == 'deprecated' \
            and en.get("category") == category \
            and en.get("subcategory") == subcategory
    return [make_generation_request(context, concept_set_id)
            for concept_set_id, concept_set in context.concept_sets.items()
            if is_matching_concept_set(concept_set)]


CONFIG_FILE = pathlib.Path(__file__).parent / 'config.yaml'


def prepare():
    with open(CONFIG_FILE) as file:
        data = yaml.safe_load(file)
        configuration = Configuration.model_validate(data)

    concept_sets, repository_url, commit = load_concept_sets()
    resolved_concept_sets, repository_url2, commit2 = load_resolved_concept_sets()
    assert repository_url == repository_url2
    assert commit == commit2
    context = Context(concept_sets, resolved_concept_sets, repository_url, commit)

    outputs = []
    for mapping in configuration.mappings:
        priorities = []
        only = []
        match mapping:
            case ConceptSetMapping():
                generation_requests = [resolve_concept_set_name(context, mapping.name)]
                priorities = mapping.priorities
                only = mapping.only
            case CategoryMapping(category=category, subcategory=subcategory):
                generation_requests = resolve_categories(context, category, subcategory)
            case _:
                raise RuntimeError("Unreachable")
        outputs.append(compute_output(context, generation_requests, mapping.include, mapping.exclude, priorities, only))

    return configuration, outputs


def generate_cql(output_directory):
    configuration, outputs = prepare()
    for output, mapping in zip(outputs, configuration.mappings):
        cql_definition = mapping.cql_definition
        if cql_definition is None:
            cql_definition = ' '.join(re.split("(?<=[a-z])(?=[A-Z])", mapping.name))
        write_cql_library(output, output_directory, mapping.name, cql_definition)


def generate_markdown(output_directory):
    with open(CONFIG_FILE) as file:
        data = yaml.safe_load(file)
        configuration = Configuration.model_validate(data)

    concept_sets, repository_url, commit = load_concept_sets()
    resolved_concept_sets, repository_url2, commit2 = load_resolved_concept_sets()
    assert repository_url == repository_url2
    assert commit == commit2
    context = Context(concept_sets, resolved_concept_sets, repository_url, commit)

    # Config entries are looked up by name: the data dictionary concept set name,
    # or the label of a category entry (e.g. "AnticoagulationDrugs").
    config_mappings = {mapping.name: mapping for mapping in configuration.mappings}

    def resolve_name(name: str) -> Output:
        name = name.strip()
        mapping = config_mappings.get(name)
        if mapping is None:
            # No exceptions configured: use the concept set as it is
            return compute_output(context, [resolve_concept_set_name(context, name)], [], [])
        if isinstance(mapping, CategoryMapping):
            generation_requests = resolve_categories(context, mapping.category, mapping.subcategory)
            return compute_output(context, generation_requests, mapping.include, mapping.exclude)
        generation_requests = [resolve_concept_set_name(context, name)]
        return compute_output(context, generation_requests, mapping.include, mapping.exclude,
                              mapping.priorities, mapping.only)

    update_markdown_files(resolve_name, output_directory)


def print_project_concept_sets(project_id):
    concept_sets, repository_url, commit = load_concept_sets()
    resolved_concept_sets, _, _ = load_resolved_concept_sets()
    entries = load_project_concept_sets(project_id, concept_sets, resolved_concept_sets)
    print(f"Project {project_id}: {len(entries)} concept sets (data dictionary commit {commit[:7]})")
    for entry in entries:
        info = entry.info
        note = "  <- loaded from an older commit" if entry.from_history else ""
        print(f"  {entry.group:<20} {info.concept_set_id:>4} {info.name[:50]:<50} "
              f"v{entry.version:<7} {len(info.resolved_concepts):>3} concepts{note}")
    groups = {}
    for entry in entries:
        groups[entry.group] = groups.get(entry.group, 0) + 1
    print("Groups: " + ", ".join(f"{name} ({count})" for name, count in groups.items()))


def generate_concept_set_list(output_file, project_id=5):
    """Write the concept sets of a project, with the rules from config.yaml applied, to a yaml file."""
    with open(CONFIG_FILE) as file:
        configuration = Configuration.model_validate(yaml.safe_load(file))

    concept_sets, repository_url, commit = load_concept_sets()
    resolved_concept_sets, _, _ = load_resolved_concept_sets()
    context = Context(concept_sets, resolved_concept_sets, repository_url, commit)
    entries = load_project_concept_sets(project_id, concept_sets, resolved_concept_sets)

    config_mappings = {mapping.name: mapping for mapping in configuration.mappings
                       if isinstance(mapping, ConceptSetMapping)}
    unknown = sorted(set(config_mappings) - {entry.info.name for entry in entries})
    if unknown:
        raise RuntimeError(f"config.yaml has entries for concept sets that are not in project {project_id}: "
                           + ", ".join(unknown))

    result = []
    for entry in entries:
        info = entry.info
        mapping = config_mappings.get(info.name)
        if mapping:
            print(f"Concept set {info.name}")
            output = compute_output(context, [info], mapping.include, mapping.exclude,
                                    mapping.priorities, mapping.only)
        else:
            output = compute_output(context, [info], [], [])
        concepts = []
        for concept in sorted(output.concepts, key=concept_sort_key):
            item = {"concept_id": concept.concept_id,
                    "name": concept.name,
                    "with_descendants": bool(concept.descendants)}
            if concept.priority is not None:
                item["priority"] = concept.priority
            concepts.append(item)
        result.append({"name": info.name,
                       "concept_set_id": info.concept_set_id,
                       "version": entry.version,
                       "group": entry.group,
                       "concepts": concepts})

    project_names = {entry.info.name for entry in entries}
    for additional in configuration.additional_concept_sets:
        if additional.name in project_names:
            raise RuntimeError(f"Additional concept set '{additional.name}' has the same name as a concept set of project {project_id}")
        result.append({"name": additional.name,
                       "group": "additional",
                       "concepts": [{"concept_id": concept.concept_id,
                                     "name": concept.name,
                                     "with_descendants": concept.descendants}
                                    for concept in additional.concepts]})

    header = (f"# Concept sets of project {project_id} with the rules of config.yaml applied.\n"
              f"# Generated from {repository_url} at commit {commit}.\n"
              f"# Do not edit.\n")
    output_file.write_text(header + yaml.safe_dump(result, sort_keys=False, allow_unicode=True, width=200))
    print(f"Wrote {len(result)} concept sets with {sum(len(e['concepts']) for e in result)} concepts to {output_file}")
