library "IndicateQiElements" version '1.0.0'

using OMOP version 'v5.4'

//include OMOPHelpers

// Terminology
// The OMOPSV (OMOP Standard Vocabulary) codesystem is built-in and
// uses the OMOP concept id as code.

codesystem OMOPSV: 'https://fhir-terminology.ohdsi.org' // SV = Standardized Vocabulary

// Visit
code "IcuAdmissionDate": '36659961' from OMOPSV     // Intensive care unit (ICU) admission date
code "IcuDischargeDate": '36659649' from OMOPSV     // Intensive care unit (ICU) discharge date

code "Intensive Care": '32037' from OMOPSV

//define IntensiveCarePatients:
//    [VisitOccurrence] v
//        where v.visitConcept ~ "Intensive Care"
//        return all v

//define LengthOfStay:
//    [VisitOccurrence] v return all (duration in days between v.visitStartDate and v.visitEndDate)

//define function LengthOfStayF1(Start DateTime, End DateTime):
//  return all duration in days Start and End
//
//define function LengthOfStayF2(v List<VisitOccurrence>):
//  duration in days v.visitStartDate and v.visitEndDate
