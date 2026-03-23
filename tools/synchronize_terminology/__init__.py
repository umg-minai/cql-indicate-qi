import subprocess
import json
import pathlib

import requests
from xdg import xdg_cache_home

DATA_URL = "https://raw.githubusercontent.com/indicate-eu/data-dictionary-content/refs/heads/main/docs/data.json"
UI_URL = "https://indicate-eu.github.io/data-dictionary-content"
PROJECT_INFO_URL = "https://github.com/indicate-eu/data-dictionary-content/blob/main/projects/5.json"

def retrieve_cql_data():
    print("Collecting used concepts from CQL libraries")
    try:
        process = subprocess.run(['java',
                                  '-jar', '/home/jan/code/cql/cql-on-omop/target/cql-on-omop-1.0-SNAPSHOT.jar',
                                  'terminology', '--omop-version', 'v5.4',
                                  '-p', '5432', '-u', 'postgres', '--password', 'yourpassword', '-d', 'ohdsi',
                                  '-I', '/home/jan/code/indicate/quality-indicators/cql/',
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


def retrieve_dictionary_data():
    cache_dir = pathlib.Path(xdg_cache_home())
    cache_file = cache_dir / pathlib.Path('indicate-data.json')
    try:
        print(f"Trying to read from cache file {cache_file}")
        with open(cache_file) as file:
            return json.load(file)

    except FileNotFoundError:
        print(f"Downloading from {DATA_URL}")
        response = requests.get(DATA_URL)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        print(f"Writing to cache file {cache_file}")
        with open(cache_file, 'w') as file:
            json.dump(data, file)
        return data

def synchronize():
    cql_data = retrieve_cql_data()
    dictionary_data = retrieve_dictionary_data()

    all_concept_sets = dictionary_data.get("conceptSets", [])
    used_concept_sets = []
    unmapped_concepts = []
    for concept in cql_data:
        def contains_concept_id(concept_id, concept_set):
            def temp(item):
                return item.get("concept", {}).get("conceptId") == concept_id
            return any( temp(item) for item
                        in concept_set.get("expression", {}).get("items", []))
        found = False
        for concept_set in all_concept_sets:
           if contains_concept_id(int(concept.get("id")), concept_set):
               found = True
               if not any( old_concept_set for old_concept_set in used_concept_sets
                           if old_concept_set.get("id") == concept_set.get("id") ):
                   used_concept_sets.append(concept_set)
        if not found:
            unmapped_concepts.append(concept)

    print(f"\033[1mThe CQL libraries use {len(used_concept_sets)} of {len(all_concept_sets)} concept sets\033[0m")
    for concept_set in used_concept_sets:
        concept_set_id = concept_set.get("id")
        concept_set_name = concept_set.get('name')
        print(f"* \033]8;;{UI_URL}/#/concept-sets?id={concept_set_id}\033\\ {concept_set_name} ({concept_set_id})\033]8;;\033\\")

    print(f"\n\033[1mJSON-formatted for updating \033]8;;{PROJECT_INFO_URL}\033\\{PROJECT_INFO_URL}\033]8;;\033\\:\033[0m")
    print(f"  {json.dumps(sorted( concept_set.get('id') for concept_set in used_concept_sets))}")

    if unmapped_concepts:
        print(f"\n\033[33mThe following {len(unmapped_concepts)} concepts are not covered by any concept set:\033[0m")
        for concept in sorted(unmapped_concepts, key=lambda x: x.get("name") or ""):
            print(f"* {concept}")
    return used_concept_sets


if __name__ == '__main__':
    synchronize()
