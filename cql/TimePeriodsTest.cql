library "TimePeriodsTest" version '1.0.0'

include "TestUtilities" called T

include "TimePeriods" called P

// Tests for "Test Shifts during Period"

define "Test Shifts during Period 1":
  // Empty period.
  (1) _
    let actual: P."Shifts during Period"(
                  Interval[@2026-06-11T06:00:00, @2026-06-11T06:00:00]
                )
      // Work around the fact that {} = {} => null
      return if actual ~ {} then
               true
             else
               T.SimpleTestFailure('Test Shifts during Period ' + ' 1')

define "Test Shifts during Period 2":
  // Non-empty period that is properly contained in one shift..
  (1) _
    let actual: P."Shifts during Period"(
                  Interval[@2026-06-11T07:00:00, @2026-06-11T08:00:00]
                )
      // Work around the fact that {} = {} => null
      return if actual ~ {} then
               true
             else
               T.SimpleTestFailure('Test Shifts during Period ' + ' 2')

define "Test Shifts during Period 3":
  // A short period that overlaps multiple shifts but does not includes any.
  (1) _
    let actual: P."Shifts during Period"(
                  Interval[@2026-06-11T10:00:00, @2026-06-11T15:00:00]
                )
      // Work around the fact that {} = {} => null
      return if actual ~ {} then
               true
             else
               T.SimpleTestFailure('Test Shifts during Period ' + ' 3')

define "Test Shifts during Period 4":
  // Period aligned with shift starts and ends.
  (1) _
    let actual:   P."Shifts during Period"(
                    Interval[@2026-06-11T06:00:00, @2026-06-12T06:00:00]
                  ),
        expected: {
                    Interval[@2026-06-11T06:00:00, @2026-06-11T14:00:00),
                    Interval[@2026-06-11T14:00:00, @2026-06-11T22:00:00),
                    Interval[@2026-06-11T22:00:00, @2026-06-12T06:00:00)
                  }
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Shifts during Period ' + ' 4')

define "Test Shifts during Period 5":
  // Period start aligned with shift start, period end not aligned.
  (1) _
    let actual:   P."Shifts during Period"(
                    Interval[@2026-06-11T06:00:00, @2026-06-12T15:00:00]
                  ),
        expected: {
                    Interval[@2026-06-11T06:00:00, @2026-06-11T14:00:00),
                    Interval[@2026-06-11T14:00:00, @2026-06-11T22:00:00),
                    Interval[@2026-06-11T22:00:00, @2026-06-12T06:00:00),
                    Interval[@2026-06-12T06:00:00, @2026-06-12T14:00:00)
                  }
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Shifts during Period ' + ' 5')

// Tests for "24-hour Periods overlapping Period"

define "Test 24-hour Periods overlapping Period 1":
  (1) _
    let actual:       P."24-hour Periods overlapping Period"(
                        Interval[@2026-06-11T15:00:00, @2026-06-11T16:00:00]
                      ),
        expected:     { Interval[@2026-06-11T06:00:00, @2026-06-12T06:00:00) }
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test 24-hour Periods overlapping Period ' + '1')

define "Test 24-hour Periods overlapping Period 2":
  (1) _
    let actual:       P."24-hour Periods overlapping Period"(
                        Interval[@2026-06-11T15:00:00, @2026-06-13T03:00:00]
                      ),
        expected:     {
                        Interval[@2026-06-11T06:00:00, @2026-06-12T06:00:00),
                        Interval[@2026-06-12T06:00:00, @2026-06-13T06:00:00)
                      }
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test 24-hour Periods overlapping Period ' + '2')

// Tests for "Visits and 24-hour Periods during Period"

define "Test Visits and 24-hour Periods during Period 1":
  // Test empty list of visits.
  (1) _
    let visits:       {},
        reviewPeriod: Interval[@2000-01-01T00:00:00, @3000-12-31T00:00:00),
        actual:       P."Visits and 24-hour Periods during Period"(
                        visits, reviewPeriod
                      )
      // Work around the fact that {} = {} => null
      return if actual ~ {} then
               true
             else
               T.SimpleTestFailure('Test Visits and 24-hour Periods during Period ' + '1')

define "Test Visits and 24-hour Periods during Period 2":
  // Smoke test: Single visit that spans multiple days with start and end times
  // that are not aligned with the start of the clinical day.
  (1) _
    let visits:       { Interval[@2026-06-11T15:00:00, @2026-06-14T20:00:00] },
        reviewPeriod: Interval[@2000-01-01T00:00:00, @3000-12-31T00:00:00),
        actual:       P."Visits and 24-hour Periods during Period"(
                        visits, reviewPeriod
                      ),
        expected:     {
                        {
                          visit:                 First(visits),
                          overlappingPeriods:    {
                            Interval[@2026-06-11T06:00:00, @2026-06-12T06:00:00),
                            Interval[@2026-06-12T06:00:00, @2026-06-13T06:00:00),
                            Interval[@2026-06-13T06:00:00, @2026-06-14T06:00:00),
                            Interval[@2026-06-14T06:00:00, @2026-06-15T06:00:00)
                          },
                          fullyContainedPeriods: {
                            Interval[@2026-06-12T06:00:00, @2026-06-13T06:00:00),
                            Interval[@2026-06-13T06:00:00, @2026-06-14T06:00:00)
                          }
                        }
                      }
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Visits and 24-hour Periods during Period ' + '2')

