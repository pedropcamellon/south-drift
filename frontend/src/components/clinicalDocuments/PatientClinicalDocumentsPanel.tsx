"use client";

import { useState } from "react";

import {
    ClinicalDocument,
    ClinicalDocumentAttachmentView,
} from "@/types/clinicalDocument";
import { Upload } from "lucide-react";

import { DeleteDocumentDialog } from "@/components/documents/DeleteDocumentDialog";
import { DocumentUploadModal } from "@/components/documents/DocumentUploadModal";
import { DocumentViewerModal } from "@/components/documents/DocumentViewerModal";
import { Button } from "@/components/ui/button";

import { API_ENDPOINTS, apiRequest } from "@/lib/api";

import { usePatientDocuments } from "@/hooks/usePatientDocuments";

import { DocumentList } from "./DocumentList";
import { DocumentSearchInput } from "./DocumentSearchInput";
import { DocumentSortFilterMenu } from "./DocumentSortFilterMenu";

interface PatientClinicalDocumentsPanelProps {
    patientId: string;
}

export function PatientClinicalDocumentsPanel({
    patientId,
}: PatientClinicalDocumentsPanelProps) {
    const {
        documents,
        loading,
        error,
        selectedTypes,
        sortBy,
        searchQuery,
        setSortBy,
        setSearchQuery,
        toggleType,
        clearFilters,
        clearSearch,
        deleteDocument,
        refreshDocuments,
    } = usePatientDocuments(patientId);

    const [uploadModalOpen, setUploadModalOpen] = useState(false);
    const [viewerModalOpen, setViewerModalOpen] = useState(false);
    const [deleteModalOpen, setDeleteModalOpen] = useState(false);
    const [selectedDocument, setSelectedDocument] =
        useState<ClinicalDocumentAttachmentView | null>(null);
    const [documentToDelete, setDocumentToDelete] =
        useState<ClinicalDocument | null>(null);

    const handleUploadSuccess = () => {
        refreshDocuments();
    };

    const handleViewDocument = async (doc: ClinicalDocument) => {
        const attachment = doc.attachments[0];
        if (!attachment) return;

        try {
            const response = await apiRequest(
                API_ENDPOINTS.documentAttachmentDownload(doc.id, attachment.id)
            );

            if (!response.ok) {
                throw new Error("Failed to get document view URL");
            }

            const docWithPresignedUrl = {
                ...doc,
                attachment,
                fileUrl: response.url,
            };
            setSelectedDocument(docWithPresignedUrl);
            setViewerModalOpen(true);
        } catch (err) {
            console.error("Error loading document:", err);
            alert("Failed to load document for viewing");
        }
    };

    const handleDownloadDocument = async (doc: ClinicalDocument) => {
        const attachment = doc.attachments[0];
        if (!attachment) return;

        const response = await apiRequest(
            API_ENDPOINTS.documentAttachmentDownload(doc.id, attachment.id)
        );
        if (!response.ok) {
            throw new Error("Failed to get document download URL");
        }
        window.open(response.url, "_blank");
    };

    const handleDeleteClick = (doc: ClinicalDocument) => {
        setDocumentToDelete(doc);
        setDeleteModalOpen(true);
    };

    const handleDeleteConfirm = async () => {
        if (!documentToDelete) return;

        try {
            await deleteDocument(documentToDelete.id);
        } catch (err) {
            console.error("Failed to delete document:", err);
            alert("Failed to delete document. Please try again.");
        }
    };

    if (loading) return <div>Loading documents...</div>;
    if (error) return <div className="text-red-500">{error}</div>;

    return (
        <div>
            <div className="flex justify-between items-center mb-4">
                <h3 className="font-semibold">Clinical Documents</h3>
                <div className="flex gap-2">
                    <DocumentSearchInput
                        value={searchQuery}
                        onChange={setSearchQuery}
                        onClear={clearSearch}
                    />
                    <DocumentSortFilterMenu
                        sortBy={sortBy}
                        selectedTypes={selectedTypes}
                        onSortChange={setSortBy}
                        onTypeToggle={toggleType}
                        onClearFilters={clearFilters}
                    />
                    <Button onClick={() => setUploadModalOpen(true)} size="sm">
                        <Upload className="w-4 h-4 mr-2" />
                        Upload Document
                    </Button>
                </div>
            </div>

            <DocumentList
                documents={documents}
                onView={handleViewDocument}
                onDownload={handleDownloadDocument}
                onDelete={handleDeleteClick}
            />

            <DocumentUploadModal
                open={uploadModalOpen}
                onClose={() => setUploadModalOpen(false)}
                patientId={patientId}
                onUploadSuccess={handleUploadSuccess}
            />

            {selectedDocument && (
                <DocumentViewerModal
                    document={selectedDocument}
                    open={viewerModalOpen}
                    onClose={() => {
                        setViewerModalOpen(false);
                        setSelectedDocument(null);
                    }}
                />
            )}

            <DeleteDocumentDialog
                document={documentToDelete}
                open={deleteModalOpen}
                onClose={() => {
                    setDeleteModalOpen(false);
                    setDocumentToDelete(null);
                }}
                onConfirm={handleDeleteConfirm}
            />
        </div>
    );
}
