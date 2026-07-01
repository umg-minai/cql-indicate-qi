import xdg
import pathlib
import subprocess
import json
import glob


REPOSITORY_URL  = "https://github.com/indicate-eu/data-dictionary"
CACHE_DIRECTORY = pathlib.Path(xdg.xdg_cache_home())
CLONE_DIRECTORY = CACHE_DIRECTORY / 'indicate' / 'data-dictionary'


VERSIONS_FILE = "concept_sets_versions.json"


PROJECTS_DIRECTORY = "projects"


data_dictionary_commit = None


def ensure_data_dictionary_clone(timeout=60):
    global data_dictionary_commit
    if data_dictionary_commit:
        return CLONE_DIRECTORY, data_dictionary_commit
    else:
        def run_git(cwd, *args):
            try:
                process = subprocess.run(['git'] + list(args),
                                         cwd=cwd,
                                         env={'GIT_TERMINAL_PROMPT': '0'},
                                         capture_output=True,
                                         check=True,
                                         timeout=timeout)
                return process.stdout
            except subprocess.CalledProcessError as e:
                output = str(e.stdout, encoding='UTF8')
                error = str(e.stderr, encoding='UTF8')
                message = f"Git operation {e.cmd} failed with code {e.returncode} and output\n{output}\n{error}"
                raise RuntimeError(message) from None
            except subprocess.TimeoutExpired as e:
                output = str(e.stdout, encoding='UTF8')
                error = str(e.stderr, encoding='UTF8')
                message = f"Git operation {e.cmd} timed out after {e.timeout} seconds with output\n{output}\n{error}"
                raise RuntimeError(message) from None

        if not CLONE_DIRECTORY.exists():
            parent = CLONE_DIRECTORY.parent
            parent.mkdir(parents=True, exist_ok=True)
            run_git(parent, 'clone', REPOSITORY_URL)
        else:
            run_git(CLONE_DIRECTORY, 'pull')
        output = run_git(CLONE_DIRECTORY, 'rev-parse', 'HEAD')
        data_dictionary_commit = output.strip().decode()
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
            # The resolved concept sets don't contain names.  Get the name
            # from the corresponding non-resolved concept set.
            with open(f"{directory}/concept_sets/{concept_set_id}.json") as file:
                concept_set = json.load(file)
                metadata = concept_set.get('metadata', {})
                en = metadata.get('translations', {}).get('en', {})
                resolved_concept_set['name']        = concept_set.get('name')
                resolved_concept_set['deprecated']  = metadata.get('reviewStatus') == 'deprecated'
                resolved_concept_set['category']    = en.get('category', None)
                resolved_concept_set['subcategory'] = en.get('subcategory', None)
        concept_sets[concept_set_id] = resolved_concept_set
    print(f"Read {len(concept_sets)} resolved concept sets at commit {commit}")
    return concept_sets, REPOSITORY_URL, commit


def load_concept_set_versions():
    directory, _ = ensure_data_dictionary_clone()
    with open(directory / VERSIONS_FILE) as file:
        return json.load(file)

# Projects

def project_file_name(repository_directory, project_id):
    return repository_directory / PROJECTS_DIRECTORY / f"{str(project_id)}.json"


def load_project(project_id):
    directory, _ = ensure_data_dictionary_clone()
    with open(project_file_name(directory, project_id)) as file:
        return json.load(file)


def store_project(project_id, data):
    directory, _ = ensure_data_dictionary_clone()
    with open(project_file_name(directory, project_id), 'w') as file:
        json.dump(data, file, indent=2, ensure_ascii=False)