define "Test Visits and 24-hour Periods during Period 3":
  // Edge case: start and end of visit are aligned with start of clinical day.
  (1) _
    let visits:       { Interval[@2026-06-11T06:00:00, @2026-06-12T06:00:00] },
        reviewPeriod: Interval[@2000-01-01T00:00:00, @3000-12-31T00:00:00),
        actual:       P."Visits and 24-hour Periods during Period"(
                        visits, reviewPeriod
                      ),
        expected:     {
                        {
                          visit:                 First(visits),
                          overlappingPeriods:    {
                            Interval[@2026-06-11T06:00:00, @2026-06-12T06:00:00)
                          },
                          fullyContainedPeriods: {
                            Interval[@2026-06-11T06:00:00, @2026-06-12T06:00:00)
                          }
                        }
                      }
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Visits and 24-hour Periods during Period ' + '3')

define "Test Visits and 24-hour Periods during Period 4":
  // Visit is properly contained in a single clinical day.
  (1) _
    let visits:       { Interval[@2026-06-11T08:00:00, @2026-06-11T12:00:00] },
        reviewPeriod: Interval[@2000-01-01T00:00:00, @3000-12-31T00:00:00),
        actual:       P."Visits and 24-hour Periods during Period"(
                        visits, reviewPeriod
                      )
      return if actual ~ {} then
               true
             else
               T.SimpleTestFailure('Test Visits and 24-hour Periods during Period ' + '4')

define "Test Visits and 24-hour Periods during Period 5":
  // Visit overlaps multiple 24-hour periods but does not contain any
  // complete 24-hour periods.
  (1) _
    let visits:       { Interval[@2026-06-11T03:00:00, @2026-06-11T12:00:00] },
        reviewPeriod: Interval[@2000-01-01T00:00:00, @3000-12-31T00:00:00),
        actual:       P."Visits and 24-hour Periods during Period"(
                        visits, reviewPeriod
                      )
      return if actual ~ {} then
               true
             else
               T.SimpleTestFailure('Test Visits and 24-hour Periods during Period ' + '5')

define "Test Visits and 24-hour Periods during Period 6":
  // Multiple visits
  (1) _
    let visits:       {
                        Interval[@2026-06-11T03:00:00, @2026-06-12T12:00:00],
                        Interval[@2026-07-01T01:00:00, @2026-07-03T02:00:00]
                      },
        reviewPeriod: Interval[@2000-01-01T00:00:00, @3000-12-31T00:00:00),
        actual:       P."Visits and 24-hour Periods during Period"(
                        visits, reviewPeriod
                      ),
        expected:     {
                        {
                          visit:                 visits[0],
                          overlappingPeriods:    {
                            Interval[@2026-06-10T06:00:00, @2026-06-11T06:00:00),
                            Interval[@2026-06-11T06:00:00, @2026-06-12T06:00:00),
                            Interval[@2026-06-12T06:00:00, @2026-06-13T06:00:00)
                          },
                          fullyContainedPeriods: {
                            Interval[@2026-06-11T06:00:00, @2026-06-12T06:00:00)
                          }
                        },
                        {
                          visit:                 visits[1],
                          overlappingPeriods:    {
                            Interval[@2026-06-30T06:00:00, @2026-07-01T06:00:00),
                            Interval[@2026-07-01T06:00:00, @2026-07-02T06:00:00),
                            Interval[@2026-07-02T06:00:00, @2026-07-03T06:00:00)
                          },
                          fullyContainedPeriods: {
                            Interval[@2026-07-01T06:00:00, @2026-07-02T06:00:00)
                          }
                        }
                      }
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Visits and 24-hour Periods during Period ' + '6')

// Results

define Results: {
  "Test Shifts during Period 1",
  "Test Shifts during Period 2",
  "Test Shifts during Period 3",
  "Test Shifts during Period 4",
  "Test Shifts during Period 5",

  "Test 24-hour Periods overlapping Period 1",
  "Test 24-hour Periods overlapping Period 2",

  "Test Visits and 24-hour Periods during Period 1",
  "Test Visits and 24-hour Periods during Period 2",
  "Test Visits and 24-hour Periods during Period 3",
  "Test Visits and 24-hour Periods during Period 4",
  "Test Visits and 24-hour Periods during Period 5",
  "Test Visits and 24-hour Periods during Period 6"
}
