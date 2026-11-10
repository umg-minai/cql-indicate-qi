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
    let intubationStart: i.procedureDatetime,
        intubationEnd:   i.procedureEndDatetime,
        extubationStart: First(
                           "Extubation Procedures" e
                             where e.procedureDatetime after intubationEnd
                             return all e.procedureDatetime
                         )
      return all Interval[intubationStart, extubationStart]
