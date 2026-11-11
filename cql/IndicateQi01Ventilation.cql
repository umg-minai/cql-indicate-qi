// Name     01 - Ventilation
// Version  1.0
//
// Description:
//   Lung-protective mechanical ventilation should reduce inflammation and lung
//   damage. Therefore patients with ARDS should be ventilated with a tidal
//   volume around 6 mL/kg ideal body weight (IBW).  The positive end
//   expiratory pressure (PEEP) should be adjusted according to the ARDSnet
//   PEEP table (mild ARDS: low PEEP table, moderate/severe ARDS: high PEEP
//   table).  The plateau pressure should be lower or equal 30 cmH2O.  The
//   inspiratory pressure difference (driving pressure, Pdelta) should be
//   lower or equal 14 cmH2O.

library "IndicateQi01Ventilation" version '1.0.0'

using OMOP version 'v5.4'

include OMOPHelpers

include Intervals called I
include TimePeriods called T

include IndicateQiUtilities called U
include IndicateQiElements called elm

include TidalVolumeMeasurements
include IntubatedPeriods

code "Invasive Ventilation Procedure": '37158404' from elm.OMOPSV

code "ARDS Condition": '4195694' from elm.OMOPSV // ICD10 based code: '45552897'

code "Horowitz index in Arterial blood":                                         '3029943' from elm.OMOPSV
code "Horowitz index adjusted to patients actual temperature in Arterial blood": '3029268' from elm.OMOPSV
concept "PaO2/FiO2 (Horowitz index) Measurement": {
  "Horowitz index in Arterial blood",
  "Horowitz index adjusted to patients actual temperature in Arterial blood"
}

code "PaO2 Default Measurement":              '3027801' from elm.OMOPSV
code "PaO2 Temperature Adjusted Measurement": '3022803' from elm.OMOPSV

concept "PaO2 Measurement": {
  "PaO2 Default Measurement",
  "PaO2 Temperature Adjusted Measurement"
}

code "Inspired oxygen concentration":                                         '4353936' from elm.OMOPSV
code "Oxygen/Inspired gas Respiratory system --on ventilator":                '3026238' from elm.OMOPSV
code "Oxygen/Inspired gas Respiratory system by O2 Analyzer --on ventilator": '3025408' from elm.OMOPSV
code "Oxygen/Total gas setting [Volume Fraction] Ventilator":                 '3024882' from elm.OMOPSV

concept "FiO2 Measurement": {
  "Inspired oxygen concentration",
  "Oxygen/Inspired gas Respiratory system --on ventilator",
  "Oxygen/Inspired gas Respiratory system by O2 Analyzer --on ventilator",
  "Oxygen/Total gas setting [Volume Fraction] Ventilator"
}

code "Total PEEP Respiratory system":                       '42527140' from elm.OMOPSV // LOINC   measurement
code "Positive end expiratory pressure setting Ventilator": '3022875'  from elm.OMOPSV // LOINC   measurement
code "Positive end expiratory pressure setting":            '4216746'  from elm.OMOPSV // SNOMED  observation
code "Positive end expiratory pressure":                    '4353713'  from elm.OMOPSV // SNOMED  observation

concept "PEEP Measurement": {
  "Total PEEP Respiratory system",
  "Positive end expiratory pressure setting Ventilator"
}

concept "PEEP Observation": {
  "Positive end expiratory pressure setting",
  "Positive end expiratory pressure"
}

code "Airway plateau pressure":                                                             '44782825' from elm.OMOPSV
code "Airway pressure --at zero inspiratory flow on ventilator":                            '3006369' from elm.OMOPSV
code "Airway pressure by Airway pressure monitor --at zero inspiratory flow on ventilator": '3012810' from elm.OMOPSV
code "Dynamic plateau pressure":                                                            '21490565' from elm.OMOPSV
code "Pressure.plateau Respiratory system airway":                                          '36304439' from elm.OMOPSV
code "Pressure.plateau Respiratory system airway --on ventilator":                          '36303946' from elm.OMOPSV

