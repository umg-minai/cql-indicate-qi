"""Tests for the CQL library names.

Run from the tools directory: python3 test_cql.py (or with pytest).
"""

import re
import tempfile
from pathlib import Path

from terminology_from_data_dictionary import cql
from terminology_from_data_dictionary.cql import check_cql_library_names, cql_library_name
from terminology_from_data_dictionary.model import ConceptOutput, ConceptSetMapping, Output


def expect_error(function, *arguments):
    try:
        function(*arguments)
    except RuntimeError:
        return
    raise AssertionError(f"{function.__name__}{arguments} should raise an error")


def test_names_are_made_of_the_words():
    assert cql_library_name("Glucose in blood") == "GlucoseInBlood"
    assert cql_library_name("Tidal volume (Vt)") == "TidalVolumeVt"
    assert cql_library_name("Insulin, Regular, Human") == "InsulinRegularHuman"


def test_a_name_never_starts_with_a_digit():
    assert (cql_library_name("3-minute Diagnostic Interview for CAM-defined Delirium (3D-CAM)")
            == "ThreeMinuteDiagnosticInterviewForCAMDefinedDelirium3DCAM")
    assert cql_library_name("4 A\'s Test for Delirium Screening") == "FourAsTestForDeliriumScreening"
    assert cql_library_name("12-lead ECG") == "TwelveLeadECG"
    expect_error(cql_library_name, "1000 things")


def test_symbols_and_accents():
    assert cql_library_name("Driving Pressure (\u0394P)") == "DrivingPressureDeltaP"
    assert cql_library_name("R\u00e9animation") == "Reanimation"
    expect_error(cql_library_name, "Test \u0436")


def test_an_empty_name_is_an_error():
    expect_error(cql_library_name, "(-)")


def test_two_concept_sets_must_not_give_the_same_name():
    assert check_cql_library_names(["Glucose in blood", "Body height"]) == {
        "GlucoseInBlood": "Glucose in blood", "BodyHeight": "Body height"}
    expect_error(check_cql_library_names, ["Insulin, Regular", "Insulin Regular"])


def test_an_entry_has_a_cql_library_unless_it_says_otherwise():
    assert ConceptSetMapping(name="Body height").cql is True
    assert ConceptSetMapping(name="Heparin", cql=False).cql is False


def _library_text(concepts_define):
    cql.generation_stamp = lambda: ["stamp"]
    output = Output([], [ConceptOutput(None, 1, "insulin a", False), ConceptOutput(None, 2, "insulin b", False)],
                    "url", "commit")
    with tempfile.TemporaryDirectory() as directory:
        cql.write_cql_library(output, Path(directory), "InsulinIngredients", "Insulin Ingredients", concepts_define)
        return (Path(directory) / "InsulinIngredients.cql").read_text()


def test_a_library_can_have_a_definition_that_lists_its_concepts_as_omop_concepts():
    text = _library_text("Insulin Ingredient Concepts")
    assert "include OMOPFunctions\n" in text
    assert 'define "Insulin Ingredient Concepts":' in text
    assert '("Insulin Ingredients".codes) c return all OMOPFunctions.ToOMOPConcept(c)' in text


def test_a_library_has_no_such_definition_unless_asked_for():
    text = _library_text(None)
    assert "OMOPFunctions" not in text and "\ndefine " not in text


def _code_names(concepts):
    cql.generation_stamp = lambda: ["stamp"]
    with tempfile.TemporaryDirectory() as directory:
        cql.write_cql_library(Output([], concepts, "url", "commit"), Path(directory), "Test", "Test")
        text = (Path(directory) / "Test.cql").read_text()
    codes = re.findall(r'^code "([^"]+)":', text, re.M)
    block = re.search(r'^concept "Test": \{\n(.*?)\n\}', text, re.S | re.M).group(1)
    assert re.findall(r'"([^"]+)"', block) == codes  # the concept lists the same names
    return codes


def test_codes_with_the_same_name_are_told_apart_by_their_vocabulary():
    codes = _code_names([ConceptOutput(None, 4099154, "Body weight", False, vocabulary="SNOMED"),
                         ConceptOutput(None, 3025315, "Body weight", False, vocabulary="LOINC"),
                         ConceptOutput(None, 4178502, "Body weight measure", False, vocabulary="SNOMED")])
    assert codes == ["Body weight (LOINC)", "Body weight (SNOMED)", "Body weight measure"]


def test_the_concept_id_is_added_if_the_vocabulary_does_not_tell_them_apart():
    codes = _code_names([ConceptOutput(None, 2, "Pressure", False, vocabulary="LOINC"),
                         ConceptOutput(None, 1, "Pressure", False, vocabulary="LOINC"),
                         ConceptOutput(None, 3, "Flow", False), ConceptOutput(None, 4, "Flow", False)])
    assert codes == ["Flow 3", "Flow 4", "Pressure (LOINC) 1", "Pressure (LOINC) 2"]


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} tests passed")
