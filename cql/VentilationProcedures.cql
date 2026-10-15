library "VentilationProcedures" version '1.0.0'

using OMOP version 'v5.4'

include IndicateQiElements called E

// The code lists in this file are based on ventilation-modes.md in
// https://github.com/umg-minai/indicate-qi-definitions

// Pressure driven ventilation procedures

code "Assist control ventilation pressure control inflation-type":                                                                                                                     '37152410' from E.OMOPSV
code "Assist control ventilation pressure-control inflation-type and assured constant airway pressure adjunct":                                                                        '37152412' from E.OMOPSV
code "Synchronized intermittent mandatory ventilation with pressure-control, an assured constant airway pressure adjunct and pressure-support at the higher pressure level only":      '37152388' from E.OMOPSV
code "Synchronized intermittent mandatory ventilation with pressure-control, one level of pressure-support active during both phases and an assured constant airway pressure adjunct": '37152387' from E.OMOPSV
code "Synchronized intermittent mandatory ventilation with pressure-control, two levels of pressure-support and an assured constant airway pressure adjunct":                          '37152386' from E.OMOPSV
code "Airway pressure release ventilation":                                                                                                                                            '4072515'  from E.OMOPSV
code "Assist control ventilation volume-targeted pressure-control inflation-type":                                                                                                     '37152411' from E.OMOPSV
code "Assist control ventilation volume-targeted pressure-control inflation-type and assured constant airway pressure adjunct":                                                        '37152408' from E.OMOPSV
code "Bilevel positive airway pressure titration":                                                                                                                                     '40491848' from E.OMOPSV
code "Synchronized intermittent mandatory ventilation - pressure-control pressure-support inflation":                                                                                  '37152364' from E.OMOPSV
code "Synchronized intermittent mandatory ventilation - volume targeted pressure-control and pressure-support inflation":                                                              '37152384' from E.OMOPSV
code "Synchronized intermittent mandatory ventilation with synchronized termination pressure-control, pressure-support and an assured constant airway pressure adjunct":               '37152389' from E.OMOPSV
code "Synchronized intermittent mandatory ventilation with volume targeted pressure-control, pressure-support and an assured constant airway pressure adjunct":                        '37152390' from E.OMOPSV
code "Continuous mandatory ventilation pressure-control inflation-type":                                                                                                               '37151337' from E.OMOPSV
code "Continuous mandatory ventilation pressure-control inflation-type and assured constant airway pressure adjunct":                                                                  '37151338' from E.OMOPSV
code "Continuous mandatory ventilation volume-targeted pressure-control inflation-type":                                                                                               '37151339' from E.OMOPSV
code "Dual pressure spontaneous ventilation support":                                                                                                                                  '4055262' from E.OMOPSV
code "Neurally adjusted ventilatory assist":                                                                                                                                           '1243692' from E.OMOPSV

concept "Pressure Driven Ventilation Procedure": {
  "Assist control ventilation pressure control inflation-type",
  "Assist control ventilation pressure-control inflation-type and assured constant airway pressure adjunct",
  "Synchronized intermittent mandatory ventilation with pressure-control, an assured constant airway pressure adjunct and pressure-support at the higher pressure level only",
  "Synchronized intermittent mandatory ventilation with pressure-control, one level of pressure-support active during both phases and an assured constant airway pressure adjunct",
  "Synchronized intermittent mandatory ventilation with pressure-control, two levels of pressure-support and an assured constant airway pressure adjunct",
  "Airway pressure release ventilation",
  "Assist control ventilation volume-targeted pressure-control inflation-type",
  "Assist control ventilation volume-targeted pressure-control inflation-type and assured constant airway pressure adjunct",
  "Bilevel positive airway pressure titration",
  "Synchronized intermittent mandatory ventilation - pressure-control pressure-support inflation",
  "Synchronized intermittent mandatory ventilation - volume targeted pressure-control and pressure-support inflation",
  "Synchronized intermittent mandatory ventilation with synchronized termination pressure-control, pressure-support and an assured constant airway pressure adjunct",
  "Synchronized intermittent mandatory ventilation with volume targeted pressure-control, pressure-support and an assured constant airway pressure adjunct",
  "Continuous mandatory ventilation pressure-control inflation-type",
  "Continuous mandatory ventilation pressure-control inflation-type and assured constant airway pressure adjunct",
  "Continuous mandatory ventilation volume-targeted pressure-control inflation-type",
  "Dual pressure spontaneous ventilation support",
  "Neurally adjusted ventilatory assist"
}

// Volume driven ventilation procedures

code "Assist control ventilation volume-control inflation-type":                                                                                                  '37152409' from E.OMOPSV
code "Assisted controlled mandatory ventilation":                                                                                                                 '4055375'  from E.OMOPSV
code "Synchronized intermittent mandatory ventilation":                                                                                                           '4245036'  from E.OMOPSV
code "Synchronized intermittent mandatory ventilation - volume control pressure-support inflation":                                                               '37152363' from E.OMOPSV
code "Synchronized intermittent mandatory ventilation volume control inflation and an assured constant airway pressure adjunct during expiratory phase":          '37152385' from E.OMOPSV
code "Continuous mandatory ventilation volume-control inflation-type":                                                                                            '37152413' from E.OMOPSV
code "Continuous mandatory ventilation volume-control inflation-type and assured constant airway pressure adjunct in the expiratory phase":                       '37151336' from E.OMOPSV
code "Intermittent mandatory ventilation":                                                                                                                        '37157167' from E.OMOPSV
code "Intermittent mandatory ventilation with synchronized-termination pressure control and assured constant airway pressure adjunct during the inflation phase": '37157430' from E.OMOPSV
code "Intermittent mandatory ventilation with synchronized-termination pressure-control and assured constant airway pressure adjunct":                            '37152407' from E.OMOPSV

concept "Volume Driven Ventilation Procedure": {
  "Assist control ventilation volume-control inflation-type",
  "Assisted controlled mandatory ventilation",
  "Synchronized intermittent mandatory ventilation",
  "Synchronized intermittent mandatory ventilation - volume control pressure-support inflation",
  "Synchronized intermittent mandatory ventilation volume control inflation and an assured constant airway pressure adjunct during expiratory phase",
  "Continuous mandatory ventilation volume-control inflation-type",
  "Continuous mandatory ventilation volume-control inflation-type and assured constant airway pressure adjunct in the expiratory phase",
  "Intermittent mandatory ventilation",
  "Intermittent mandatory ventilation with synchronized-termination pressure control and assured constant airway pressure adjunct during the inflation phase",
  "Intermittent mandatory ventilation with synchronized-termination pressure-control and assured constant airway pressure adjunct"
}

// All ventilation procedures

define "PCV or VCV Ventilation Procedure": System.Concept{
  codes: Flatten({
    "Pressure Driven Ventilation Procedure".codes,
    "Volume Driven Ventilation Procedure".codes
  })}