concept "Plateau Pressure Measurement": {
  "Airway plateau pressure",
  "Airway pressure --at zero inspiratory flow on ventilator",
  "Airway pressure by Airway pressure monitor --at zero inspiratory flow on ventilator",
  "Dynamic plateau pressure",
  "Pressure.plateau Respiratory system airway",
  "Pressure.plateau Respiratory system airway --on ventilator"
}

// PEEP Tables

// The following two functions are called only with quantities with unit '1'
// so that no repeated conversion is necessary.
define function "Low PEEP for FiO2"(FiO2 Quantity):
  Quantity{
    value: case
             when FiO2 < 0.5 '1' then 5
             when FiO2 < 0.6 '1' then 8
             when FiO2 < 0.8 '1' then 10
             when FiO2 < 1.0 '1' then 14
             else 18
           end,
    unit:  'cm[H2O]'
  }

define function "High PEEP for FiO2"(FiO2 Quantity):
  Quantity{
    value: case
             when FiO2 < 0.4 '1' then 5
             when FiO2 < 0.5 '1' then 14
             when FiO2 < 0.6 '1' then 16
             when FiO2 < 0.9 '1' then 20
             else 22
           end,
    unit:  'cm[H2O]'
  }

context Patient

// Sorted in reverse chronological order for "Last Observation Carried
// Forward" (LOCF) logic below.
define "PaO2 Measurements":
  [Measurement: "PaO2 Measurement"] m
    where U.EnsureQuantityWithUnit('PaO2 measurement', m, 'mm[Hg]') is not null
    return all m
    sort by measurementDatetime desc

define "FiO2 Measurements":
  [Measurement: "FiO2 Measurement"] m
    where (1) _
            let quantity: U.EnsureQuantity('FiO2 measurement', m)
              // Make sure that other dimensionless units don't slip through.
              // This is unlikely but for example convert 1 '[IU]' to '%'
              // "works" in CQL.
              return case
                       when quantity is null then
                         false
                       when not (quantity.unit in { '1', '%' }) then
                         U.SignalProblemWithValue(
                           'FiO2 measurement unit must be either \'1\' or \'%\','
                           + ' not \'' + quantity.unit + '\'',
                           false
                         )
                       else
                         true
                     end
    return all m
    sort by measurementDatetime desc

define "PaO2/FiO2 (Horowitz index) Measurements":
  [Measurement: "PaO2/FiO2 (Horowitz index) Measurement"] m
    where U.EnsureQuantityWithUnit('Horowitz index', m, 'mm[Hg]') is not null
    return all m
    sort by measurementDatetime desc

// This is not sorted like the other measurements because the PEEP
// measurements dictate the timing and the other measurements are carried
// forward to align with the PEEP measurements.
define "PEEP Measurements":
  [Measurement: "PEEP Measurement"] m
    return all m
    sort by measurementDatetime

define "PEEP Observations":
  [Observation: "PEEP Observation"] o
    return all o
    sort by observationDatetime

define "Ordered PEEP Data":
  (Flatten({
    "PEEP Measurements" m
      let quantity: U.EnsureQuantityWithUnit('PEEP Measurement', m, 'cm[H2O]')
        where quantity is not null
        return all { concept:  m.measurementConcept,
                     datetime: convert m to DateTime,
                     quantity: quantity },
    "PEEP Observations" o
      let quantity: U.EnsureQuantityWithUnit('PEEP Observation', o, 'cm[H2O]')
        where quantity is not null
        return all { concept:  o.observationConcept,
                     datetime: convert o to DateTime,
                     quantity: quantity }
  })) d
    return all d
    sort by datetime

define function "PEEP Concept Priority"(omopConcept OMOP.Concept):
  // Preference order for different kinds of PEEP measurements and
  // observations, concepts with lower number are preferred over concepts with
  // higher numbers.
  (1) _
    let systemCode: convert omopConcept to System.Code
      return case systemCode
               when "Total PEEP Respiratory system"                       then 1
               when "Positive end expiratory pressure setting"            then 2
               when "Positive end expiratory pressure"                    then 3
               when "Positive end expiratory pressure setting Ventilator" then 4
               else                                                            null
             end

