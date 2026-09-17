library "IndicateQi04GlucoseControlTest" version '1.0.0'

using OMOP version 'v5.4'

include OMOPFunctions

include "TestUtilities" called T

include "IndicateQi04GlucoseControl" called Q

define "Concept mmol/L": OMOP.Concept{
  conceptId:   8753,
  conceptCode: 'mmol/L'
}

define "Concept mg/L": OMOP.Concept{
  conceptId:   8751,
  conceptCode: 'mg/L'
}

// Tests for "Is Acceptable Glucose Level"

define "Test Is Acceptable Glucose Level 1":
  (1) _
    let actual:   Q."Is Acceptable Glucose Level"(0 'mmol/L'),
        expected: false
     return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Is Acceptable Glucose Level ' + '1')

// Tests for "Successful Glucose Control"

define "Test Successful Glucose Control 1":
  // Acceptable glucose level in current measurement.
  (1) _
    let previous: null,
        current:  Measurement{
                    measurementDatetime: @2016-07-09T21:00:00,
                    valueAsNumber:       4,
                    unitConcept:         "Concept mmol/L"
                  },
        next:     null,
        actual:   Q."Successful Glucose Control"(previous, current, next),
        expected: true
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Successful Glucose Control ' + '1')

define "Test Successful Glucose Control 2":
  // Corrected glucose level in next measurement.
  (1) _
    let previous: null,
        current:  Measurement{
                    measurementDatetime: @2016-07-09T21:00:00,
                    valueAsNumber:       1,
                    unitConcept:         "Concept mmol/L"
                  },
        next:     Measurement{
                    measurementDatetime: @2016-07-09T22:00:00,
                    valueAsNumber:       4,
                    unitConcept:         "Concept mmol/L"
                  },
        actual:   Q."Successful Glucose Control"(previous, current, next),
        expected: true
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Successful Glucose Control ' + '2')

define "Test Successful Glucose Control 3":
  // Previous measurement within expected time frame, acceptable glucose level
  // in current measurement.
  (1) _
    let previous: Measurement{
                    measurementDatetime: @2016-07-09T13:00:00,
                    valueAsNumber:       1,
                    unitConcept:         "Concept mmol/L"
                  },
        current:  Measurement{
                    measurementDatetime: @2016-07-09T21:00:00,
                    valueAsNumber:       4,
                    unitConcept:         "Concept mmol/L"
                  },
        next:     null,
        actual:   Q."Successful Glucose Control"(previous, current, next),
        expected: true
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Successful Glucose Control ' + '3')

define "Test Successful Glucose Control 4":
  // Time between previous and current measurement too long.
  (1) _
    let previous: Measurement{
                    measurementDatetime: @2016-07-09T05:00:00,
                    valueAsNumber:       4,
                    unitConcept:         "Concept mmol/L"
                  },
        current:  Measurement{
                    measurementDatetime: @2016-07-09T21:00:00,
                    valueAsNumber:       4,
                    unitConcept:         "Concept mmol/L"
                  },
        next:     Measurement{
                    measurementDatetime: @2016-07-09T22:00:00,
                    valueAsNumber:       4,
                    unitConcept:         "Concept mmol/L"
                  },
        actual:   Q."Successful Glucose Control"(previous, current, next),
        expected: false
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Successful Glucose Control ' + '4')

define "Test Successful Glucose Control 5":
  // Next measurement does not correct glucose level.
  (1) _
    let previous: null,
        current:  Measurement{
                    measurementDatetime: @2016-07-09T21:00:00,
                    valueAsNumber:       11,
                    unitConcept:         "Concept mmol/L"
                  },
        next:     Measurement{
                    measurementDatetime: @2016-07-09T22:00:00,
                    valueAsNumber:       11,
                    unitConcept:         "Concept mmol/L"
                  },
        actual:   Q."Successful Glucose Control"(previous, current, next),
        expected: false
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Successful Glucose Control ' + '5')

define "Test Successful Glucose Control 6":
  // Next measurement corrects glucose level but is too late.
  (1) _
    let previous: null,
        current:  Measurement{
                    measurementDatetime: @2016-07-09T21:00:00,
                    valueAsNumber:       1,
                    unitConcept:         "Concept mmol/L"
                  },
        next:     Measurement{
                    measurementDatetime: @2016-07-10T01:00:00,
                    valueAsNumber:       4,
                    unitConcept:         "Concept mmol/L"
                  },
        actual:   Q."Successful Glucose Control"(previous, current, next),
        expected: false
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Successful Glucose Control ' + '6')

define "Test Successful Glucose Control 7":
  // Glucose level measurement is in mg/L instead of mmol/L.
  (1) _
    let previous: null,
        current:  Measurement{
                    measurementDatetime: @2016-07-09T21:00:00,
                    valueAsNumber:       1000,
                    unitConcept:         "Concept mg/L"
                  },
        next:     null,
        actual:   Q."Successful Glucose Control"(previous, current, next),
        expected: true
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Successful Glucose Control ' + '7')

// Results

define Results: {
  "Test Is Acceptable Glucose Level 1",

  "Test Successful Glucose Control 1",
  "Test Successful Glucose Control 2",
  "Test Successful Glucose Control 3",
  "Test Successful Glucose Control 4",
  "Test Successful Glucose Control 5",
  "Test Successful Glucose Control 6",
  "Test Successful Glucose Control 7"
}
