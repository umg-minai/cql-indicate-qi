// This library orchestrates unit tests for the CQL libraries in this project.
//
// To run tests, use an invocation like the following:
//
//   java -jar PATH-TO-CQL-ON-OMOP/cql-on-omop-1.1.9-SNAPSHOT.jar \
//     batch                                                      \
//     -I PATH-TO-THIS-REPOSITORY/cql/ Test                       \
//     --result-name="Test.*"

library Test version '1.0.0'

include "TimePeriodsTest"

include "IndicateQi04GlucoseControlTest"
include "IndicateQi06InfectionRateTest"

define Results: Flatten({
  TimePeriodsTest.Results,
  "IndicateQi04GlucoseControlTest".Results,
  "IndicateQi06InfectionRateTest".Results
})