define "PEEP Data":
  // Iterate through "Ordered PEEP Data" which is ordered according to
  // measurement/observation time and identify items with identical times. For
  // those, keep only the item with the lower priority number.
  (1) _
    let result: ("Ordered PEEP Data") d aggregate r
                     starting ({ previous: null,
                                 result:   {} }
                               as Tuple{previous Tuple{concept  OMOP.Concept,
                                                       datetime DateTime,
                                                       quantity Quantity},
                                        result   List<Tuple{concept  OMOP.Concept,
                                                            datetime DateTime,
                                                            quantity Quantity}>}):
                  case
                    // Data items generated at different times or no previous
                    // data item.
                    when    r.previous is null
                         or not (r.previous.datetime = d.datetime) then
                      { previous: d, result: Flatten({ r.result, {r.previous } }) }
                    // "New" item has lower priority number -> use "new" item
                    // by replacing old item.
                    when   "PEEP Concept Priority"(d.concept)
                         < "PEEP Concept Priority"(r.previous.concept) then
                      { previous: d, result: r.result }
                    // "Old" item has lower (or equal) priority number -> use
                    // "old" item by ignoring new item.
                    else
                      r
                  end
      // Flush final tentative item, if any, into result list.
      return if result.previous is not null then
               Flatten({ result.result, { result.previous } })
             else
               result.result

define "Plateau Pressure Measurements":
  [Measurement: "Plateau Pressure Measurement"] m
    return all m
    sort by measurementDatetime desc

define "Ventilation Procedures":
  [ProcedureOccurrence: "Invasive Ventilation Procedure"] p
    where U.CheckDateTimeInterval(p)
    return all p

define "ARDS Conditions":
  [ConditionOccurrence: "ARDS Condition"] c
    where U.CheckDateTimeInterval(c)
    return all c

// In CQL
//
//   @2026-06-17T10:11:12 same or before @2026-06-17T10:11:12 => true
//   @2026-06-17T10:11:13 same or before @2026-06-17T10:11:12 => false
//
// but
//
//   @2026-06-17T10:11 same or before @2026-06-17T10:11:12 => null
//
// In this use case, we want the third example to evaluate to true.  For
// greater precision mismatches, we want false.
define function "Same or Before with Minute Precision"(earlier DateTime,
                                                       later   DateTime):
  (1) _
    let fullPrecisionResult:   earlier same or before later,
        minutePrecisionResult: earlier same minute or before later
      return case
               when fullPrecisionResult is not null then
                 fullPrecisionResult
               when minutePrecisionResult is not null then
                 minutePrecisionResult
               else
                 false
             end

// Last Observation Carried Forward
define function "PaO2 LOCF"(targetTime DateTime):
  First("PaO2 Measurements" m
          where "Same or Before with Minute Precision"(
                  convert m to DateTime,
                  targetTime
                )
          return all m)

define function "FiO2 LOCF"(targetTime DateTime):
  First("FiO2 Measurements" m
          where "Same or Before with Minute Precision"(
                  convert m to DateTime,
                  targetTime
                )
          return all m)

define function "PaO2/FiO2 LOCF"(targetTime DateTime):
  First("PaO2/FiO2 (Horowitz index) Measurements" m
          where "Same or Before with Minute Precision"(
                  convert m to DateTime,
                  targetTime
                )
          return all m)

define function "Plateau Pressure Measurement LOCF"(targetTime DateTime):
  First("Plateau Pressure Measurements" m
          where "Same or Before with Minute Precision"(
                  convert m to DateTime,
                  targetTime
                )
          return all m)

define "Usable Tidal Volume Measurements":
  // Select Tidal Volume measurements according to the "Tidal volume (Vt)"
  // (322) concept set. All concept in that concept use the unit mL for the
  // measurements.  We Do not retrieve measurements according to the "Tidal
  // volume per body weight (Vt/kg)" concept set since such measurements are
  // uncommon and would require scaling with the (actual) body weight.
  [Measurement: TidalVolumeMeasurements."Tidal Volume Measurements"] m
    // TODO(moringenj): include the measurement in the message once we have ToString for Measurement
    where U.EnsureQuantityWithUnit('Tidal volume measurement', m, 'mL') is not null
    return all m
    sort by measurementDatetime desc

