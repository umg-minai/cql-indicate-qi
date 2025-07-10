library "IndicateQiElements" version '1.0.0'

using OMOP version 'v5.4'

include OMOPHelpers

// TODO: @sgibb,: drop default value when leaving testing environment
parameter "Review Period"
    default Interval[@2025-04-05T00:00:00.0, @2025-04-20T00:00:00.0)

// Terminology
// The OMOPSV (OMOP Standard Vocabulary) codesystem is built-in and
// uses the OMOP concept id as code.
codesystem OMOPSV: 'https://fhir-terminology.ohdsi.org' // SV = Standardized Vocabulary

// Visit
code "IcuAdmissionDate": '36659961' from OMOPSV     // Intensive care unit (ICU) admission date
code "IcuDischargeDate": '36659649' from OMOPSV     // Intensive care unit (ICU) discharge date

code "Intensive Care": '32037' from OMOPSV

context Patient

/*
@title: Valid visits occurrences
@description: Limit visits to valid visits, where the admission is before the
discharge.
@return: Valid visits sorted by admission date.
@author: Sebastian Gibb <mail@sebastiangibb.de>
@examples
include "IndicateQiElements" called elm
elm."Valid VisitOccurence"
*/
define "Valid VisitOccurrence":
  ([VisitOccurrence] v sort by visitStartDatetime) v
  where v.visitStartDatetime <= v.visitEndDatetime
  return all v

/*
@title: Age in Years
@description: AgeInYearsAt is not working in CQL-on-OMOP with the current test
data. This function calculate the age based on the year, month, day information
given.
@param: p
@param: reftime reference time, e.g. today.
@return: Integer, age in years
@examples:
include "IndicateQiElements" called elm
elm.iqAgeInYears([Person ] p, end of elm."Review Period")
*/
define function iqAgeInYears(person List<Person>, reftime DateTime):
  (person) p return CalculateAgeInYearsAt(
    Date(p.yearOfBirth, p.monthOfBirth, p.dayOfBirth), (reftime) r
  )

/*
@title: Intensive Care Visits
@description: Limit visits/population to adult intensive care patients.
@return: Entries with an "Intensive Care" concept.
@author: Sebastian Gibb <mail@sebastiangibb.de>
@examples:
include "IndicateQiElements" called elm
elm."Intensive Care Visits"
*/
// TODO: @sgibb, limit to adults if supported by CQL-on-OMOP
/*define "Intensive Care Visits":
    "Valid VisitOccurrence" v
        where v.visitConcept ~ "Intensive Care" 
        //   and AgeInYearsAt(start of "Review Period") >= 18
        return all v
*/
// workaround; needs `context Patient` and `,focus [Person]` in the REPL
define "Intensive Care Visits":
  "Valid VisitOccurrence" v 
        where v.visitConcept ~ "Intensive Care" 
          and CalculateAgeInYearsAt(
            Date(Patient.yearOfBirth, Patient.monthOfBirth, Patient.dayOfBirth),
            start of "Review Period"
          ) >= 18
        return all v

/*
@title: Intensive Care Visits in Review Period
@description: Limit visits/population to adult intensive care patients in the
review period.
@return: Entries with an "Intensive Care" concept in the Review Period
@author: Sebastian Gibb <mail@sebastiangibb.de>
@examples:
include "IndicateQiElements" called elm
elm."Intensive Care Visits in Review Period"
*/
define "Intensive Care Visits in Review Period":
  "Intensive Care Visits" v
    where v.visitStartDatetime after start of "Review Period" 
      and v.visitEndDatetime before end of "Review Period"
    return all v

/*
@examples
include "IndicateQiElements" called elm
code "Glucose": '3020491' from elm.OMOPSV
elm."Measurements in Review Period" m where m.measurementConcept ~ "Glucose"
*/
define "Measurements in Review Period":
    [Measurement] m
        where m.measurementDatetime in "Review Period"
        return all m

/*
@title: Lenght of stay
@description: Returns the duration of the given visits periods.
@param: vs `List` of time `VisitOccurrence`s defining the visit period.
@return: duration of the visit.
@author: Sebastian Gibb <mail@sebastiangibb.de>
@examples:
include "IndicateQiElements" called elm
elm.LengthOfStay(elm.IntensiveCarePatients)
*/
define function LengthOfStay(vs List<VisitOccurrence>):
    (vs) v return all duration in days between v.visitStartDate and v.visitEndDate

/*
@title: Limit Time Period to Review Period
@description: Restrict time period to the given review period.
@param: tp `List` of time `Interval`s defining the visit/observation period.
@param: rp `Interval` of the review period.
@return: intersection time and review period.
@author: Sebastian Gibb <mail@sebastiangibb.de>
@examples:
include "IndicateQiElements" called elm
define b:
    ({Interval[@1990-01-01, @1990-12-31],
      Interval[@2025-04-05, @2025-04-08],
      Interval[@2025-04-05, @2025-04-18],
      Interval[@2025-04-18, @2025-04-25]})
define rp:
    Interval[@2025-04-05T00:00:00.0, @2025-04-20T00:00:00.0)
elm.LimitPeriod(b, rp)
*/
define function LimitPeriod(tp List<Interval<DateTime>>, rp Interval<DateTime>):
    (tp) p return all p intersect (rp)

// vim: filetype=cql

