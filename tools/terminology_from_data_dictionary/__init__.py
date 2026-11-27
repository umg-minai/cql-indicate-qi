import pathlib
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import yaml

from data_dictionary import load_concept_sets, load_resolved_concept_sets
from terminology_from_data_dictionary.model import Configuration, ConceptSetMapping, CategoryMapping, \
    OMOPConceptReference, PriorityEntry, Output, ConceptOutput, ConceptSetInfo
from terminology_from_data_dictionary.cql import write_cql_library, cql_library_name, check_cql_library_names
from terminology_from_data_dictionary.markdown import update_markdown_files, concept_sort_key
from terminology_from_data_dictionary.project import load_project_concept_sets
import cql as cql_on_omop
from provenance import generation_info
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
                   only: Optional[List[OMOPConceptReference]] = None,
                   no_classification: bool = False):
    """If no_classification is set, classification concepts (standardConcept C) are left out,
    because they cannot be mapping targets."""
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

    if use_expressions and priorities:
        expression_ids = {item["concept"]["conceptId"] for request in concept_sets for item in request.expression}
        if any(entry.concept_id not in expression_ids for entry in priorities):
            use_expressions = False

    if use_expressions and no_classification:
        for request in concept_sets:
            for item in request.expression:
                if item.get("concept", {}).get("standardConcept") == "C" and item.get("includeDescendants"):
                    print("  Using resolved concept set because of a classification concept with descendants")
                    use_expressions = False

    if use_expressions:
        for request in concept_sets:
            items = request.expression
            for item in items:
                concept = item.get("concept")
                if no_classification and concept.get("standardConcept") == "C":
                    continue
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
                if no_classification and resolved_concept.get("standardConcept") == "C":
                    continue
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
                                                 vocabulary or included.vocabulary or "", concept_code)
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
            concepts[concept_id].redundancy_group = entry.redundancy_group
            concepts[concept_id].is_preferred = entry.is_preferred

    groups = dict()
    for concept in concepts.values():
        if concept.redundancy_group is not None:
            groups.setdefault(concept.redundancy_group, []).append(concept)
    for group_name, members in groups.items():
        preferred = [member for member in members if member.is_preferred]
        if len(members) < 2 or len(preferred) != 1:
            raise RuntimeError(f"Redundancy group '{group_name}' needs at least two concepts and exactly one preferred concept, "
                               f"found {len(members)} concepts and {len(preferred)} preferred")

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


def generate_cql(output_directory, project_id=5):
    """Write a CQL library for every concept set of a project, unless config.yaml says cql: false or used: false for it.
    Also for every category in config.yaml and for every additional concept set."""
    configuration, outputs = prepare()
    concept_sets, repository_url, commit = load_concept_sets()
    resolved_concept_sets, _, _ = load_resolved_concept_sets()
    context = Context(concept_sets, resolved_concept_sets, repository_url, commit)
    entries = load_project_concept_sets(project_id, concept_sets, resolved_concept_sets)

    config_mappings = {mapping.name: mapping for mapping in configuration.mappings
                       if isinstance(mapping, ConceptSetMapping)}
    project_names = {entry.info.name for entry in entries}
    for name in config_mappings:
        if name not in project_names:
            raise RuntimeError(f"config.yaml has an entry for '{name}', which is not a concept set of project {project_id}")

    def definition_name(name, explicit=None):
        return explicit or " ".join(re.split("(?<=[a-z])(?=[A-Z])", name))

    libraries = []  # library name, name of the concept in the library, output, definition of the concepts
    for output, mapping in zip(outputs, configuration.mappings):
        if isinstance(mapping, CategoryMapping):
            libraries.append((mapping.name, definition_name(mapping.name, mapping.cql_definition), output, None))
    for entry in entries:
        mapping = config_mappings.get(entry.info.name)
        if mapping is not None and not (mapping.cql and mapping.used):
            continue
        if mapping is None:
            output = compute_output(context, [entry.info], [], [])
        else:
            output = compute_output(context, [entry.info], mapping.include, mapping.exclude,
                                    mapping.priorities, mapping.only)
        libraries.append((entry.info.name, definition_name(entry.info.name, mapping.cql_definition if mapping else None),
                          output, None))
    # Concept sets that are defined in config.yaml and are not in the data dictionary
    for additional in configuration.additional_concept_sets:
        concepts = [ConceptOutput(None, concept.concept_id, concept.name, concept.descendants,
                                  concept.vocabulary or context.concept_details.get(concept.concept_id, ("", ""))[0])
                    for concept in additional.concepts]
        libraries.append((additional.name, additional.name, Output([], concepts, repository_url, commit),
                          additional.concepts_define))

    # every library is named by cql_library_name; two concept sets must not give the same name
    check_cql_library_names([name for name, _, _, _ in libraries])
    for name, definition, output, concepts_define in libraries:
        write_cql_library(output, output_directory, cql_library_name(name), definition, concepts_define)


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
        if not mapping.used:
            raise RuntimeError(f"A markdown file injects the concept set '{name}', but config.yaml says used: false for it")
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


