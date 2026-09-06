import type { DiagnosticReport } from "./diagnosticReport";
import type { ImagingStudy } from "./imagingStudy";
import type { PatientEncounter } from "./index";

interface PatientTimelineEntryBase {
    id: string;
    patientId: string;
    occurredAt: string;
    title: string;
    status: string;
}

export interface EncounterTimelineEntry extends PatientTimelineEntryBase {
    kind: "encounter";
    encounter: PatientEncounter;
}

export interface DiagnosticReportTimelineEntry extends PatientTimelineEntryBase {
    kind: "diagnostic_report";
    diagnosticReport: DiagnosticReport;
}

export interface ImagingStudyTimelineEntry extends PatientTimelineEntryBase {
    kind: "imaging_study";
    imagingStudy: ImagingStudy;
}

export type PatientTimelineEntry =
    | EncounterTimelineEntry
    | DiagnosticReportTimelineEntry
    | ImagingStudyTimelineEntry;

export interface PatientTimelineResponse {
    entries: PatientTimelineEntry[];
    nextCursor?: string | null;
}
