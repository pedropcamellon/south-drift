export type ClinicalDocumentCategory =
    | "clinical_note"
    | "external_record"
    | "visit_summary"
    | "patient_submission";

export type ClinicalRecordStatus =
    | "preliminary"
    | "final"
    | "amended"
    | "entered_in_error";

export interface Attachment {
    id: string;
    clinicalDocumentId: string;
    storageKey: string;
    fileName: string;
    mimeType: string;
    byteSize: number;
    checksum?: string;
    createdAt: string;
}

export interface ClinicalDocument {
    id: string;
    patientId: string;
    category: ClinicalDocumentCategory;
    status: ClinicalRecordStatus;
    title: string;
    authoredAt?: string;
    receivedAt?: string;
    encounterId?: string;
    createdAt: string;
    attachments: Attachment[];
}

export interface ClinicalDocumentAttachmentView extends ClinicalDocument {
    attachment: Attachment;
    fileUrl: string;
}
