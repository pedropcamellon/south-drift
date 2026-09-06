export type ImagingModality = "xray" | "ct" | "mri" | "ultrasound";

export interface ImagingStudyCreate {
    patientId: string;
    modality: ImagingModality;
    performedAt: string;
    externalStudyId?: string | null;
    originatingEncounterId?: string | null;
    clinicalDocumentId?: string | null;
    diagnosticReportId?: string | null;
}

export interface ImagingStudy extends ImagingStudyCreate {
    id: string;
    createdAt: string;
}
