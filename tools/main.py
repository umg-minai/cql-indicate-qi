import typer
from pathlib import Path
import terminology_from_data_dictionary
import synchronize_terminology
import update_project as update_project_implementation

app = typer.Typer()


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
def generate_concept_set_list(output_file: Path, project_id: int = 5):
    terminology_from_data_dictionary.generate_concept_set_list(output_file, project_id)


if __name__ == "__main__":
    app()
