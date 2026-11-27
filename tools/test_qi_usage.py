"""Tests for the QI information from cql-on-omop.

Run from the tools directory: python3 test_qi_usage.py (or with pytest).
"""

import tempfile
from pathlib import Path

import cql as cql_on_omop


def expect_error(function, *arguments):
    try:
        function(*arguments)
    except RuntimeError:
        return
    raise AssertionError(f"{function.__name__}{arguments} should raise an error")


def test_the_qi_libraries_are_found_by_their_names():
    with tempfile.TemporaryDirectory() as directory:
        for name in ("IndicateQi01Ventilation", "IndicateQi03Feeding", "IndicateQi03FeedingTest",
                     "IndicateQiElements", "IndicateQiUtilities", "BodyHeight"):
            (Path(directory) / f"{name}.cql").write_text("")
        assert cql_on_omop.qi_libraries(directory) == ["IndicateQi01Ventilation", "IndicateQi03Feeding"]


def test_the_qi_of_a_concept_come_from_the_libraries_that_use_it():
    entries = [{"id": "37158404", "usingLibraries": ["IndicateQi06InfectionRate", "IndicateQi01Ventilation"]},
               {"id": "3025315", "usingLibraries": ["IndicateQi03Feeding"]},
               {"id": "1", "usingLibraries": ["IndicateQi04GlucoseControl", "SomeHelperLibrary"]}]
    assert cql_on_omop.qi_of_concepts(entries) == {37158404: {"QI01", "QI06"}, 3025315: {"QI03"}, 1: {"QI04"}}


def test_an_old_cql_on_omop_that_only_names_main_is_an_error():
    expect_error(cql_on_omop.qi_of_concepts, [{"id": "1", "usingLibraries": ["Main"]}])


def test_the_jar_must_exist():
    with tempfile.TemporaryDirectory() as directory:
        (Path(directory) / "IndicateQi01Ventilation.cql").write_text("")
        try:
            cql_on_omop.retrieve_qi_usage(directory, Path(directory) / "missing.jar")
        except FileNotFoundError:
            return
        raise AssertionError("a missing jar should raise an error")


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} tests passed")
