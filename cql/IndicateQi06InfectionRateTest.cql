library "IndicateQi06InfectionRateTest" version '1.0.0'

include "TestUtilities" called T

include "IndicateQi06InfectionRate" called Q

define "Test incidence 1":
  (1) _
    let actual:   Q.incidence(
                    Interval[@2026-06-11T06:00:00, @2026-06-12T06:00:00),
                    1,
                    1
                  ),
        expected: 1000
      return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test incidence ' + '1')

// Results

define Results: {
  "Test incidence 1"
}
