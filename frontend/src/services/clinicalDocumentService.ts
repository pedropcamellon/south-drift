import {
    ClinicalDocument,
    ClinicalDocumentCategory,
} from "@/types/clinicalDocument";

import { API_ENDPOINTS, apiJson, apiRequest } from "@/lib/api";
import { getAuthToken } from "@/lib/auth-api";

export async function listClinicalDocuments(
    patientId: string
): Promise<ClinicalDocument[]> {
    const url = API_ENDPOINTS.documentsByPatient(patientId);
    return apiJson<ClinicalDocument[]>(url);
}

export async function getClinicalDocument(
    id: string
): Promise<ClinicalDocument> {
    return apiJson<ClinicalDocument>(API_ENDPOINTS.document(id));
}

export async function deleteClinicalDocument(id: string): Promise<void> {
    const res = await apiRequest(API_ENDPOINTS.document(id), {
        method: "DELETE",
    });
    if (!res.ok) throw new Error("Failed to delete document");
}

export interface UploadDocumentParams {
    file: File;
    patientId: string;
    category: ClinicalDocumentCategory;
    title: string;
    onProgress?: (progress: number) => void;
}

export async function uploadDocument(
    params: UploadDocumentParams
): Promise<ClinicalDocument> {
    const { file, patientId, category, title, onProgress } = params;

    const formData = new FormData();
    formData.append("file", file);
    formData.append("patientId", patientId);
    formData.append("category", category);
    formData.append("title", title);

    return new Promise((resolve, reject) => {
        const xhr = new XMLHttpRequest();
        const token = getAuthToken();

        // Track upload progress
        xhr.upload.onprogress = (e) => {
            if (e.lengthComputable && onProgress) {
                const progress = Math.round((e.loaded / e.total) * 100);
                onProgress(progress);
            }
        };

        // Handle successful response
        xhr.onload = () => {
            if (xhr.status >= 200 && xhr.status < 300) {
                try {
                    const response = JSON.parse(xhr.responseText);
                    resolve(response);
                } catch (error) {
                    reject(new Error("Failed to parse response"));
                }
            } else {
                reject(new Error(`Upload failed with status ${xhr.status}`));
            }
        };

        // Handle errors
        xhr.onerror = () => reject(new Error("Network error during upload"));
        xhr.onabort = () => reject(new Error("Upload aborted"));

        // Send request
        xhr.open("POST", API_ENDPOINTS.documentUpload);
        if (token) {
            xhr.setRequestHeader("Authorization", `Bearer ${token}`);
        }
        xhr.send(formData);
    });
}
