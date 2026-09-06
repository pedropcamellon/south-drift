# ChartReviewBench-v1

`ChartReviewBench-v1` is a committed, synthetic-only benchmark for the
chart-review agent. It evaluates bounded draft-support behavior; it does not
contain real patient data and does not authorize diagnosis, treatment, or
autonomous action.

Each benchmark case has its own folder and a canonical `case.yaml` file:

```text
v1/
	README.md
	<case-id>/
		case.yaml
```

## Case Boundary

A case describes three separate concerns:

- `input.active_review` is the immutable `ChartReviewInput` snapshot initially
  supplied to the agent. It uses the production contract's `timeline`,
  `documents`, `interactions`, and optional `transcript` source grouping.
- `input.history_catalog` holds synthetic `ChartReviewSourceChunk` entries that
  the fake bounded-history tool may return. These entries are not supplied to
  the model unless its one history decision results in their retrieval.
- `expected` contains evaluator assertions. It is never supplied to the model.

The case schema is intentionally chart-review-specific. Shared dataset or
tracking abstractions remain deferred until a second service has a proven
compatible need.

## Expected Assertions

`expected.output` uses atomic assertions instead of a complete expected
`ChartReviewOutput` sentence-for-sentence:

- `summary_facts`: facts the summary must communicate.
- `missing_information`: factual gaps that must remain visible and must not be
  invented away.
- `allowed_source_ids`: exact source IDs supplied to final generation that may
  be cited.
- `forbidden_source_ids`: known invalid citations, including an unsupplied
  content-role variant from the same interaction.
- `confidence`: optional until the confidence rubric is defined by task #40.

`expected.history_decision` evaluates the separate bounded lookup step with
`should_retrieve`, optional required or forbidden `search_terms`, and exact
`expected_returned_source_ids`. A no-retrieval or no-match result is valid when
the active context already has the relevant fact or no approved history block
matches a genuine gap.

`expected.validation.expected_status` states whether the final provider result
is expected to validate against `ChartReviewOutput`.

## Adding Cases

Use synthetic identifiers and source content. Keep source IDs stable and
unique within `active_review`; final citations must use only the source IDs
actually supplied to final generation, not every entry in `history_catalog`.
Add one case only after it can be loaded against the existing chart-review
contracts and can express both acceptable behavior and the failure it guards.
