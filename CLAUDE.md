## Pull request reviews

When reviewing a PR:

- Identify the relevant requirements in umg-minai/indicate-qi-definitions
  from references in the PR, commit messages, and linked issues.
- Read the referenced definitions and relevant issue discussion. Use the
  explicitly referenced revision. Do not silently substitute current main.
  If the intended revision cannot be established, report that uncertainty.
- Compare the CQL before and after the change against those requirements.
  Check completeness and semantic equivalence, including populations,
  counting units, numerator, denominator, exclusions, and timing.
- Check CQL correctness, especially interval boundaries, null and
  three-valued logic, units, overlapping events, and duplicate counting.
- Assess whether the changes introduce regressions or undocumented
  interpretations. Explain a concrete example for each suspected mismatch.
- Link findings to both the source requirement and affected CQL.
  Distinguish implementation errors, unclear specifications, and clinical
  questions. Do not claim equivalence where source material is missing.
