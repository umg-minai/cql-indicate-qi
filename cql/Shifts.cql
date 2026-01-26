library "Shifts" version '1.0.0'

using OMOP version 'v5.4'

include OMOPHelpers
include LocalTimeGermany called L

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
