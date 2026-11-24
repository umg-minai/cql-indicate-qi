import typer
from pathlib import Path
import data_dictionary
import terminology_from_data_dictionary
import synchronize_terminology
import update_project as update_project_implementation

app = typer.Typer()


@app.callback()
def main(data_dictionary_repository: str = typer.Option(data_dictionary.DEFAULT_REPOSITORY_URL,
                                                        envvar="INDICATE_DATA_DICTIONARY_REPOSITORY",
                                                        help="Git URL of the data dictionary repository"),
         data_dictionary_branch: str = typer.Option(data_dictionary.DEFAULT_BRANCH,
                                                    envvar="INDICATE_DATA_DICTIONARY_BRANCH",
                                                    help="Branch of the data dictionary repository")):
    data_dictionary.configure(data_dictionary_repository, data_dictionary_branch)


@app.command()
def generate_cql(output_directory: Path):
    terminology_from_data_dictionary.generate_cql(output_directory)


@app.command()
def generate_markdown(output_directory: Path):
    terminology_from_data_dictionary.generate_markdown(output_directory)


@app.command()
def synchronize():
    synchronize_terminology.synchronize()


@app.command()
def update_project():
    update_project_implementation.update()


@app.command()
def project_concept_sets(project_id: int = 5):
    terminology_from_data_dictionary.print_project_concept_sets(project_id)


@app.command()
def generate_concept_set_list(output_file: Path,
                              project_id: int = 5,
                              definitions_directory: Path = typer.Option(None, help="Directory with the QI markdown files; used to fill in the qi of each concept set")):
    terminology_from_data_dictionary.generate_concept_set_list(output_file, project_id, definitions_directory)


if __name__ == "__main__":
    app()
