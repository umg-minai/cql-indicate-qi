library "ExtubationProcedures"

include IndicateQiElements called E

code "Extubation of trachea (normal)":                '4148972' from E.OMOPSV
code "Removal of endotracheal tube":                  '4150627' from E.OMOPSV
code "Removal of tracheostomy tube":                  '4012607' from E.OMOPSV
code "Ventilating tube removal by another physician": '4195943' from E.OMOPSV

concept "Extubation Procedure": {
  "Extubation of trachea (normal)",
  "Removal of endotracheal tube",
  "Removal of tracheostomy tube",
  "Ventilating tube removal by another physician"
}
