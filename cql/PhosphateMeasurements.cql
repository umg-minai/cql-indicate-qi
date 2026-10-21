// This file has been generated automatically from
// commit ed47895b904941be91a0e959eb4a58af9bb763cc of
// https://github.com/indicate-eu/data-dictionary
// Concept set(s)
// * Phosphate in blood (2 direct entries) [modified 2026-05-27]

// Do not edit

library "PhosphateMeasurements"

include IndicateQiElements called E

code "Phosphate [Mass/volume] in Blood":            '3024232' from E.OMOPSV
code "Phosphate [Mass/volume] in Serum or Plasma":  '3011904' from E.OMOPSV
code "Phosphate [Moles/volume] in Blood":           '3018913' from E.OMOPSV
code "Phosphate [Moles/volume] in Serum or Plasma": '3003458' from E.OMOPSV

concept "Phosphate Measurements": {
  "Phosphate [Mass/volume] in Blood",
  "Phosphate [Mass/volume] in Serum or Plasma",
  "Phosphate [Moles/volume] in Blood",
  "Phosphate [Moles/volume] in Serum or Plasma"
}
