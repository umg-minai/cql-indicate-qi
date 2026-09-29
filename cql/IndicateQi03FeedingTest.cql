library "IndicateQi03FeedingTest" version '1.0.0'

using OMOP version 'v5.4'

include "TestUtilities" called T

include "IndicateQi03Feeding" called Q

// Tests for "Maybe Rewrite Calorie Unit 1"

define "Test Maybe Rewrite Calorie Unit 1":
  (1) _
    let actual:   Q."Maybe Rewrite Calorie Unit"(null, @2026-06-10T06:00:00),
        expected: null
     return if actual is null then
               true
             else
               T.SimpleTestFailure('Test Maybe Rewrite Calorie Unit ' + '1')

define "Test Maybe Rewrite Calorie Unit 2":
  (1) _
    let actual:   Q."Maybe Rewrite Calorie Unit"(2000 'kcal/d',
                                                 @2026-06-10T06:00:00),
        expected: 2000 'kcal/d'
     return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Maybe Rewrite Calorie Unit ' + '2')

define "Test Maybe Rewrite Calorie Unit 3":
  (1) _
    let actual:   Q."Maybe Rewrite Calorie Unit"(2000 'kcal',
                                                 @2026-06-10T06:00:00),
        expected: 2000 'kcal/d'
     return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Maybe Rewrite Calorie Unit ' + '3')

define "Test Maybe Rewrite Calorie Unit 4":
  (1) _
    let actual:   Q."Maybe Rewrite Calorie Unit"(25 'kcal/kg',
                                                 @2026-06-10T06:00:00),
        expected: 2000 'kcal/d'
     return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Maybe Rewrite Calorie Unit ' + '4')

define "Test Maybe Rewrite Calorie Unit 5":
  (1) _
    let actual:   Q."Maybe Rewrite Calorie Unit"(30 'kcal/kg/(24.h)',
                                                 @2026-06-10T06:00:00),
        expected: 2000 'kcal/d'
     return if actual = expected then
               true
             else
               T.SimpleTestFailure('Test Maybe Rewrite Calorie Unit ' + '5')

// Results

define Results: {
  "Test Maybe Rewrite Calorie Unit 1",
  "Test Maybe Rewrite Calorie Unit 2",
  "Test Maybe Rewrite Calorie Unit 3",
  "Test Maybe Rewrite Calorie Unit 4",
  "Test Maybe Rewrite Calorie Unit 5"
}
