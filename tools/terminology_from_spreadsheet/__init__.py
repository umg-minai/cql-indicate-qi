import os.path

import pandas as pd

def write_drugs_to_file(drugs_dataframe,
                        filename,
                        library_name,
                        concept_definition_name,
                        source_description="minimal_data_dictionary.xlsx"):
    print(f"Generating library {library_name}")

    entries = dict()

    def find_unique_name(base_name: str):
        unique_name = base_name
        index = 1
        while unique_name in entries:
            print(f"Name clash {base_name}")
            index += 1
            unique_name = f"{base_name} ({index})"
        return unique_name

    for index, row in drugs_dataframe.iterrows():
        concept_name = row["concept_name"]
        omop_concept_id = row["omop_concept_id"]
        is_duplicate = False
        for existing_concept_name, existing_concept_id in entries.items():
            if omop_concept_id == existing_concept_id:
                print(f"Duplicate id {omop_concept_id} -> '{concept_name}' and '{existing_concept_name}'")
                is_duplicate = True
        if not is_duplicate:
            unique_name = find_unique_name(concept_name)
            entries[unique_name] = omop_concept_id

    with open(filename, 'w') as file:
        file.write(f"""// This file has been generated automatically from
// {source_description}
// Do not edit

library "{library_name}"

include IndicateQiElements called E

""")
        for concept_name, concept_id in entries.items():
            file.write(f"code \"{concept_name}\": '{concept_id}' from E.OMOPSV\n")
        file.write(f"\nconcept \"{concept_definition_name}\": {{")
        is_first = True
        for concept_name in sorted(entries.keys()):
            if is_first:
                is_first = False
            else:
                file.write(",")
            file.write(f"\n  \"{concept_name}\"")
        file.write("\n}\n")

def generate_library_for_category(drugs_dataframe, subcategory, library_name, concept_definition_name, source_name):
    drugs = drugs_dataframe[drugs_dataframe['subcategory'] == subcategory]
    write_drugs_to_file(drugs,
                        f"../../cql/{library_name}.cql",
                        library_name,
                        concept_definition_name,
                        source_description=f"rows with subcategory '{subcategory}' in 'drugs' table in {source_name}")


spreadsheet_filename = '/home/jan/Downloads/minimal_data_dictionary.xlsx'
source_name = os.path.basename(spreadsheet_filename)
data_frame = pd.read_excel(spreadsheet_filename, sheet_name='drugs')

generate_library_for_category(data_frame,
                              "Other drugs",
                              'InsulinDrugs',
                              'Insulin Drugs',
                              source_name)

generate_library_for_category(data_frame,
                              "Anticoagulants",
                              'AnticoagulationDrugs',
                              'Anticoagulation Drugs',
                              source_name)
