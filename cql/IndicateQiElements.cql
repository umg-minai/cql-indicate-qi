library "IndicateQiElements" version '1.0.0'

using OMOP version 'v5.4'

include OMOPHelpers

// TODO: @sgibb, drop default value when leaving testing environment
parameter ReviewPeriod
    default Interval[@2025-04-05T00:00:00.0, @2025-04-20T00:00:00.0)

// Terminology
// The OMOPSV (OMOP Standard Vocabulary) codesystem is built-in and
// uses the OMOP concept id as code.

codesystem OMOPSV: 'https://fhir-terminology.ohdsi.org' // SV = Standardized Vocabulary

// Visit
code "IcuAdmissionDate": '36659961' from OMOPSV     // Intensive care unit (ICU) admission date
code "IcuDischargeDate": '36659649' from OMOPSV     // Intensive care unit (ICU) discharge date

code "Intensive Care": '32037' from OMOPSV

code "D-dimer": '3048530' from OMOPSV    // Fibrin D-dimer DDU [Mass/volume] in Platelet poor plasma

// TODO: @sgibb, use the correct Glc OMOP Concept ID, use the Ddimer for testing
// b/c there are any Glc measurements in the test db
code "Glucose": '3048530' from OMOPSV    // D-dimer
// code "Glucose": '3020491' from OMOPSV    // Glucose [Moles/volume] in Blood
// or
// 3000483

define "IntensiveCarePatients":
    [VisitOccurrence] v
        where v.visitConcept ~ "Intensive Care"
        return all v

define function LengthOfStay(vs List<VisitOccurrence>):
    (vs) v return all duration in days between v.visitStartDate and v.visitEndDate

/*
@examples:
include "IndicateQiElements" called elm
elm."Measurements in Review Period" m where m.measurementConcept ~ elm."Glucose"
*/
define "Measurements in Review Period":
    [Measurement] m
        where m.measurementDatetime in ReviewPeriod
        return all m

/*
@title: Limit Time Period to Review Period
@description: Restrict time period to the given review period.
@param tp: `List` of time `Interval`s defining the visit/observation period.
@param rp: `Interval` of the review period.
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
