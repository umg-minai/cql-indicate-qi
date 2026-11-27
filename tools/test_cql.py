"""Tests for the CQL library names.

Run from the tools directory: python3 test_cql.py (or with pytest).
"""

from terminology_from_data_dictionary.cql import check_cql_library_names, cql_library_name
from terminology_from_data_dictionary.model import ConceptSetMapping


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


if __name__ == "__main__":
    tests = [value for name, value in sorted(globals().items()) if name.startswith("test_")]
    for test in tests:
        test()
    print(f"{len(tests)} tests passed")
