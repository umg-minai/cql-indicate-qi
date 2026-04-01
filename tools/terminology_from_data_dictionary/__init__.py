import json
import pathlib

import requests
from xdg import xdg_cache_home

URL = "https://raw.githubusercontent.com/indicate-eu/data-dictionary-content/refs/heads/main/docs/data.json"

def retrieve_data():
    cache_dir = pathlib.Path(xdg_cache_home())
    cache_file = cache_dir / pathlib.Path('indicate-data.json')
    try:
        print(f"Trying to read from cache file {cache_file}")
        with open(cache_file) as file:
            return json.load(file)

    except FileNotFoundError:
        print(f"Downloading from {URL}")
        response = requests.get(URL)
        response.raise_for_status()  # Raise HTTPError for bad responses (4xx or 5xx)
        data = response.json()
        print(f"Writing to cache file {cache_file}")
        with open(cache_file, 'w') as file:
            json.dump(data, file)
        return data


def generate_library_for_category(concept_sets,
                                  category,
                                  subcategory,
                                  library_name,
                                  concept_definition_name):
    """Generates a CQL library for a specific drug category."""

    def is_matching_concept_set(concept_set):
        en = concept_set.get("metadata", {}).get("translations", {}).get("en", {})
        return en.get("category") == category and en.get("subcategory") == subcategory
    relevant_concept_sets = [concept_set for concept_set in concept_sets if is_matching_concept_set(concept_set)]

    write_drugs_to_file(relevant_concept_sets,
                        f"../../cql/{library_name}.cql",
                        library_name,
                        concept_definition_name)


def write_drugs_to_file(concept_sets,
                        filename,
                        library_name,
                        concept_definition_name):
    """Writes drug concepts to a CQL file."""
    print(f"Writing {len(concept_sets)} concept sets to {filename}")
    concept_sets_comments = "// Concept set(s)\n"
    for concept_set in concept_sets:
        concept_set_name = concept_set.get("name")
        concept_set_size = len(concept_set.get("expression", {}).get("items"))
        concept_set_modification_date = concept_set.get("modifiedDate")
        concept_sets_comments += f"// * {concept_set_name} ({concept_set_size} entries) [modified {concept_set_modification_date}]\n"
    with open(filename, 'w') as file:
        file.write(f"""// This file has been generated automatically from
// {URL}
{concept_sets_comments}
// Do not edit

library "{library_name}"

include IndicateQiElements called E

""")
        entries = {}
        for concept_set in concept_sets:
            items = concept_set.get("expression", {}).get("items")
            for item in items:
                concept = item.get("concept")
                concept_id = concept.get("conceptId")
                concept_name = concept.get("conceptName")
                entries[concept_name] = concept_id

        for concept_name, concept_id in sorted(entries.items(), key=lambda x: x[0].lower()):
            file.write(f"code \"{concept_name}\": '{concept_id}' from E.OMOPSV\n")

        file.write(f"\nconcept \"{concept_definition_name}\": {{")
        is_first = True
        for concept_name in sorted(entries.keys(), key=lambda x: x.lower()):
            if is_first:
                is_first = False
            else:
                file.write(",")
            file.write(f"\n  \"{concept_name}\"")
        file.write("\n}\n")


def main():
    """Main function to fetch data and generate libraries."""
    try:
        data = retrieve_data()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data: {e}")
        return 1

    concept_sets = data["conceptSets"]

    generate_library_for_category(concept_sets,
                                  "Drug",
                                  "Other drugs",
                                  'InsulinDrugs',
                                  'Insulin Drugs')

    generate_library_for_category(concept_sets,
                                  "Drug",
                                  'Anticoagulants',
                                  'AnticoagulationDrugs',
                                  'Anticoagulation Drugs')

    return None


if __name__ == "__main__":
    main()