define function "Tidal Volume LOCF"(targetTime DateTime):
  First(("Usable Tidal Volume Measurements") m
          where m same hour or before targetTime
          return all m)

// PaO2 unit mm[Hg], FiO2 unit either '1' or '%'.  This function produces mm[Hg].
define function "Ensure PaO2/FiO2"(peepTime DateTime):
  (1) _
    let "PaO2/fiO2": "PaO2/FiO2 LOCF"(peepTime)
      return if "PaO2/fiO2" is not null then
               "PaO2/fiO2"
             else
               (1) __
                 let paO2:     "PaO2 LOCF"(peepTime),
                     paO2Time: (convert paO2 to DateTime),
                     // TODO(moringenj): is this correct for fiO2?
                     fiO2:     "FiO2 LOCF"(peepTime)
                   // If the paO2 measurement is within 6 hours of the
                   // PEEP measurement, use the paO2 and fiO2
                   // measurements.  Otherwise assume mild ARDS by
                   // returning 300 'mm[Hg]' which is classified as mild
                   // below.
                   return if (duration in hours between paO2Time and peepTime) < 6 then
                            paO2 / fiO2
                          else
                            300 'mm[Hg]'

define function "Is mild ARDS"("PaO2/FiO2" Quantity):
  "PaO2/FiO2" > 200 'mm[Hg]'

define function "ARDS Condition Periods in Period"(period Interval<DateTime>):
  I.UnionIntervals(
    "ARDS Conditions" c
      let ardsInterval: (convert c to Interval<DateTime>)
        where ardsInterval overlaps period
        return all ardsInterval intersect period,
    // In some datasets, ARDS is not represented explicitly as an
    // ConditionOccurrence. To support these datasets, apply a
    // alternative criterion based on a clinical definition of ARDS. The
    // computation of the second criterion can either use the Horowitz index
    // directly or calculate it from PaO2 and FiO2 measurements.
    //
    // We combine the intervals for the Horowitz index measurements and
    // separate PaO2 and FiO2 measurements since they may represent
    // measurements taken at different times.
    I.UnionIntervals(
      "PaO2/FiO2 (Horowitz index) Measurements" horowitzMeasurement
        where     horowitzMeasurement in period
              and (convert horowitzMeasurement to Quantity) < 200 'mm[Hg]'
        return all (1) _
                     let dateTime: convert horowitzMeasurement to DateTime
                       return Interval[dateTime, dateTime],
      "PaO2 Measurements" paO2Measurement
        // Find a FiO2 measurement that precedes the
        // selected PaO2 measurement. If there is one, make
        // sure it is within 60 minutes of the PaO2
        // measurement. If both measurements are available,
        // compute the fallback criterion.
        let paO2Time:        convert paO2Measurement to DateTime,
            fiO2Measurement: "FiO2 LOCF"(paO2Time),
            fiO2Time:        convert fiO2Measurement to DateTime
          where     paO2Time during period
                and (duration in minutes between fiO2Time and paO2Time) <= 60
                and ((convert paO2Measurement to Quantity)
                     / (convert fiO2Measurement to Quantity)) < 200 'mm[Hg]'
          return all Interval[paO2Time, paO2Time]
    )
  )

define function "Recommended PEEP for PaO2"(peepTime DateTime):
  (1) _
    let FiO2:         "FiO2 LOCF"(peepTime),
        // Implicit conversion to OMOP.Quantity followed by explicit unit
        // conversion to '1' (fraction, possible conversion from '%'). The
        // conversion cannot fail because FiO2 measurements are eagerly checked
        // for convertibility to unit '1'.
        FiO2Quantity: convert FiO2 to '1',
        "PaO2/FiO2":  "Ensure PaO2/FiO2"(peepTime)
      return if "Is mild ARDS"("PaO2/FiO2") then
               "Low PEEP for FiO2"(FiO2Quantity)
             else
               "High PEEP for FiO2"(FiO2Quantity)