def generate_concept_set_list(output_file, project_id=5, cql_directory="../cql", jar=cql_on_omop.JAR_FILENAME):
    """Write the concept sets of a project, with the rules from config.yaml applied, to a yaml file."""
    with open(CONFIG_FILE) as file:
        configuration = Configuration.model_validate(yaml.safe_load(file))

    concept_sets, repository_url, commit = load_concept_sets()
    resolved_concept_sets, _, _ = load_resolved_concept_sets()
    context = Context(concept_sets, resolved_concept_sets, repository_url, commit)
    entries = load_project_concept_sets(project_id, concept_sets, resolved_concept_sets)

    # domain of every concept, to derive omop_record
    domain_of = {}
    for concept_set in concept_sets.values():
        for item in concept_set["expression"]["items"]:
            domain_of[item["concept"]["conceptId"]] = item["concept"]["domainId"]
    for resolved in resolved_concept_sets.values():
        for concept in resolved["resolvedConcepts"]:
            domain_of.setdefault(concept["conceptId"], concept["domainId"])
    omop_records = {"Measurement": "Measurement", "Procedure": "ProcedureOccurrence", "Drug": "DrugExposure",
                    "Condition": "ConditionOccurrence", "Observation": "Observation", "Device": "DeviceExposure"}
    included_records = {included.concept_id: included.omop_record
                        for mapping in configuration.mappings for included in mapping.include
                        if included.omop_record}

    def omop_record(concept_id):
        if concept_id in included_records:
            return included_records[concept_id]
        domain = domain_of.get(concept_id)
        if domain not in omop_records:
            raise RuntimeError(f"No omop_record known for domain {domain} of concept {concept_id}")
        return omop_records[domain]

    # The QIs that use a concept: the QI libraries that cql-on-omop names in usingLibraries
    qi_of_concept = cql_on_omop.qi_of_concepts(cql_on_omop.retrieve_qi_usage(cql_directory, jar))

    def qis_of(concept_ids):
        return sorted(set().union(*(qi_of_concept.get(concept_id, set()) for concept_id in concept_ids)))

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
        if mapping and not mapping.used:
            print(f"Concept set {info.name} is not used")
            continue
        if mapping:
            print(f"Concept set {info.name}")
            output = compute_output(context, [info], mapping.include, mapping.exclude,
                                    mapping.priorities, mapping.only, no_classification=True)
        else:
            output = compute_output(context, [info], [], [], no_classification=True)
        concepts = []
        for concept in sorted(output.concepts, key=concept_sort_key):
            item = {"concept_id": concept.concept_id,
                    "name": concept.name,
                    "omop_record": omop_record(concept.concept_id),
                    "with_descendants": bool(concept.descendants)}
            if concept.priority is not None:
                item["priority"] = concept.priority
            if concept.redundancy_group is not None:
                item["redundancy_group"] = concept.redundancy_group
                item["is_preferred"] = concept.is_preferred
            concepts.append(item)
        ids = {item["concept_id"] for item in concepts}
        if any(item["with_descendants"] for item in concepts):
            resolved = resolved_concept_sets.get(info.concept_set_id)
            if resolved:
                ids |= {concept["conceptId"] for concept in resolved["resolvedConcepts"]}
        result.append({"name": info.name,
                       "concept_set_id": info.concept_set_id,
                       "version": entry.version,
                       "project_group": entry.group,
                       "qi": qis_of(ids),
                       "concepts": concepts})

    project_names = {entry.info.name for entry in entries}
    for additional in configuration.additional_concept_sets:
        if additional.name in project_names:
            raise RuntimeError(f"Additional concept set '{additional.name}' has the same name as a concept set of project {project_id}")
        result.append({"name": additional.name,
                       "project_group": "additional",
                       "qi": qis_of({concept.concept_id for concept in additional.concepts}),
                       "concepts": [{"concept_id": concept.concept_id,
                                     "name": concept.name,
                                     "omop_record": additional.omop_record,
                                     "with_descendants": concept.descendants}
                                    for concept in additional.concepts]})

    document = {"generated": {"project_id": project_id, **generation_info()}, "concept_sets": result}
    output_file.write_text("# Generated file, do not edit.\n"
                           + yaml.safe_dump(document, sort_keys=False, allow_unicode=True, width=200))
    print(f"Wrote {len(result)} concept sets with {sum(len(e['concepts']) for e in result)} concepts to {output_file}")
