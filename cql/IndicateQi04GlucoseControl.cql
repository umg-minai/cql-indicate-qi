// Name     04 - Glucose Control
// Version  1.0
//
// Description:
// Control of appropriate glucose levels
//
// Numerator:
//  (All ICU patients) - (all patients with <= 10 mmol/l glucose )
//  (includes all patients with glucose > 10 mmol/l and all patients without
//  any glucose measurement)
//
// Denominator:
//  All patients admitted to the intensive care unit during
//  the period reviewed.

library "IndicateQi04GlucoseControl" version '1.0.0'

using OMOP version 'v5.4'

include OMOPHelpers
include IndicateQiElements called elm

// TODO: @sgibb, use the correct Glc OMOP Concept ID, use the Horowitz for testing
// b/c there are not any Glc measurements in the test db
code "Glucose": '3029943' from elm.OMOPSV   // Horowitz
parameter "High Glucose Level" default 200.0 'mm[Hg]'
parameter "Time between two consecutive High Glucose Levels" default 4 hours

// code "Glucose": '3020491' from OMOPSV    // Glucose [Moles/volume] in Blood
//parameter "High Glucose Level" default 10.0 'mmol/l'
// or
// 3000483

context Patient

define "Visits with High Glucose Measurements":
  from
    elm."Intensive Care Visits in Review Period" icv,
    "High Glucose Measurements" hgm
    where hgm.measurementDatetime during
        Interval[icv.visitStartDatetime, icv.visitEndDatetime]
    return icv

define "Consecutive High Glucose Measurements":
  from
    "High Glucose Measurements" hgm1,
    "High Glucose Measurements" hgm2
  where hgm2.measurementDatetime after hgm1.measurementDatetime
    and hgm2.measurementDatetime before hgm1.measurementDatetime +
      "Time between two consecutive High Glucose Levels"
  return hgm1

define "High Glucose Measurements":
  elm."Measurements in Review Period" m
    where m.measurementConcept ~ "Glucose"
      and OMOPHelpers.ToQuantity(m) > "High Glucose Level"
    sort by measurementDatetime

// TODO: @sgibb, due to "context Patient" and ",focus [Person]" this counts
// patient-wise (just 0 or 1) instead of ICU wide
define Denominator:
  Count(elm."Intensive Care Visits in Review Period") -
  Count("Visits with High Glucose Measurements")

define Numerator:
  Count(elm."Intensive Care Visits in Review Period")

define QI:
  Numerator / Denominator

// vim: filetype=cql
