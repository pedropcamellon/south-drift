# Clinical Data Model

## Status

Active architecture decision for the clinical-model migration. It describes
developer contracts, not supported end-user workflows.

## Decision

Folium adopts the mature-model separation used by OpenEMR and CARLOS: a clinical
contact, an administered immunization, an active medication, a performed
procedure, a diagnostic result, a document, and a note are distinct clinical
records. They may be related, but one must not be represented as an overloaded
subtype or free-text field of another.

Folium owns its typed schema and API contracts. This is not an adoption of either
upstream schema, and it does not add FHIR persistence or FHIR APIs.

## Core Conventions

- Every clinical root is patient-owned with a required typed `patient_id`.
- Independently dated records remain independently dated even when they were
  produced during an encounter.
- Encounter context is an optional typed foreign key on a record that can occur
  independently of the encounter.
- A patient-history timeline is a backend read projection over typed source
  records. It is not a mutable catch-all `ClinicalEvent` table.
- Detail and action APIs operate on the authoritative source record, not on a
  timeline row.
- Cross-resource relationships are named and typed. Do not use a polymorphic
  `owner_type`/`owner_id` escape hatch.

## Encounter

An `Encounter` is Folium's patient-owned record of one bounded clinical contact
or care episode. It records who was involved, what kind of contact occurred,
its clinical purpose and workflow status, when it began and ended, and the
clinician, location, and encounter-level draft-support fields needed to operate
that contact.

An Encounter is used for an outpatient visit, telehealth or telephone contact,
portal encounter, emergency contact, or inpatient stay. An inpatient admission
and discharge are the start and end lifecycle boundaries of one Encounter, not
independent record types.

An Encounter is not a container for every clinical fact recorded during it:

- Raw notes and transcripts are `EncounterNarrative` records owned by the
  Encounter.
- Audio capture and generated draft summary state are encounter workflow data.
- A diagnostic result, imaging study, clinical document, immunization,
  medication, or procedure remains its own patient-owned record, even when it
  carries an optional originating Encounter reference.
- `prior_encounter_id` links a same-patient preceding contact for continuity; it
  does not establish timeline order or replace independently dated records.

Every Encounter requires a patient, type, purpose, status, title, and start
time. Its end time is optional, but when present cannot precede the start time.
The patient-history timeline renders an Encounter as one dated contact entry;
detail and action APIs operate on the Encounter and its owned narratives rather
than on a generic timeline event.

## Clinical Records

| Record                               | Purpose                                                                                                            | Timeline behavior                                                                                              | Encounter relationship          |
| ------------------------------------ | ------------------------------------------------------------------------------------------------------------------ | -------------------------------------------------------------------------------------------------------------- | ------------------------------- |
| `Encounter`                          | A clinical contact: in-person visit, telehealth, telephone, portal, emergency, or inpatient stay.                  | One dated contact entry.                                                                                       | It is the contextual record.    |
| `EncounterNarrative`                 | Raw narrative captured for an encounter, including a transcription.                                                | Renders through its encounter; not a separate clinical event.                                                  | Required.                       |
| `Immunization`                       | A vaccine administration with administration time, vaccine identity, manufacturer, lot, performer, and status.     | One dated administration entry.                                                                                | Optional originating encounter. |
| `Medication`                         | A longitudinal medication record with status and prescribed/recorded times.                                        | Timeline entries reflect explicit medication lifecycle events, not every active medication on every page load. | Optional originating encounter. |
| `Procedure`                          | A performed clinical procedure, including surgery, with performed time, status, performer, and structured details. | One dated procedure entry.                                                                                     | Optional originating encounter. |
| `DiagnosticReport` and `Observation` | A report-level result with report-owned atomic values.                                                             | The report is the timeline entry; observations render in its detail.                                           | Optional originating encounter. |
| `ClinicalDocument` and `Attachment`  | A clinical record and its stored payload.                                                                          | A document may be a dated timeline entry when clinically meaningful.                                           | Optional originating encounter. |
| `ImagingStudy`                       | Independently dated imaging metadata.                                                                              | One dated imaging entry.                                                                                       | Optional originating encounter. |