define function "Is Conforming Tidal Volume"(tidalVolume Measurement):
  (1) _
    // No need to use an error-checking conversion for tidalVolume since
    // "Usable Tidal Volume Measurements" has already checked everything,
    // including the conversion to mL.
    let tidalVolumeQuantity:  convert tidalVolume to Quantity,
        tidalVolumeValue:     (convert tidalVolumeQuantity to 'mL').value,
        tidalVolumeTime:      convert tidalVolume to DateTime,
        // The function returns the ideal body weight expressed in a unit of
        // mass that is either kg itself or convertible to kg.
        idealBodyWeight:      elm."Ideal Body Weight Measured or Computed Before"(
                                tidalVolumeTime
                              ),
        idealBodyWeightValue: (convert idealBodyWeight to 'kg').value
      return tidalVolumeValue in Interval[
                                   4 * idealBodyWeightValue,
                                   8 * idealBodyWeightValue
                                 ]

define function "Effective Plateau Pressure"(peepTime DateTime):
  // This used to select either "Plateau Pressure Measurement LOCF" if
  // available for peepTime or "Peak Inspiratory Pressure LOCF" for peepTime
  // if available and "Ventilation Mode" for peepTime was 'Pressure Driven'.
  // Since determining the ventilation mode proved too unreliable, the fallback
  // to "Peak Inspiratory Pressure LOCF" is no longer attempted.
  (1) _
    let plateauPressureMeasurement: "Plateau Pressure Measurement LOCF"(peepTime)
      return if plateauPressureMeasurement is not null then
               U.EnsureQuantityWithUnit('Plateau pressure measurement',
                                        plateauPressureMeasurement,
                                        'cm[H2O]')
             else
               null

define function "Is Conforming PEEP"(peepMeasurement Tuple{concept  OMOP.Concept,
                                                           datetime DateTime,
                                                           quantity Quantity}):
  (1) _
    let peepQuantity:       peepMeasurement.quantity,
        peepTime:           peepMeasurement.datetime,
        tidalVolume:        "Tidal Volume LOCF"(peepTime),
        plateauPressure:    "Effective Plateau Pressure"(peepTime),
        pressureDifference: plateauPressure - peepQuantity,
        recommendedPEEP:    "Recommended PEEP for PaO2"(peepTime)
      return     peepQuantity >= recommendedPEEP
             and if tidalVolume is not null then
                   "Is Conforming Tidal Volume"(tidalVolume)
                 else
                   false
             and plateauPressure <= 30 'cm[H2O]'
             and pressureDifference <= 14 'cm[H2O]'

// Quality Indicator

define function "Is in Initial Population"(visitInterval Interval<DateTime>):
      AgeInYearsAt(start of visitInterval) >= 18
  and Exists(collapse(
        I.IntersectIntervals(
          "Ventilation Procedures" p
            let ventilationInterval: convert p to Interval<DateTime>
              where ventilationInterval overlaps visitInterval
              return all ventilationInterval,
          I.IntersectIntervals(
            I.UnionIntervals(
              IntubatedPeriods."Intubated Periods via Device Exposure" i
                where i overlaps visitInterval
                return all i intersect visitInterval,
              IntubatedPeriods."Intubated Periods via Procedure" i
                where i overlaps visitInterval
                return all i intersect visitInterval
            ),
            "ARDS Condition Periods in Period"(visitInterval)
          )
        )
      ))

define "Visit Results":
  (T."Visits with 24-hour Periods") visitWithPeriods
    let visitInterval:               visitWithPeriods.visit,
        inInitialPopulationForVisit: "Is in Initial Population"(visitInterval),
        measurementsInVisit:         ("PEEP Data") d
                                       where d.datetime in visitInterval
                                       return all d
      return all (visitWithPeriods.fullyContainedPeriods) period
                   let measurementsInPeriod: (measurementsInVisit) m
                                               where m.datetime in period
                                               return all m,
                       goodMeasurements:     (measurementsInPeriod) m
                                               where "Is Conforming PEEP"(m)
                                               return all m,
                       numerator:            Count(goodMeasurements),
                       denominator:          Count(measurementsInPeriod)
                     return all elm."Period Result"(period,
                                                    inInitialPopulationForVisit,
                                                    numerator,
                                                    denominator)

