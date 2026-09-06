export type DiagnosticReportStatus =
    | "registered"
    | "partial"
    | "final"
    | "amended"
    | "cancelled";

export type ObservationStatus =
    | "registered"
    | "preliminary"
    | "final"
    | "amended"
    | "cancelled";

export type ObservationValueType = "quantity" | "text" | "code" | "boolean";

export interface ClinicalProvenanceInput {
    sourceSystem?: string | null;
    externalId?: string | null;
    authoredAt?: string | null;
    receivedAt?: string | null;
    recordedAt?: string | null;
    authorId?: string | null;
    recorderId?: string | null;
    version?: string | null;
}

export interface DiagnosticReportCreate {
    patientId: string;
    status: DiagnosticReportStatus;
    title: string;
    effectiveAt?: string | null;
    issuedAt?: string | null;
    receivedAt?: string | null;
    conclusion?: string | null;
    originatingEncounterId?: string | null;
    provenance?: ClinicalProvenanceInput | null;
}

export interface ObservationCreate {
    patientId: string;
    status: ObservationStatus;
    code: string;
    display: string;
    valueType: ObservationValueType;
    value?: string | null;
    unit?: string | null;
    dataAbsentReason?: string | null;
    effectiveAt?: string | null;
    provenance?: ClinicalProvenanceInput | null;
}

export interface DiagnosticReportBundleCreate {
    report: DiagnosticReportCreate;
    observations: ObservationCreate[];
}

export interface Observation extends ObservationCreate {
    id: string;
    diagnosticReportId: string;
    createdAt: string;
}

export interface DiagnosticReport extends DiagnosticReportCreate {
    id: string;
    createdAt: string;
    observations: Observation[];
}
