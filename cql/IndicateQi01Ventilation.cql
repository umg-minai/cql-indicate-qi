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
//
// Numerator:
//
// Denominator:
//

library "IndicateQi01Ventilation" version '1.0.0'

using OMOP version 'v5.4.MIMIC'

include OMOPHelpers
include IndicateQiElements called elm

code "ARDS Condition": '4195694' from elm.OMOPSV // ICD10 based code: '45552897'

code "Intubated (Tube Present)": '4097216' from elm.OMOPSV

concept "Intubation Tube": {
  "Intubated (Tube Present)"
}

code "Invasive Ventilation Procedure": '37158404' from elm.OMOPSV

concept "Ventilation Procedure": {
  "Invasive Ventilation Procedure"
}

code "Ventilation Mode": '37042784' from elm.OMOPSV

code "PaO2/FiO2 Measurement": '3029943' from elm.OMOPSV

code "PaO2 Default Measurement":              '3027801' from elm.OMOPSV
code "PaO2 Temperature Adjusted Measurement": '3022803' from elm.OMOPSV

concept "PaO2 Measurement": {
  "PaO2 Default Measurement",
  "PaO2 Temperature Adjusted Measurement"
}

code "FiO2 Measurement": '4353936' from elm.OMOPSV

code "PEEP Total, Measured Measurement": '42527140' from elm.OMOPSV
code "PEEP Setting Measurement":         '4216746'  from elm.OMOPSV
code "PEEP General Measurement":         '4353713'  from elm.OMOPSV

concept "PEEP Measurement": {
  "PEEP Total, Measured Measurement",
  "PEEP Setting Measurement",
  "PEEP General Measurement"
}

code "Plateau Pressure": '44782825' from elm.OMOPSV

code "Inpiratory Pressure Setting Measurement": '4215838' from elm.OMOPSV // [cmH2O]
code "Peak Inspiratory Pressure Measurement":   '4101694' from elm.OMOPSV // [mmHg], CAVE different units, has to be converted to [cmH2O]

concept "Inpiratory Pressure Measurement": {
  "Inpiratory Pressure Setting Measurement",
  "Peak Inspiratory Pressure Measurement"
}

code "Tidal Volume Inspiratory Measurement":  '44782826' from elm.OMOPSV
code "Tidal Volume Spontaneuous Measurement": '4108448'  from elm.OMOPSV
code "Tidal Volume Setting Measurement":      '3012410'  from elm.OMOPSV
code "Tidal Volume General Measurement":      '4029625'  from elm.OMOPSV

concept "Tidal Volume Measurement": {
  "Tidal Volume Inspiratory Measurement",
  "Tidal Volume Spontaneuous Measurement",
  "Tidal Volume Setting Measurement",
  "Tidal Volume General Measurement"
}

// PEEP Tables

define function "Low PEEP for FiO2"(FiO2 Quantity):
  Quantity{
    value: case
             when FiO2 < 0.5 '%' then 5
             when FiO2 < 0.6 '%' then 8
             when FiO2 < 0.8 '%' then 10
             when FiO2 < 1.0 '%' then 14
             else 18
           end,
    unit:  'cm[H2O]'
  }

define function "High PEEP for FiO2"(FiO2 Quantity):
  Quantity{
    value: case
             when FiO2 < 0.4 '%' then 5
             when FiO2 < 0.5 '%' then 14
             when FiO2 < 0.6 '%' then 16
             when FiO2 < 0.9 '%' then 20
             else 22
           end,
    unit:  'cm[H2O]'
  }

context Patient

define "PaO2/FiO2 Measurements":
  [Measurement: "PaO2/FiO2 Measurement"] m
    return all m
    sort by measurementDatetime desc

define "Ventilation Mode Obserations":
  [Observation: "Ventilation Mode"]

// TODO(moringenj): what is the correct logic and acceptable precision for comparing times in this context?
define function "PaO2 LOCF"(targetTime DateTime):
  First([Measurement: "PaO2 Measurement"] m
          where convert m to DateTime same hour or before targetTime
          return all m
          sort by measurementDatetime desc)

define function "FiO2 LOCF"(targetTime DateTime):
  First([Measurement: "FiO2 Measurement"] m
          where convert m to DateTime same hour or before targetTime
          return all m
          sort by measurementDatetime desc)

define function "PaO2/FiO2 LOCF"(targetTime DateTime):
  First("PaO2/FiO2 Measurements" m
          where convert m to DateTime same hour or before targetTime
          return all m)

define function "Tidal Volume LOCF"(targetTime DateTime):
  First([Measurement: "Tidal Volume Measurement"] m
          where convert m to DateTime same hour or before targetTime
          return all m
          sort by measurementDatetime desc)

/*define "PaO2 Measurements":
  [Measurement: "PaO2 Measurement"]*/

define "PEEP Measurements":
  [Measurement: "PEEP Measurement"]

