from typing import List, Dict


# These concepts are described in INDICATE's general mapping
# recommendations rather than specific concept sets.
IGNORED_CONCEPT_IDS = {
    8532,  # FEMALE
    8507,  # MALE
    32037, # Intensive Care
}


IGNORED_LIBRARIES = { "InsulinIngredients" }


def concept_set_usage(used_concepts: List[Dict],
                      all_concept_sets: List[Dict],
                      ignored_concept_ids: List[int] = None,
                      ignored_libraries: List[str] = None):
    if ignored_concept_ids is None:
        ignored_concept_ids = IGNORED_CONCEPT_IDS
    if ignored_libraries is None:
        ignored_libraries = IGNORED_LIBRARIES
    # Restrict to relevant concepts.
    relevant_used_concepts = [ concept for concept in used_concepts
                               if (set(concept.get("usingLibraries"))
                                   - ignored_libraries) ]
    # Build a map from concept id to concept sets which contain that
    # concept id for quicker lookup.
    concept_id_to_concept_set = dict()
    for concept_set in all_concept_sets:
        for concept in concept_set.get('resolvedConcepts', []):
            concept_id = concept.get('conceptId')
            if concept_id in concept_id_to_concept_set:
                concept_id_to_concept_set[concept_id].append(concept_set)
            else:
                concept_id_to_concept_set[concept_id] = [ concept_set ]
    # For concepts that are used in CQL libraries (modulo imperfect
    # precision of the analysis), find the data dictionary concept
    # sets in which the concepts are defined.
    used_concept_sets = []
    unmapped_concepts = []
    for concept in relevant_used_concepts:
        concept_id = int(concept.get("id"))
        if concept_id in ignored_concept_ids:
            continue
        found = False
        concept_sets = concept_id_to_concept_set.get(concept_id, [])
        if concept_sets:
            found = True
            # If the concept is contained in deprecated concept
            # sets and non-deprecated concept sets, consider only
            # the non-deprecated ones.  Otherwise, consider the
            # deprecated ones as well.
            relevant_concept_sets = [ concept_set
                                      for concept_set in concept_sets
                                      if not concept_set.get("deprecated") ]
            if not relevant_concept_sets:
                 relevant_concept_sets = concept_sets
            for concept_set in relevant_concept_sets:
                if not any( old_concept_set for old_concept_set in used_concept_sets
                            if old_concept_set.get("conceptSetId") == concept_set.get("conceptSetId") ):
                    used_concept_sets.append(concept_set)
                if not 'used_concepts' in concept_set:
                    concepts_used_by_concept_set = dict()
                    concept_set["used_concepts"] = concepts_used_by_concept_set
                else:
                    concepts_used_by_concept_set = concept_set.get("used_concepts")
                concepts_used_by_concept_set[concept_id] = concept
        if not found:
            unmapped_concepts.append(concept)
    return used_concept_sets, unmapped_concepts
