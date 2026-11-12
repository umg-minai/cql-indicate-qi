## Pull request reviews

### Verify requirements and implementation

- Identify the relevant requirements in umg-minai/indicate-qi-definitions
  from references in the PR, commit messages, and linked issues.
- Read the referenced definitions and relevant issue discussion. Use the
  explicitly referenced revision. Do not silently substitute current main.
  If the intended revision cannot be established, report that uncertainty.
- Follow relevant earlier PR conversations, inline review threads, and issue
  discussions for the changed QIs and shared functions. Read resolutions and
  their rationale. Treat accepted decisions as context, not every suggestion
  or previous AI review as an agreed requirement. Revisit a settled decision
  only with a specific new reason, and link the discussion being reconsidered.
- Compare the CQL before and after the change against those requirements.
  Check completeness and semantic equivalence, including populations,
  counting units, numerator, denominator, exclusions, and timing.
- Check CQL correctness, especially interval boundaries, null and
  three-valued logic, units, overlapping events, and duplicate counting.
- Read explanatory comments in the changed CQL, affected helpers, and relevant
  call sites. They may document deliberate exceptions, assumptions, or design
  decisions. Check that rationale against both the implementation and the
  referenced definition before proposing a change. If it is contradicted or
  outdated, explain the conflict and whether the code, comment, or specification
  needs correction; a comment alone does not prove correctness.
- Assess whether the changes introduce regressions or undocumented
  interpretations. Explain a concrete example for each suspected mismatch.
- Separate newly introduced or worsened issues from unrelated existing defects.
  Distinguish implementation errors, unclear specifications, and clinical
  questions. Do not claim equivalence where source material is missing.

### Make every comment a clear change request

- Lead with what the author should correct or clarify. Exclude descriptions
  of behavior that is already correct, positive confirmations, successful
  checks, harmless refactors, and general summaries of the diff.
- Use a short imperative title followed by the failing behavior, its practical
  consequence, and the required correction. Keep the explanation compact;
  include an input or timing example only when it demonstrates the defect.
- Report only observations that identify a necessary correction or clarification. 
  State explicitly what needs to change and why. Omit descriptions of correct or 
  intended behavior. If the PR was meant to change selection, identify the unmet 
  requirement, show why the current CQL still fails it, and request the necessary 
  correction explicitly.
- Link each finding to the affected CQL lines at the reviewed commit and to
  the precise definition, issue comment, or earlier PR decision it relies on.
  Use absolute GitHub URLs, descriptive labels, full commit SHAs for code, and
  line anchors where available. Use real comment/thread permalinks for
  discussions; do not fabricate references or substitute an unrelated source.
- If evidence is unavailable, request a source or decision in the main review
  only when it is necessary to assess or correct the implementation. Put other
  access or verification limitations in the context footer.
- Avoid duplicate findings across inline comments and the summary. Link the
  inline finding from a short summary when useful. With no actionable finding,
  post a brief completion statement without enumerating correct behavior.

### Finish with verification context

- Put a compact, collapsed `<details>` block titled `Review context` at the
  end of the summary. Record the reviewed CQL commit, definition revisions,
  supplementary sources, and material verification limitations there. Omit
  empty sections. Keep evidence essential to a change request next to that
  finding, but do not put an audit trail or a coverage checklist before it.
