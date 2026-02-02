// Name     05 - Prevention of venous thromboembolism
// Version  1.0
//
// Description:
//  Venous thromboembolism (VTE) is a frequent complication that
//  contributes significantly to morbidity and mortality among critically
//  ill patients.  Pharmacologic thromboprophylaxis should reduce VTE.
//
// Numerator:
//  Number of 24 hour periods starting at admission + 24 hours in which
//  at least one of the listed drugs has been used.
//
// Denominator:
//  Number of 24 hour periods.

library "IndicateQi05ThrombembolicPrevention" version '1.0.0'

using OMOP version 'v5.4'

include OMOPHelpers
include TimePeriods called T
include IndicateQiElements called elm
include AnticoagulationDrugs

context Patient

define "Anticoagulation Drug Exposures":
  [DrugExposure: "AnticoagulationDrugs"."Anticoagulation Drugs"] e
    return all e
    sort by drugExposureStartDatetime asc

define function "Anticoagulation Drug Exposures during Period"(period Interval<DateTime>):
  ("Anticoagulation Drug Exposures") e
    where convert e to Interval<DateTime> overlaps period
    return e

define debugExposures:
  "Anticoagulation Drug Exposures" e
    return all {i: convert e to Interval<DateTime>, d: e.drugConcept.conceptName}

// 24-hour periods

define debugVisit: elm."Intensive Care Visits in Review Period" v return convert v to Interval<DateTime>

define function "24-hour Period with Conforming Medication"(period Interval<DateTime>):
  Exists("Anticoagulation Drug Exposures during Period"(period))

define "24-hour Periods with conforming Medication during Visits":
  T."24-hour Periods in Visits" periods
    return all Flatten({
      { First(periods) }, // First period always counts as conforming
      (Tail(periods)) p
        where "24-hour Period with Conforming Medication"(p)
        return all p
    })

define "24-hour Periods":
  Flatten(T."24-hour Periods in Visits")

define "24-hour Periods with Conforming Medication":
  Flatten("24-hour Periods with conforming Medication during Visits")

// Quality Indicator

define "Is in Initial Population":
      Exists(elm."Intensive Care Visits in Review Period")
  and (elm."Age at Start of Review Period" >= 18)

define Denominator:
  Count("24-hour Periods")

define Numerator:
  Count("24-hour Periods with Conforming Medication")

define QI:
  if "Is in Initial Population" then
    Numerator / Denominator
  else
    null

define Result:
  {
    patient:     Patient,
    period:      elm."Review Period",
    numerator:   Numerator,
    denominator: Denominator,
    qi:          QI
  }
