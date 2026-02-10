// Name     02 - Weaning
// Version  1.0
//
// Description:
//   The duration of mechanical ventilation should be as short as
//   possible. Daily spontaneous breathing trials seem to be important for a
//   fast weaning.
//
// Numerator:
//
// Denominator:
//

library "IndicateQi02Weaning" version '1.0.0'

using OMOP version 'v5.4'

include OMOPHelpers

include Intervals called I
include LocalTimeGermany called L
include TimePeriods called T

include IndicateQiElements called elm

// TODO(moringenj): shared with IndicateQi01Ventilation
code "Intubated (Tube Present)": '4097216' from elm.OMOPSV

concept "Intubation Tube": {
  "Intubated (Tube Present)"
}

code "Invasive Ventilation Procedure": '37158404' from elm.OMOPSV

concept "Ventilation Procedure": {
  "Invasive Ventilation Procedure"
}

code "Trial of Spontaneous Breathing Procedure": '4308797' from elm.OMOPSV

concept "Trial of Spontaneous Breathing": {
  "Trial of Spontaneous Breathing Procedure"
}

code "Normal Extubation Procedure": '4148972' from elm.OMOPSV

code "Inadvertent Extubation Procedure": '4231838' from elm.OMOPSV

concept "Extubation": {
  "Normal Extubation Procedure",
  "Inadvertent Extubation Procedure"
}

context Patient

define "Ventilation Procedures":
  [ProcedureOccurrence: "Ventilation Procedure"] p
    where convert p to Interval<DateTime> overlaps elm."Review Period"

define "Ventilation Periods":
  "Ventilation Procedures" p return all convert p to Interval<DateTime>

define "Trial of Spontaneous Breathing Procedures":
  [ProcedureOccurrence: "Trial of Spontaneous Breathing"] p
    where convert p to Interval<DateTime> overlaps elm."Review Period"
    return all p
    sort by procedureDatetime

define "Extubation Procedures":
  [ProcedureOccurrence: "Extubation"] p
    where convert p to Interval<DateTime> overlaps elm."Review Period"
    return all p
    sort by procedureDatetime

define "Periods without Ventilation":
  I.SubtractFromInterval(elm."Review Period", "Ventilation Periods")

// Spontaneous Breathing Trial

define function "Is Spontaneous Breathing Trial in Period"(period Interval<DateTime>):
     Exists("Trial of Spontaneous Breathing Procedures" p
              where convert p to Interval<DateTime> overlaps period)
  or Exists("Extubation Procedures" p
              where convert p to Interval<DateTime> overlaps period)
  or Exists("Periods without Ventilation" p where p overlaps period)

// 24-hour periods

// In this variant, each period start at 6:00 and ends 24 h later at
// 5:59. All periods of this kind that fall within the visits are
// initially generated even though some of those at the beginning and at
// the end of the visit may not be used due to exclusion rules.
/*define function "24-hour Periods during Visit"(visit VisitOccurrence):
  (1) _
    let periodInterval:   convert visit to Interval<DateTime>,
        periodStartDay:   date from start of periodInterval,
        periodEnd:        end of periodInterval,
        firstPeriodStart: L.ExpandDateToDateTime(periodStartDay) + 6 hours,
        dayDuration:      Quantity{value: (convert 1 'd' to 's').value, unit: 'seconds'}
      return if firstPeriodStart before periodEnd then
               (Expand(Interval[firstPeriodStart, periodEnd], dayDuration)) s
                 let period: Interval[s, s + dayDuration)
                   where period included in periodInterval
                   return all period
             else
               {}

define "24-hour Periods during Visits":
  (elm."Intensive Care Visits in Review Period") v
    let periods: "24-hour Periods during Visit"(v)
      where Exists(periods)
      return all periods*/

define "24-hour Periods with Spontaneous Breathing Trial during Visits":
  T."24-hour Periods in Visits" periods
    return all ((periods) p
                  where "Is Spontaneous Breathing Trial in Period"(p)
                  return all p)

define "24-hour Periods":
  Flatten(T."24-hour Periods in Visits")

define "24-hour Periods with Spontaneous Breathing Trial":
  Flatten("24-hour Periods with Spontaneous Breathing Trial during Visits")

// Quality Indicator

// TODO(moringenj): these must happen at the same time
define "Is in Initial Population":
      Exists(elm."Intensive Care Visits in Review Period")
  and Exists([DeviceExposure: "Intubation Tube"])
  // TODO(moringenj): ventilation must be at least 48 hours
  and Exists("Ventilation Procedures")
  and (elm."Age at Start of Review Period" >= 18)

define "24-hour Periods Results":
  (T."24-hour Periods in Visits") periods
    return all (periods) p
                 let numerator:   Count(("24-hour Periods with Spontaneous Breathing Trial") s
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
