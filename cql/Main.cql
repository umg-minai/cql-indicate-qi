library "Main" version '0.0.0'

using OMOP version 'v5.4'

include OMOPFunctions

include "IndicateQi01Ventilation"              called "Qi01"
include "IndicateQi02Weaning"                  called "Qi02"
include "IndicateQi03Feeding"                  called "Qi03"
include "IndicateQi04GlucoseControl"           called "Qi04"
include "IndicateQi05ThromboembolicPrevention" called "Qi05"
include "IndicateQi06InfectionRate"            called "Qi06"
include "IndicateQi07PainSedationDelir"        called "Qi07"
include "IndicateQi08AdvanceCarePlan"          called "Qi08"
include "IndicateQi09Mobilisation"             called "Qi09"

define NoMatchingConcept: OMOPFunctions.SC(0)

define function ToObservation(
    indicatorConceptId Integer,
    result             Tuple{
                         patient      OMOP.Person,
                         reviewPeriod Interval<DateTime>,
                         periods      List<Tuple{
                                        period      Interval<DateTime>,
                                        numerator   Decimal,
                                        denominator Integer,
                                        qi          Decimal
                                      }>
                       }
  ):
  if Exists((result.periods) p where p.qi is not null) then
    (result.periods) p
      //where p.qi is not null
      return all OMOP.Observation{
        observationConceptId:   indicatorConceptId,
        observationTypeConcept: NoMatchingConcept,
        observationDatetime:    start of p.period,
        observationDate:        date from start of p.period,
        person:                 result.patient,
        valueAsNumber:          p.qi
      }
  else
    {}

define function ToDebugObservation(baseConceptId Integer,
                                   periods       List<Tuple{
                                                   period Interval<DateTime>,
                                                   values List<Decimal>
                                                 }>):
  Flatten(
    (periods) p
      return all
        (
          (p.values) v aggregate r starting ({o: {}, i: 1}):
            {
              o: Flatten({
                   r.o,
                   {
                     OMOP.Observation{
                       observationConceptId:   baseConceptId + r.i,
                       observationTypeConcept: NoMatchingConcept,
                       observationDatetime:    start of p.period,
                       observationDate:        date from start of p.period,
                       person:                 null, // result.patient.personId,
                       valueAsNumber:          v
                     }
                   }
                 }),
              i: r.i + 1
            }
        ).o
  )

context Patient

define Results:
  Flatten({
    ToObservation(2000100101, "Qi01".Result),
    ToObservation(2000100102, "Qi02".Result),
    ToObservation(2000100103, "Qi03".Result),
    ToObservation(2000100104, "Qi04".Result),
    ToObservation(2000100105, "Qi05".Result),
    ToObservation(2000100106, "Qi06".Result),
    ToObservation(2000100107, "Qi07".Result),
    ToObservation(2000100108, "Qi08".Result),
    ToObservation(2000100109, "Qi09".Result),

    ToDebugObservation(2000101000, "Qi01"."Debug Results"),
    ToDebugObservation(2000102000, "Qi02"."Debug Results"),
    ToDebugObservation(2000103000, "Qi03"."Debug Results"),
    ToDebugObservation(2000106000, "Qi06"."Debug Results"),
    ToDebugObservation(2000107000, "Qi07"."Debug Results")
  })
