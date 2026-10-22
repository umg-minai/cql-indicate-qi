# General utilities


def maybe_truncate(string: str, max_length: int = 80):
    return string if len(string) <= max_length else string[:max_length - 1] + '…'

# Athena links

ATHENA_URL = "https://athena.ohdsi.org"


def make_athena_url(concept_id):
    return f"{ATHENA_URL}/search-terms/terms/{concept_id}" if concept_id < 2_000_000_000 else None


def format_concept_for_terminal(concept_id, concept_name, max_width=80):
    label = maybe_truncate(concept_name or '«no name»', max_length=max_width)
    url = make_athena_url(concept_id)
    if url:
        return f"\033]8;;{url}\033\\{label} ({concept_id})\033]8;;\033\\"
    else:
        return f"{label} ({concept_id}, custom concept)"


# INDICATE data dictionary links

UI_URL = "https://indicate-eu.github.io/data-dictionary"


def make_concept_set_url(concept_set_id):
    return f"{UI_URL}/#/concept-sets?id={concept_set_id}"


def format_concept_set_for_terminal(concept_set_id, concept_set_name, concept_set_version = None):
    url = make_concept_set_url(concept_set_id)
    return f"\033]8;;{url}\033\\{concept_set_name} ({concept_set_id})\033]8;;\033\\" \
        + (f"; version {concept_set_version}" if concept_set_version else '')


def format_concept_set_for_terminal_via_id(concept_set_id, all_concept_sets, concept_set_version):
    concept_set = all_concept_sets[concept_set_id]
    concept_set_name = concept_set.get('name')
    return format_concept_set_for_terminal(concept_set_id, concept_set_name, concept_set_version)
