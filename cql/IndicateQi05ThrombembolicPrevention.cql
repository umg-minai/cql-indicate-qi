// Name     05 - Prevention of venous thromboembolism
// Version  1.0
//
// Description:
//   Venous thromboembolism (VTE) is a frequent complication that
//   contributes significantly to morbidity and mortality among critically
//   ill patients.  Pharmacologic thromboprophylaxis should reduce VTE.
//
// Numerator:
//   Number of 24 hour periods starting with the second 24 hour period
//   in which at least one of the listed drugs has been used.
//
// Denominator:
//   Number of 24 hour periods.

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
    where (convert e to Interval<DateTime>) overlaps period
    return all e

// 24-hour periods

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

define "24-hour Periods Results":
  (T."24-hour Periods in Visits") periods
    return all (periods) p
                 let numerator:   Count(("24-hour Periods with Conforming Medication") s
                                          where (p as Interval<DateTime>) includes (s as Interval<DateTime>) return all s),
                     denominator: Count(("24-hour Periods") s
                                          where (p as Interval<DateTime>) includes (s as Interval<DateTime>) return all s)
                   return all {
                     period:      p as Interval<DateTime>,
                     numerator:   numerator,
                     denominator: denominator,
                     qi:          if "Is in Initial Population" then
                                    numerator / denominator
                                  else
                                    null
                   }

define Result:
  {
    patient:      Patient,
    reviewPeriod: elm."Review Period",
    periods:      Flatten("24-hour Periods Results")
  }
