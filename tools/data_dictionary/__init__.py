from xdg import xdg_cache_home
import pathlib
import subprocess
import json
import glob

REPOSITORY_URL  = "https://github.com/indicate-eu/data-dictionary"
CACHE_DIRECTORY = pathlib.Path(xdg_cache_home())
CLONE_DIRECTORY = CACHE_DIRECTORY / 'indicate' / 'data-dictionary'

data_dictionary_commit = None

def ensure_data_dictionary_clone():
    global data_dictionary_commit
    if data_dictionary_commit:
        return CLONE_DIRECTORY, data_dictionary_commit
    else:
        if not CLONE_DIRECTORY.exists():
            parent = CLONE_DIRECTORY.parent
            parent.mkdir(parents=True, exist_ok=True)
            subprocess.run(['git', 'clone', REPOSITORY_URL], cwd=parent)
        else:
            subprocess.run(['git', 'pull'], cwd=CLONE_DIRECTORY)
        process = subprocess.run(['git', 'rev-parse', 'HEAD'],
                                 cwd=CLONE_DIRECTORY,
                                 stdout=subprocess.PIPE)
        data_dictionary_commit = process.stdout.strip().decode()
        return CLONE_DIRECTORY, data_dictionary_commit

# Concept sets

def load_concept_sets():
    concept_sets = dict()
    directory, commit = ensure_data_dictionary_clone()
    for filename in glob.glob(f"{directory}/concept_sets/*.json"):
        with open(filename, 'rb') as file:
            concept_set = json.load(file)
        concept_set_id = concept_set.get('id')
        concept_sets[concept_set_id] = concept_set
    print(f"Read {len(concept_sets)} concept sets at commit {commit}")
    return concept_sets, REPOSITORY_URL, commit

def load_resolved_concept_sets(add_names=True):
    concept_sets = dict()
    directory, commit = ensure_data_dictionary_clone()
    for filename in glob.glob(f"{directory}/concept_sets_resolved/*.json"):
        with open(filename, 'rb') as file:
            resolved_concept_set = json.load(file)
        concept_set_id = resolved_concept_set.get('conceptSetId')
        if add_names:
            # The resolved concept sets don't contain names. Get the name
            # from the corresponding non-resolved concept set.
            with open(f"{directory}/concept_sets/{concept_set_id}.json") as file:
                concept_set = json.load(file)
                resolved_concept_set['name'] = concept_set.get('name')
                resolved_concept_set['deprecated'] = concept_set.get('metadata', {}).get('reviewStatus') == 'deprecated'
        concept_sets[concept_set_id] = resolved_concept_set
    print(f"Read {len(concept_sets)} resolved concept sets at commit {commit}")
    return concept_sets, REPOSITORY_URL, commit