define Result: elm."Overall Result"(Patient, "Visit Results")


define "Debug Results":
  Flatten(
    (T."Visits with 24-hour Periods") visitWithPeriods
      let visitInterval:               visitWithPeriods.visit,
          inInitialPopulationForVisit: "Is in Initial Population"(visitInterval),
          measurementsInVisit:         ("PEEP Measurements") m
                                         where m in visitInterval
                                         return all m
        return all (visitWithPeriods.overlappingPeriods) p
          let measurementsInPeriod:        (measurementsInVisit) m
                                             where m in p
                                             return all m,
              peepQuantity:                Median(
                                             (measurementsInPeriod) m
                                               return all convert m to Quantity
                                           ),
              tidalVolume:                 Median(
                                             "Usable Tidal Volume Measurements" m
                                               where m in p
                                               return all m
                                           ),
              tidalVolumeLocf:             Median(
                                             (measurementsInPeriod) m
                                               let peepTime: convert m to DateTime
                                                 return all "Tidal Volume LOCF"(peepTime)
                                           ),
              plateauPressure:             Median(
                                             "Plateau Pressure Measurements" m
                                               where m in p
                                               return all m
                                           ),
              plateauPressureLocf:         Median(
                                             (measurementsInPeriod) m
                                               let peepTime: convert m to DateTime
                                                 return all "Effective Plateau Pressure"(peepTime)
                                           ),
              pressureDifference:          Median(
                                             (measurementsInPeriod) m
                                               let peepTime: convert m to DateTime
                                                 return all plateauPressure - peepQuantity
                                           ),
              recommendedPEEP:             Median(
                                             (measurementsInPeriod) m
                                               let peepTime: convert m to DateTime
                                                 return all "Recommended PEEP for PaO2"(peepTime)
                                           ),
              ventilationProcedureCount:   Count(
                                             "Ventilation Procedures" o
                                               where convert o to Interval<DateTime> overlaps p
                                               return all o
                                           ),
              intubationTubeExposureCount: Count(
                                             "Intubation Tube Exposures" e
                                               where convert e to Interval<DateTime> overlaps p
                                               return all e
                                           ),
              ardsCondition:               if "ARDS Condition in Period"(p) then 1.0 else 0.0,
              paO2:                        Median(
                                             "PaO2 Measurements" m
                                               where m in p
                                               return all m
                                           ),
              paO2Locf:                    Median(
                                             (measurementsInPeriod) m
                                               let peepTime: convert m to DateTime
                                                 return all "PaO2 LOCF"(peepTime)
                                           ),
              fiO2:                        Median(
                                             "FiO2 Measurements" m
                                               where m in p
                                               return all m
                                           ),
              fiO2Locf:                    Median(
                                             (measurementsInPeriod) m
                                               let peepTime: convert m to DateTime
                                                 return all "FiO2 LOCF"(peepTime)
                                           )
          return all {
                       period: p,
                       values: {
                                 (convert peepQuantity          to 'cm[H2O]').value as Decimal,
                                 (convert tidalVolume           to 'mL')     .value as Decimal,
                                 (convert tidalVolumeLocf       to 'mL')     .value as Decimal,
                                 (convert plateauPressure       to 'cm[H2O]').value as Decimal,
                                 (convert plateauPressureLocf   to 'cm[H2O]').value as Decimal,
                                 (convert pressureDifference    to 'cm[H2O]').value as Decimal,
                                 (convert recommendedPEEP       to 'cm[H2O]').value as Decimal,
                                 convert ventilationProcedureCount                  to Decimal,
                                 convert intubationTubeExposureCount                to Decimal,
                                 ardsCondition,
                                 (convert paO2                  to 'mm[Hg]') .value as Decimal,
                                 (convert paO2Locf              to 'mm[Hg]') .value as Decimal,
                                 (convert fiO2                  to '%')      .value as Decimal,
                                 (convert fiO2Locf              to '%')      .value as Decimal
                               }
                     }
  )
