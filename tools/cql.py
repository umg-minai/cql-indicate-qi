import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path


JAR_FILENAME = 'cql-on-omop.jar'


DATABASE_PORT     = 9432
DATABASE_NAME     = 'omop_cdm'
DATABASE_USERNAME = 'postgres'
DATABASE_PASSWORD = 'postgres'
DATABASE_SCHEMA   = 'vocab'


def retrieve_used_concepts(timeout=60):
    print("Collecting used concepts from CQL libraries")
    try:
        process = subprocess.run(['java',
                                  '-jar', JAR_FILENAME,
                                  'terminology', '--resolve-concepts',
                                  '--omop-version', 'v5.4',
                                  '-p',         str(DATABASE_PORT),
                                  '-u',         DATABASE_USERNAME,
                                  '--password', DATABASE_PASSWORD,
                                  '-d',         DATABASE_NAME,
                                  '--schema',   DATABASE_SCHEMA,
                                  '-I', '../cql/',
                                  'Main'],
                                  capture_output=True,
                                  text=True,
                                  timeout=timeout)
        output = process.stdout
        if process.returncode != 0:
            error = process.stderr
            message = f"Error running cql-on-omop program: \n{error}{output}"
            raise RuntimeError(message)
        # Assuming the Java program outputs valid JSON
        try:
            data = json.loads(output)
            return data
        except json.JSONDecodeError as e:
            raise RuntimeError(f"Error decoding JSON: {e}") from None
    except subprocess.TimeoutExpired as e:
        message = f"cql-on-omop process timed out after {e.timeout} seconds"
        raise RuntimeError(message) from None


def qi_libraries(cql_directory):
    """The names of the QI libraries in a directory of CQL libraries, e.g. IndicateQi01Ventilation."""
    return sorted(path.stem for path in Path(cql_directory).glob("IndicateQi[0-9][0-9]*.cql")
                  if not path.stem.endswith("Test"))


def retrieve_qi_usage(cql_directory="../cql", jar=JAR_FILENAME, timeout=300):
    """Run cql-on-omop on the QI libraries (without a database).

    Because the QI libraries are named on the command line, cql-on-omop knows that they are the QI
    libraries: usingLibraries of every concept names the QI libraries that use it. Needs cql-on-omop
    1.1.16 or newer."""
    libraries = qi_libraries(cql_directory)
    if not libraries:
        raise RuntimeError(f"No QI libraries (IndicateQi01...) found in {cql_directory}")
    if not Path(jar).exists():
        raise FileNotFoundError(f"{jar} not found. cql-on-omop 1.1.16 or newer is needed to find out which QI uses a concept")
    print(f"Collecting the concepts that the {len(libraries)} QI libraries use")
    try:
        process = subprocess.run(["java", "-jar", str(jar), "terminology", "--omop-version", "v5.4",
                                  "-I", f"{str(cql_directory).rstrip('/')}/", *libraries],
                                 capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired as e:
        raise RuntimeError(f"cql-on-omop process timed out after {e.timeout} seconds") from None
    if process.returncode != 0:
        raise RuntimeError(f"Error running cql-on-omop program: \n{process.stderr}{process.stdout}")
    try:
        return json.loads(process.stdout)
    except json.JSONDecodeError as e:
        raise RuntimeError(f"Error decoding JSON: {e}") from None


def qi_of_concepts(entries):
    """From the output of cql-on-omop: for every concept id the set of QIs (QI01, ...) that use it."""
    result = defaultdict(set)
    for entry in entries:
        for library in entry.get("usingLibraries", []):
            match = re.fullmatch(r"IndicateQi(\d\d).*", library)
            if match:
                result[int(entry["id"])].add("QI" + match.group(1))
    if entries and not result:
        raise RuntimeError("cql-on-omop did not name any QI library in usingLibraries. "
                           "Version 1.1.16 or newer is needed.")
    return result
