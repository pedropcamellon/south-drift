import type { ChartReviewStatus } from "@/constants/chartReview";

// Shared TypeScript definitions

// ============== PORTFOLIO TYPES ==============
export interface User {
    id: string;
    email: string;
    firstName: string;
    lastName: string;
    createdAt: Date;
    updatedAt: Date;
}

// ============== API TYPES ==============
export interface ApiResponse<T> {
    data: T;
    success: boolean;
    message?: string;
}

// ============== CLINICAL TYPES ==============
export interface ClinicalSummary {
    // Define as needed
}

export interface MedicalImage {
    // Define as needed
}

export interface Patient {
    id: string;
    medicalRecordNumber: string;
    firstName: string;
    lastName: string;
    dateOfBirth: string; // ISO string
    gender: string;
    contactInfo: string;
    medicalImages: MedicalImage[];
    clinicalSummaries: ClinicalSummary[];
}

export type EncounterType =
    | "outpatient"
    | "telehealth"
    | "telephone"
    | "portal"
    | "emergency"
    | "inpatient";

export type EncounterPurpose =
    | "initial"
    | "follow_up"
    | "preventive"
    | "procedure";
export type EncounterStatus =
    | "planned"
    | "in_progress"
    | "completed"
    | "cancelled";

export interface EncounterNarrative {
    id: string;
    patientId: string;
    encounterId: string;
    content: string;
    status: "preliminary" | "final" | "amended" | "entered_in_error";
    createdAt: string;
}

export interface PatientEncounter {
    id: string;
    createdAt: string;
    createdBy: string;
    description?: string | null;
    startedAt: string;
    endedAt?: string | null;
    isCompliant: boolean;
    location?: string | null;
    note?: string | null;
    summary?: string | null;
    structuredSummary?: StructuredSummary;
    chiefComplaint?: string;
    clinicalAssessment?: string;
    treatmentPlan?: string;
    patientId: string;
    clinicianId?: string | null;
    clinicianName?: string | null;
    title: string;
    encounterType: EncounterType;
    purpose: EncounterPurpose;
    status: EncounterStatus;
    audioMetadata?: EncounterAudioMetadata | null;
    narratives: EncounterNarrative[];
    updatedAt?: string | null;
    updatedBy?: string | null;
}

export enum VoiceNoteWorkflowStatus {
    IDLE = "idle",
    PROCESSING = "processing",
    TRANSCRIBED = "transcribed",
    COMPLETED = "completed",
    PARTIAL = "partial",
    FAILED = "failed",
}

export interface VoiceNoteWorkflowMetadata {
    workflowId?: string | null;
    runId?: string | null;
    status?: VoiceNoteWorkflowStatus | null;
    failureStage?: string | null;
    errorMessage?: string | null;
    updatedAt?: string | null;
    transcriptAppliedAt?: string | null;
}

export interface EncounterAudioMetadata {
    filename?: string | null;
    storageKey?: string | null;
    storageUrl?: string | null;
    size?: number | null;
    contentType?: string | null;
    transcriptionStatus?: VoiceNoteWorkflowStatus | null;
    voiceNoteWorkflow?: VoiceNoteWorkflowMetadata | null;
}

export interface VoiceNoteWorkflowStatusResponse {
    encounterId: string;
    workflowId?: string;
    runId?: string;
    status: VoiceNoteWorkflowStatus;
    failureStage?: string | null;
    errorMessage?: string | null;
    encounter?: PatientEncounter;
}

export type { ChartReviewStatus };
export type ChartReviewConfidence = "low" | "medium" | "high";

export interface ChartReviewSourceRef {
    sourceType: "timeline" | "document" | "encounter" | "transcript";
    resourceId?: string | null;
    displayLabel?: string | null;
    contentRole?: string | null;
    occurredAt?: string | null;
}

export interface ChartReview {
    id: string;
    encounterId: string;
    status: ChartReviewStatus;
    summary?: string | null;
    reasoning?: string | null;
    missingInfo: string[];
    followUpQuestions: string[];
    sourceRefs: ChartReviewSourceRef[];
    confidence?: ChartReviewConfidence | null;
    reviewFlags: string[];
    failureMessage?: string | null;
}

// ============== SUMMARIZATION TYPES ==============
export interface StructuredSummary {
    chief_complaint: string;
    subjective: string;
    objective: string;
    assessment: string;
    plan: string;
    clinical_tags: string[];
    icd_codes: string[];
    action_items: string[];
}

export interface SummarizationRequest {
    transcript: string;
    format?: "soap" | "narrative";
    encounter_type?: string;
    language?: string;
}

export interface SummarizationResponse {
    summary: string;
    structured_data: StructuredSummary;
    processing_time: number;
    model_used: string;
    provider: string;
    usage: {
        prompt_tokens: number;
        completion_tokens: number;
        total_tokens: number;
    };
}

export interface SummarizationHealthResponse {
    status: string;
    service_url: string;
    message?: string;
}