OpenEMR keeps patient immunizations, medication data, procedure orders/results,
encounters, and notes in separate persistence surfaces. CARLOS likewise exposes
separate medication, immunization/prevention, procedure, encounter, and note
modules. Folium follows that division at its own smaller scope.

## Relationship Map

The following relationships are the developer contract. The left side owns the
right side where the relationship is marked required; optional links provide
clinical context without changing the target record's independent identity.

| Relationship                                                  | Cardinality               | Meaning and lifecycle                                                                                                  |
| ------------------------------------------------------------- | ------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| `Patient -> Encounter`                                        | one to many, required     | Every encounter has one patient owner. Deleting a patient removes its encounters.                                      |
| `Encounter -> EncounterNarrative`                             | one to many, required     | A narrative belongs to one encounter and the same patient; deleting an encounter removes its narratives.               |
| `Encounter -> prior Encounter`                                | zero or one, same patient | Provides clinical continuity only. It does not replace chronological ordering.                                         |
| `ClinicalDocument -> Attachment`                              | one to many, required     | Attachments are document-owned storage payloads and are deleted with the document.                                     |
| `DiagnosticReport -> Observation`                             | one to many, required     | Observations belong to one report and share its patient ownership.                                                     |
| `ImagingStudy -> Encounter/ClinicalDocument/DiagnosticReport` | optional typed links      | An imaging study remains independently patient-owned; links provide originating context or associated source material. |
| `Immunization`, `Medication`, or `Procedure -> Encounter`     | optional typed link       | The activity remains independently patient-owned and clinically dated.                                                 |

The patient-history projection reads these source records and orders them for
display. It does not own them, rewrite their relationships, or become another
clinical persistence model.

## Encounter Lifecycle And Follow-Up

An admission and discharge are lifecycle boundaries of one `inpatient`
Encounter, represented by its start/end times and status. They are not separate
clinical-resource types.

A call after a flu immunization is a new `telephone` Encounter. The eventual
typed relationship to the Immunization captures the clinical context; the
symptom must not exist solely in free text on the immunization. A later explicit
adverse-event model can represent that clinical fact if Folium needs it.

## Narratives And Voice Capture

Voice recording and transcription are capture material for the Encounter that
produced them. They are not standalone timeline roots. During the current
migration, manual edits and asynchronous transcription updates modify the
current `EncounterNarrative` in place after patient/encounter ownership
validation, while recording the responsible actor and update time.

This is an interim workflow compatibility decision. The follow-up hardening
design is workflow-owned editable drafts followed by immutable final narratives
and append-only amendments with a visible supersession chain.

## Current Implementation Boundary

The initial typed-activity proof is implemented in the backend contract and ORM
layers:

- `Immunization` has required patient ownership, an optional originating
  encounter, administration time, vaccine identity, manufacturer, lot, performer,
  status, and recorded time.
- `Medication` has required patient ownership, an optional originating encounter,
  medication identity, dosage text, lifecycle status, prescribed/start/end times,
  and recorded time. Its end time cannot precede its start time.
- `Procedure` has required patient ownership, an optional originating encounter,
  procedure identity, performed time, performer, structured details, status, and
  recorded time.

The active Encounter workflow, report/document APIs, synthetic seed cohort, and
patient-history projection use the native records. Typed activity write workflows
remain intentionally deferred until a user-facing need approves them.

## Deferred Scope

- FHIR resource compatibility, APIs, profiles, terminology bindings, and
  import/export behavior.
- Broad medication-management capabilities such as prescribing, reconciliation,
  dispensing, and interaction checking.
- Scheduling, billing, and clinical decision support.
- A generic cross-resource link table or polymorphic attachment ownership.
