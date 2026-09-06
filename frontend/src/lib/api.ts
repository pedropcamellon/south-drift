/**
 * Central API configuration for FastAPI backend
 * Direct calls to FastAPI (no BFF middleware)
 */
import { getAuthToken } from "./auth-api";

export const FASTAPI_BASE_URL = process.env.NEXT_PUBLIC_API_URL;

/**
 * API endpoints configuration
 */
export const API_ENDPOINTS = {
    // Health
    health: `${FASTAPI_BASE_URL}/health`,

    // Auth
    authRegister: `${FASTAPI_BASE_URL}/auth/register`,
    authLogin: `${FASTAPI_BASE_URL}/auth/jwt/login`,
    authLogout: `${FASTAPI_BASE_URL}/auth/jwt/logout`,
    usersMe: `${FASTAPI_BASE_URL}/users/me`,

    // Patients
    patients: `${FASTAPI_BASE_URL}/api/v1/patients/`,
    patient: (id: string) => `${FASTAPI_BASE_URL}/api/v1/patients/${id}`,
    patientTimeline: (id: string) =>
        `${FASTAPI_BASE_URL}/api/v1/patients/${id}/timeline`,

    // Encounters
    encounters: `${FASTAPI_BASE_URL}/api/v1/encounters`,
    encounter: (id: string) => `${FASTAPI_BASE_URL}/api/v1/encounters/${id}`,
    encountersByPatient: (patientId: string) =>
        `${FASTAPI_BASE_URL}/api/v1/encounters/?patientId=${patientId}`,
    encounterNote: (id: string) =>
        `${FASTAPI_BASE_URL}/api/v1/encounters/${id}/note`,
    encounterSummary: (id: string) =>
        `${FASTAPI_BASE_URL}/api/v1/encounters/${id}/summary`,
    encounterVoiceNoteStatus: (id: string) =>
        `${FASTAPI_BASE_URL}/api/v1/encounters/${id}/voice-note-status`,
    encounterChartReview: (id: string) =>
        `${FASTAPI_BASE_URL}/api/v1/encounters/${id}/chart-review`,

    // Clinical Documents
    documents: `${FASTAPI_BASE_URL}/api/v1/clinical-documents`,
    document: (id: string) =>
        `${FASTAPI_BASE_URL}/api/v1/clinical-documents/${id}`,
    documentsByPatient: (patientId: string) =>
        `${FASTAPI_BASE_URL}/api/v1/clinical-documents/?patientId=${patientId}`,
    documentUpload: `${FASTAPI_BASE_URL}/api/v1/clinical-documents/upload`,
    documentAttachmentDownload: (documentId: string, attachmentId: string) =>
        `${FASTAPI_BASE_URL}/api/v1/clinical-documents/${documentId}/attachments/${attachmentId}/download`,

    // Diagnostic Reports
    diagnosticReports: `${FASTAPI_BASE_URL}/api/v1/diagnostic-reports/`,
    diagnosticReport: (id: string) =>
        `${FASTAPI_BASE_URL}/api/v1/diagnostic-reports/${id}`,
    diagnosticReportsByPatient: (patientId: string) =>
        `${FASTAPI_BASE_URL}/api/v1/diagnostic-reports/?patientId=${patientId}`,

    // Imaging Studies
    imagingStudies: `${FASTAPI_BASE_URL}/api/v1/imaging-studies/`,
    imagingStudy: (id: string) =>
        `${FASTAPI_BASE_URL}/api/v1/imaging-studies/${id}`,
    imagingStudiesByPatient: (patientId: string) =>
        `${FASTAPI_BASE_URL}/api/v1/imaging-studies/?patientId=${patientId}`,

    // Summarization
    summarize: `${FASTAPI_BASE_URL}/api/v1/summarization`,
    summarizationHealth: `${FASTAPI_BASE_URL}/api/v1/summarization/health`,
} as const;

/**
 * @deprecated Use apiJson for JSON responses or apiRequest for raw responses.
 */
export const fetcher = async <T = unknown>(url: string): Promise<T> => {
    if (typeof window !== "undefined") {
        console.warn(
            "Deprecated: fetcher() is kept for compatibility. Use apiJson() for JSON reads or apiRequest() for raw responses."
        );
    }

    return apiJson<T>(url);
};

/**
 * Authenticated API request that returns the raw Response.
 */
export async function apiRequest(
    url: string,
    init: RequestInit = {}
): Promise<Response> {
    const token = getAuthToken();
    const headers = new Headers(init.headers);

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    const res = await fetch(url, {
        ...init,
        headers,
    });

    await handleUnauthorized(res);

    return res;
}

/**
 * Authenticated API request that parses and returns JSON.
 */
export async function apiJson<T = unknown>(
    url: string,
    init: RequestInit = {}
): Promise<T> {
    const res = await apiRequest(url, init);

    if (!res.ok) {
        const error = new Error("API request failed");
        throw error;
    }

    return res.json();
}

async function handleUnauthorized(response: Response): Promise<void> {
    if (response.status === 401 && typeof window !== "undefined") {
        const { clearAuthToken } = await import("./auth-api");
        clearAuthToken();
        window.location.href = "/login";
    }
}