// PaO2 unit mm[Hg]
// FiO2 unit %
define function "Ensure PaO2/FiO2"(peepTime DateTime):
  (1) _
    let "PaO2/fiO2": "PaO2/FiO2 LOCF"(peepTime)
      return if "PaO2/fiO2" is not null then
               "PaO2/fiO2"
             else
               (1) __
                 let paO2: "PaO2 LOCF"(peepTime),
                     fiO2: 1 '%' // TODO(moringenj) where should this come from?
                   return if duration in hours between (convert paO2 to DateTime) and peepTime < 6 'h' then
                            paO2 / fiO2
                          else
                            300 'mm[Hg]'

define function "Is mild ARDS"("PaO2/FiO2" Quantity):
  "PaO2/FiO2" > 200 'mm[Hg]'

define function "Recommended PEEP for PaO2"(peepTime DateTime):
  (1) _
    let FiO2:        "FiO2 LOCF"(peepTime),
        "PaO2/FiO2": "Ensure PaO2/FiO2"(peepTime)
      return if "Is mild ARDS"("PaO2/FiO2") then
               "Low PEEP for FiO2"(FiO2)
             else
               "High PEEP for FiO2"(FiO2)

define function "Is Conforming Tidal Volume"(tidalVolume Measurement):
  (1) _
    let tidalVolumeQuantity: convert tidalVolume to Quantity,
        tidalVolumeValue:    if tidalVolumeQuantity is null then // TODO(moringenj): hack for MIMIC
                               tidalVolume.valueAsNumber
                             else
                               (convert tidalVolumeQuantity to 'mL').value,
        idwValue:            elm."Ideal Body Weight Measured or Computed".value
      return if tidalVolumeValue is null then
               Message(null, true, '400', 'Error', 'Tidal volume Unit is "' + tidalVolumeQuantity.unit + '" but must convertible to "mL"')
             else
               tidalVolumeValue in Interval[4 * idwValue, 8 * idwValue]

/*define "Effective Plateau Pressure":
  if "Ventilation Mode" ~ "Volume Driven Ventilation" then
    "Plateau Pressure Measurement"
  else
    "Inspiratory Presse Measurement"*/

/*define "Pressure Difference":
  "Effective Plateau Pressure" - "PEEP Measurement"*/

define function "Is Conforming PEEP"(peepMeasurement Measurement):
  (1) _
    let peepQuantity: convert peepMeasurement to Quantity,
        peepTime:     convert peepMeasurement to DateTime,
        tidalVolume:  "Tidal Volume LOCF"(peepTime),
        pplat:        30 'cm[H2O]', // TODO(moringenj)
        pdelta:       14 'cm[H2O]'
      return     peepQuantity >= "Recommended PEEP for PaO2"(peepTime)
             and if tidalVolume is not null then
                   "Is Conforming Tidal Volume"(tidalVolume)
                 else
                   false
             and pplat <= 30 'cm[H2O]'
             and pdelta <= 14 'cm[H2O]'

define "Conforming PEEP Measurements":
  ("PEEP Measurements") p where "Is Conforming PEEP"(p) return all p

// Quality Indicator

// TODO(moringenj): these must happen at the same time
define "Is in Initial Population":
      Exists([VisitOccurrence: elm."Intensive Care"]) // TODO(moringenj): "Intensive Care Visits in Review Period"
  and Exists([ProcedureOccurrence: "Ventilation Procedure"]) // TODO(moringenj): observation period
  and Exists([DeviceExposure: "Intubation Tube"]) // TODO(moringenj): should this be DeviceExposure?
  and Exists([ConditionOccurrence: "ARDS Condition"])
  and (elm."Age at Start of Review Period" >= 18)

define Denominator:
  Count("PEEP Measurements")

define Numerator:
  Count("Conforming PEEP Measurements")

define QI:
  if "Is in Initial Population" then
    Numerator / Denominator
  else
    null

define debugPeepTime: convert First("PEEP Measurements") to DateTime

define Result:
  {patient: Patient.personId, numerator: Numerator, denominator: Denominator, qi: QI}

define debugResult:
  {
    inInitialPopulation: "Is in Initial Population",

    // debugPeepTime:      debugPeepTime,
    // AllFiOtwo:          [Measurement: "FiO2 Measurement"] m return all convert m to DateTime,
    FiOtwo:             convert "FiO2 LOCF"(debugPeepTime) to Quantity,
    PaOtwoDivFiOTwo:    "Ensure PaO2/FiO2"(debugPeepTime),

    tidalVolumeM:        [Measurement: "Tidal Volume Measurement"] m return all convert m to Quantity,
    recommendedPeep:     "Recommended PEEP for PaO2"(debugPeepTime),
    peepMeasurements:    "PEEP Measurements" m return all convert m to Quantity,

    ventilationMode:     "Ventilation Mode Obserations" o return all o, // convert o to Quantity,

    intensiveCare:       Exists([VisitOccurrence: elm."Intensive Care"]),
    ventilation:         Exists([ProcedureOccurrence: "Ventilation Procedure"]),
    intubated:           Exists([DeviceExposure: "Intubation Tube"]),
    ards:                Exists([ConditionOccurrence: "ARDS Condition"]),
    age:                 (elm."Age at Start of Review Period" >= 18)
  }
