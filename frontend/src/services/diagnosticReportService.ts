import type {
    DiagnosticReport,
    DiagnosticReportBundleCreate,
} from "@/types/diagnosticReport";

import { API_ENDPOINTS, apiJson } from "@/lib/api";

export async function createDiagnosticReport(
    bundle: DiagnosticReportBundleCreate
): Promise<DiagnosticReport> {
    return apiJson<DiagnosticReport>(API_ENDPOINTS.diagnosticReports, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(bundle),
    });
}

export async function getDiagnosticReport(
    id: string
): Promise<DiagnosticReport> {
    return apiJson<DiagnosticReport>(API_ENDPOINTS.diagnosticReport(id));
}

export async function getDiagnosticReportsByPatient(
    patientId: string
): Promise<DiagnosticReport[]> {
    return apiJson<DiagnosticReport[]>(
        API_ENDPOINTS.diagnosticReportsByPatient(patientId)
    );
}
