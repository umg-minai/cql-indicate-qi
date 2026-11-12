library IntubatedPeriods

using OMOP version 'v5.4'

include OMOPHelpers

include IndicateQiUtilities called U
include IndicateQiElements called E

include IntubationProcedures
include ExtubationProcedures

context Patient

// Intubated via device exposure

define "Intubation Tube Exposures":
  [DeviceExposure: E."Intubation Tube"] e
    where U.CheckDateTimeInterval(e)
    return all e
    sort by deviceExposureStartDatetime

define "Intubated Periods via Device Exposure":
  "Intubation Tube Exposures" d
    return all convert d to Interval<DateTime>

// Intubated via procedure

define "Intubation Procedures":
  [ProcedureOccurrence: IntubationProcedures."Intubation Procedure"] p
    where U.CheckDateTimeInterval(p)
    sort by procedureDatetime

define "Extubation Procedures":
  [ProcedureOccurrence: ExtubationProcedures."Extubation Procedure"] p
    where U.CheckDateTimeInterval(p)
    sort by procedureDatetime

define "Intubated Periods via Procedure":
  ("Intubation Procedures") i
    // The OMOP CDM documentation states that it is common for
    // procedure_occurrence entries to either have no end time or have
    // identical start and end times. The start time should be used as a
    // fallback value for the end time, if required.
    //
    // If there is no recorded extubation, at least try to limit the intubated
    // period using a following intubation procedure. The following intubation
    // procedure has no corresponding extubation either but at least
    // overlapping periods are prevented. We do not try to limit the intubated
    // period to visit periods because visits may be interrupted without the
    // patient being extubated, for example when the patient leaves the ICU for
    // some procedure and then returns.
    //
    // If there neither an extubation nor another intubation follows a given
    // intubation, the period is unbounded to the right.
    let intubationStart: i.procedureDatetime,
        intubationEnd:   Coalesce(i.procedureEndDatetime, intubationStart),
        extubationStart: Min({
                           First("Extubation Procedures" e
                                   where e.procedureDatetime
                                         same or after intubationEnd
                                   return all e.procedureDatetime),
                           First("Intubation Procedures" ni
                                   where ni.procedureDatetime
                                         after intubationEnd
                                   return all ni.procedureDatetime)
                         })
      return all Interval[intubationStart, extubationStart]
