import pathlib
import re
from dataclasses import dataclass
from typing import Dict, List

import yaml

from data_dictionary import load_concept_sets, load_resolved_concept_sets
from terminology_from_data_dictionary.model import Configuration, ConceptSetMapping, CategoryMapping, \
    OMOPConceptReference, Output, ConceptOutput, ConceptSetInfo
from terminology_from_data_dictionary.cql import write_cql_library
from terminology_from_data_dictionary.markdown import update_markdown_files
from utilities import format_concept_for_terminal


@dataclass
class Context:
    concept_sets: Dict[int, Dict]
    resolved_concept_sets: Dict[int, Dict]
    repository_url: str
    commit: str


def compute_output(context: Context,
                   concept_sets: List[ConceptSetInfo],
                   include: List[OMOPConceptReference],
                   exclude: List[OMOPConceptReference]):
    """Return the effective concepts that should be emitted, for example into a CQL library or Markdown table."""
    concepts: Dict[int, ConceptOutput] = dict()
    # Can we use the expression?
    use_expressions = True
    if exclude:
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
    print("  Using resolved concept set because of exclusions")

    if use_expressions:
        # Using expressions: go through the "unresolved" concept sets and collect the individual concepts, possibly
        # with descendants but definitely without exclusions.
        for request in concept_sets:
            items = request.expression
            for item in items:
                concept = item.get("concept")
                concept_id = concept.get("conceptId")
                concept_name = concept.get("conceptName")
                include_descendants = item.get("includeDescendants")
                concepts[concept_id] = ConceptOutput(request, concept_id, concept_name, include_descendants)
    else:
        for request in concept_sets:
            resolved_concepts = request.resolved_concepts
            for resolved_concept in resolved_concepts:
                concept_id = resolved_concept.get("conceptId")
                concept_name = resolved_concept.get("conceptName")
                concepts[concept_id] = ConceptOutput(request, concept_id, concept_name)

    # Add and/or remove additional concepts
    for included in include:
        concept_id = included.concept_id
        if concept_id in concepts:
            raise RuntimeError(f"Explicitly included concept {format_concept_for_terminal(concept_id, included.name)} is present in concept set(s)")
        else:
            print(f"  Including additional concept {format_concept_for_terminal(concept_id, included.name)}")
            concepts[concept_id] = ConceptOutput(None, concept_id, included.name, included.descendants)
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

    return Output(concept_sets,
                  list(sorted(concepts.values(), key=lambda x: x.name)),
                  context.repository_url,
                  context.commit)


def make_generation_request(context: Context, concept_set_id: int):
    return ConceptSetInfo(context.concept_sets[concept_set_id],
                          context.resolved_concept_sets[concept_set_id])


def resolve_concept_set_ids(context: Context, concept_set_ids: List[int]):
    return [ make_generation_request(context, concept_set_id) for concept_set_id in concept_set_ids ]


def resolve_categories(context: Context, category, subcategory):
    def is_matching_concept_set(concept_set):
        metadata = concept_set.get("metadata", {})
        en = metadata.get("translations", {}).get("en", {})
        return not metadata.get('reviewStatus') == 'deprecated' \
            and en.get("category") == category \
            and en.get("subcategory") == subcategory
    return [ make_generation_request(context, concept_set_id)
             for concept_set_id, concept_set in context.concept_sets.items()
             if is_matching_concept_set(concept_set) ]


# Entry points

CONFIG_FILE = pathlib.Path(__file__).parent / 'config.yaml'


def prepare():
    with open(CONFIG_FILE) as file:
        data = yaml.safe_load(file)
        configuration = Configuration.model_validate(data)

    concept_sets,          repository_url,  commit  = load_concept_sets()
    resolved_concept_sets, repository_url2, commit2 = load_resolved_concept_sets()
    assert repository_url == repository_url2
    assert commit         == commit2
    context = Context(concept_sets, resolved_concept_sets, repository_url, commit)

    outputs = []
    for mapping in configuration.mappings:
        match mapping:
          case ConceptSetMapping(concept_sets=concept_sets):
            generation_requests = resolve_concept_set_ids(context, concept_sets)
          case CategoryMapping(category=category, subcategory=subcategory):
            generation_requests = resolve_categories(context, category, subcategory)
          case _:
            raise RuntimeError("Unreachable")
        outputs.append(compute_output(context, generation_requests, mapping.include, mapping.exclude))

    return configuration, outputs


def generate_cql(output_directory):
    configuration, outputs = prepare()
    for output, mapping in zip(outputs, configuration.mappings):
        cql_definition = mapping.cql_definition
        if cql_definition is None:
            cql_definition = ' '.join(re.split("(?<=[a-z])(?=[A-Z])", mapping.name))
        write_cql_library(output, output_directory, mapping.name, cql_definition)


def generate_markdown(output_directory):
    configuration, outputs = prepare()
    outputs_by_key = dict()
    for output, mapping in zip(outputs, configuration.mappings):
        outputs_by_key[mapping.name] = output
    update_markdown_files(outputs_by_key, output_directory)
