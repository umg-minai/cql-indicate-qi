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


if __name__ == "__main__":
    app()
