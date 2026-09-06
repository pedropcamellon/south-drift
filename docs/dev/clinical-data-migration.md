# Clinical Data Migration

## Scope

This is the one-time replacement of Folium's starter clinical records with
patient-owned native records. There are no production users or external data
consumers, so this procedure does not provide compatibility routes, aliases, or
an in-place legacy-data upgrade.

## Retired Field Mapping

| Retired record                                            | Retired field group                                                                          | Native destination                               | Decision                                                                                  |
| --------------------------------------------------------- | -------------------------------------------------------------------------------------------- | ------------------------------------------------ | ----------------------------------------------------------------------------------------- |
| `Interaction`                                             | patient, title, type, purpose, status, start/end time, clinician, description                | `Encounter`                                      | Preserve as the patient-owned clinical contact.                                           |
| `Interaction`                                             | raw note and transcript                                                                      | `EncounterNarrative`                             | Persist separately from the encounter.                                                    |
| `Interaction`                                             | summary, structured summary, complaint, assessment, treatment plan, compliance, audit fields | `Encounter`                                      | Preserve as typed encounter workflow fields.                                              |
| `Interaction`                                             | audio reference and workflow metadata                                                        | `Encounter.audio_metadata`                       | Preserve only as encounter-associated capture state.                                      |
| `Interaction` lab-work category                           | result title, event time, conclusion, measured values                                        | `DiagnosticReport` plus owned `Observation` rows | Replace with structured, independently dated results.                                     |
| `Interaction` vaccination, medication, surgery categories | category-specific data                                                                       | `Immunization`, `Medication`, or `Procedure`     | Replace only when a native write workflow is approved; do not overload encounter purpose. |
| Legacy `Document`                                         | clinical title, category, status, author/receipt time, encounter context                     | `ClinicalDocument`                               | Preserve as a patient-owned clinical record.                                              |
| Legacy `Document`                                         | storage key, file name, MIME type, byte size, checksum                                       | `Attachment`                                     | Preserve as document-owned stored payload metadata.                                       |

## Development Reset And Verification

Use this only for synthetic local development data. It deletes all patients and
database-cascaded patient-owned clinical records, retains local users, and then
recreates the approved seed cohort.

```bash
docker compose exec folium-backend python -m app.clear_data
docker compose exec folium-backend python -m app.seed_db
docker compose exec folium-backend pytest tests
```

Verify that three synthetic patients exist and that each has a DiagnosticReport
followed by a later Encounter. Confirm the patient timeline returns `encounter`,
`diagnostic_report`, and, where seeded, `imaging_study` entries. A destructive
reset has no rollback beyond restoring the known synthetic seed cohort by rerunning
the second command.

## Stale Schema Recreation

Use this only when the local database schema predates a native model change.
Unlike the patient-data reset above, this removes all local tables, including
users and workflow records. The backend recreates and seeds the approved local
schema when it starts.

```bash
docker compose stop folium-backend folium-chartreview-worker folium-voicenotes-worker
docker compose exec -T folium-postgres psql -v ON_ERROR_STOP=1 -U folium -d folium_db \
	-c 'DROP SCHEMA public CASCADE; CREATE SCHEMA public;'
docker compose up --detach --wait folium-backend
docker compose exec -T folium-backend python -m app.seed_db
docker compose exec -T folium-backend pytest tests
```

## Migration Rule

Future schema changes require either a forward Alembic migration with an explicit
rollback or a replacement decision that updates this reset procedure before code
merges. Do not reintroduce retired `Interaction` or legacy `Document` contracts.
