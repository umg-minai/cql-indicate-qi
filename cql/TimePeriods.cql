library "TimePeriods" version '1.0.0'

using OMOP version 'v5.4'

include OMOPHelpers
include LocalTimeGermany called L
include IndicateQiElements called E

/// Shifts

// Parameters for controlling the timing of shifts.  Note that the indicator is
// specified as follows:
//
//   Each day is divided into 3 shifts/periods per days:
//   - 06:00:00 to 13:59:59
//   - 14:00:00 to 21:59:59
//   - 22:00:00 to 05:59:59
//
// So there should normally be no reason to change these values.
parameter "Shift Start within Day" Quantity default 6 hours
parameter "Shift Duration"         Quantity default 8 'h'

context Patient

define function "Shifts during Visit"(visit VisitOccurrence, shiftDuration Quantity):
  (1) _
    let periodInterval:  convert visit to Interval<DateTime>,
        periodStartDay:  date from start of periodInterval,
        periodEnd:       end of periodInterval,
        firstShiftStart: L.ExpandDateToDateTime(periodStartDay) + "Shift Start within Day"
      return if firstShiftStart before periodEnd then
               (Expand(Interval[firstShiftStart, periodEnd], shiftDuration)) s
                 let shift: Interval[s, s + shiftDuration)
                   where shift included in periodInterval
                   return all shift
             else
               {}

define function "Shifts during Visits"(visits List<VisitOccurrence>):
  (1) _
    let shiftDuration: Quantity{
                         value: (convert "Shift Duration" to 's').value,
                         unit:  'seconds'
                       }
      return all (visits) visit
                   return all "Shifts during Visit"(visit, shiftDuration)

define "Shifts in Visits":
  "Shifts during Visits"(E."Intensive Care Visits in Review Period")

/// 24-hour Periods

// Each period starts at 6:00 and ends 24 h later at 5:59 of the
// following day. All periods of this kind that fall within the visits
// are initially generated even though some of those at the beginning
// and at the end of the visit may not be used due to exclusion rules.
define function "24-hour Periods during Visit"(visit VisitOccurrence):
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

define function "24-hour Periods during Visits"(visits List<VisitOccurrence>):
  (visits) v
    let periods: "24-hour Periods during Visit"(v)
      where Exists(periods)
      return all periods

define "24-hour Periods in Visits":
  "24-hour Periods during Visits"(E."Intensive Care Visits in Review Period")
