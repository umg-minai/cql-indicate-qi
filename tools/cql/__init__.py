import json
import subprocess


JAR_FILENAME = '../cql-on-omop.jar'


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
                                  '-I', '../../cql/',
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
