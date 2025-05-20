// Name     04 - glucose control
// Version  1.0
//
// Source
//  https://semicyuc.org/wp-content/uploads/2018/10/2017_qualityindicators_eng.pdf
// Description
// SEMICYUC indicator 55
//  Indicator       MAINTAINING APPROPRIATE BLOOD GLUCOSE LEVELS
//  Dimension       Effectiveness, safety
//  Justification   Hyperglycemia in critical patients has been associated with
//      increased infectious complications, morbidity, and mortality. However,
//      strict glucose control with perfused insulin to maintain levels between
//      80 and 110 mg/dL has had a contradictory effect on mortality due to
//      a high incidence of severe hypoglycemia. Current guidelines recommend
//      aiming to maintain glucose below 150 mg/dl with insulin, avoiding
//      strict glucose- control protocols aiming for (80-110 mg/dL).
//      Continuous insulin perfusion protocols should avoid variability in
//      glucose levels.
//  Formula
//      (no of patients with glucose > 150 mg/dL treated with insulin) /
//          (no of patients with glucose > 150 mg/dL)
//  Explanation of terms
//      Indication for insulin treatment: all critical patients with
//      glucose > 150 mg/dl in 2 consecutive determinations.
//  Population      All patients admitted to the intensive care unit during
//      the period reviewed.
//  Standard        80%

library "IndicateQi04GlucoseControl" version '1.0.0'

using OMOP version 'v5.4'

include IndicateQiElements called E

define GlucoseLevel:
    [Measurement: E."Glucose"]
