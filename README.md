## Introduction

This repository contains [CQL](https://cql.hl7.org) representations of the quality indicators defined in the [INDICATE](https://indicate-europe.eu/) project.

* The CQL libraries are written based on the [OMOP Clinical Data Model](https://www.ohdsi.org/data-standardization/) version 5.4 and therefore must be applied to clinical data which conforms to that data model.

* The [cql-on-omop project](https://github.com/umg-minai/cql-on-omop) provides a CQL engine that works with SQL databases containing OMOP-formatted clinical data.

## Requirements

* A OMOP CDM v5.4-formatted database of clinical data.
  By default, the database driver assumes a PostgreSQL database.

* The `cql-on-omop` engine mentioned above can be downloaded in the form of a Java JAR file (or as a Docker container image) from the [repository of the project](https://github.com/umg-minai/cql-on-omop).

* To execute `cql-on-omop`, a Java runtime environment for language version 17 and above is required.
  Since there are no graphical components, the "headless" version of the Java runtime environment is sufficient.
  For example, on Debian Linux, the package `openjdk-21-jre-headless` can be used to run `cql-on-omp`.

## Usage

An invocation similar to the following evaluates the quality indicators in this repository against a OMOP-formatted database:

```bash
java -jar PATH-TO-CQL-ON-OMOP/cql-on-omop-1.1.9-SNAPSHOT.jar                      \
  batch --omop-version 'v5.4'                                                     \
  -c 'Take([Person], 300)'                                                        \
  --host HOST --port PORT --database DATABASE --user USERNAME --password PASSWORD \
  --result-name 'Results' --print-results-matching='Results'                      \
  -I PATH-TO-THIS-REPOSITORY/cql/ Main

```

* In the first line, `java -jar PATH-TO-CQL-ON-OMOP/cql-on-omop-1.1.9-SNAPSHOT.jar`, the `java` runtime must be provided with the downloaded `cql-on-omop` artifact.

* The second line instructs `cql-on-omop` to operate in batch mode and use OMOP CDM version 5.4.
  There should be no need to change this part of the invocation.

* The third line, `-c 'Take([Person], 300)'` selects patients to process from the database.
  The given example limits the population to 300 patients.
  To process all patients, use `-c '[Person]'` instead.

* Line 4 specifies the connection to the OMOP database.
  `HOST`, `PORT`, `DATABASE`, `USERNAME` and `PASSWORD` must be substituted with suitable values.

* Line 5, `--result-name 'Results' --print-results-matching='Results'`, specifies which CQL expressions contain the results of the QI computation and makes `cql-on-omop` print those results for each patient.

* Line 6, `-I PATH-TO-THIS-REPOSITORY/cql/ Main`, specifies where `cql-on-omop` should look for CQL libraries and that the `Main` library is the starting point for evaluation.
  `PATH-TO-THIS-REPOSITORY` must be replaced with the actual path into which this repository has been cloned.

The output of the above invocation should be similar to the following:

```
Unfiltered Context
Person{id=1}
Results => List<OMOP.v54.Observation>
  OMOP.v54.Observation {
    ...
  }
  OMOP.v54.Observation {
    ...
  }
  ...
Person{id=2}
Results => List<OMOP.v54.Observation>
  OMOP.v54.Observation {
    ...
  }
  ...
...
10.935 s, 17 successes, 84 failures
    1 time(s): ERROR '401: Blood Glucose Level does not have a numeric value'
   61 time(s): ERROR '401: Blood Glucose Level does not have a unit'
   22 time(s): ERROR '401: Tidal volume measurement does not have a unit'
```

The precise number of processed patients, reported results, number of errors, reported runtime, etc. depend on the input data and thus will be different from the example.

## References

- [CQL Author Guide](https://cql.hl7.org/02-authorsguide.html)
- [Formal definitions of INDICATE quality indicators](https://github.com/umg-minai/indicate-qi-definitions)
