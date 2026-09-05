# Chart-Review Context Model Redesign

## Problem

`ChartReviewInput` currently combines two different concepts:

- `interaction_id` identifies the single interaction requested for review.
- `interactions` is a plural list, but the backend fills it with summary and
  description chunks from that same requested interaction.

That flattening makes source citation possible, but the model does not make the
agent's initial boundary legible. It is unclear whether an entry is the current
visit, another visit, a laboratory result, or a follow-up decision. It also
encourages treating laboratory and imaging results as current-visit attachments
when they are separately dated patient-history events.

The chart-review agent must begin with one explicitly selected interaction. It
may then make one bounded request to inspect relevant prior patient history.
History can contain visits, results, and follow-ups; it is never supplied as
initial context merely because it belongs to the same patient.

## Target Boundary

The next production contract should express the distinction directly:

```text
one active interaction snapshot
  -> one bounded decision to search prior history
  -> zero to three approved history evidence chunks
  -> one validated draft with exact source citations
```

`ChartReviewInput` should carry an explicit active-interaction snapshot rather
than a generic plural `interactions` list. Its source chunks are limited to
material approved for the interaction under review: for example, its title,
summary, description, and note transcript.

The backend's history boundary should model patient-history events separately.
A history event has its own identifier, event kind, occurrence time, and
citation-ready source chunks. A clinic visit, a later laboratory result, and a
follow-up visit are distinct events even when clinically related.

## Proposed Shapes

These names describe the intended production model; implementation details may
refine them, but must preserve the boundary.

```python
class ChartReviewActiveInteraction(BaseModel):
    interaction_id: str
    source_chunks: list[ChartReviewSourceChunk]


class ChartReviewHistoryEvent(BaseModel):
    event_id: str
    event_kind: ChartReviewHistoryEventKind
    occurred_at: datetime
    source_chunks: list[ChartReviewSourceChunk]


class ChartReviewInput(BaseModel):
    patient_id: str
    active_interaction: ChartReviewActiveInteraction
```

`ChartReviewHistoryEventKind` should distinguish at least a visit, a laboratory
result, and a follow-up event. `ChartReviewSourceChunk` remains the canonical
unit that the model may cite. Its `source_id` identifies a precise supplied
block; `resource_id` refers to the underlying interaction, result, or document.

The history tool must return only the selected source chunks, not unrestricted
event records. The backend retains responsibility for patient scope,
event/source eligibility, active-interaction exclusion, result cap, and exact
provenance.

## Consequences

- A current visit can cite its own summary, description, and transcript without
  implying that prior history was present at generation time.
- A laboratory result remains a distinct dated history event. It can be
  retrieved and cited as a laboratory-result source only when the bounded
  history search returns it.
- A follow-up may cite a prior visit or lab result through exact returned source
  IDs, while the resulting draft remains review support rather than a diagnosis
  or test recommendation.
- The benchmark can model a realistic patient history: a clinic visit, a later
  lab result, and a later follow-up under review, with explicit assertions about
  whether history should have been requested.

## Migration Direction

This is a deliberate breaking production-contract change. Do not add aliases,
fallback parsing, or compatibility branches for the ambiguous
`interaction_id`/`interactions` shape. Update all producers, worker payloads,
persisted development fixtures, tests, and chart-review prompts together, then
resume benchmark authoring against the new boundary.

## Out of Scope

- Unrestricted chart retrieval or more than one history lookup.
- Diagnosis, treatment decisions, or autonomous test recommendations.
- A general EHR event model or a universal AIOps dataset schema.
