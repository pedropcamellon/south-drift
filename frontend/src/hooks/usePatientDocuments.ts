import { useEffect, useMemo, useState } from "react";

import {
    ClinicalDocument,
    ClinicalDocumentCategory,
} from "@/types/clinicalDocument";
import { CommonListSortOption } from "@/types/sort";

import {
    deleteClinicalDocument,
    listClinicalDocuments,
} from "@/services/clinicalDocumentService";

export function usePatientDocuments(patientId: string) {
    const [documents, setDocuments] = useState<ClinicalDocument[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedTypes, setSelectedTypes] = useState<
        ClinicalDocumentCategory[]
    >([]);
    const [sortBy, setSortBy] =
        useState<CommonListSortOption>("createdAt-desc");
    const [searchQuery, setSearchQuery] = useState("");

    const sortDocuments = (
        docs: ClinicalDocument[],
        sortOption: CommonListSortOption
    ): ClinicalDocument[] => {
        return [...docs].sort((a, b) => {
            if (sortOption === "createdAt-desc") {
                return (
                    new Date(b.createdAt).getTime() -
                    new Date(a.createdAt).getTime()
                );
            } else if (sortOption === "createdAt-asc") {
                return (
                    new Date(a.createdAt).getTime() -
                    new Date(b.createdAt).getTime()
                );
            } else if (sortOption === "title-asc") {
                return a.title.localeCompare(b.title);
            }
            return 0;
        });
    };

    const fetchDocuments = () => {
        setLoading(true);
        setError(null);
        listClinicalDocuments(patientId)
            .then((docs) => {
                const sorted = sortDocuments(docs, sortBy);
                setDocuments(sorted);
            })
            .catch((e) => setError(e.message))
            .finally(() => setLoading(false));
    };

    const deleteDocument = async (documentId: string): Promise<void> => {
        await deleteClinicalDocument(documentId);
        fetchDocuments();
    };

    const toggleType = (type: ClinicalDocumentCategory) => {
        setSelectedTypes((prev) =>
            prev.includes(type)
                ? prev.filter((t) => t !== type)
                : [...prev, type]
        );
    };

    const clearFilters = () => {
        setSelectedTypes([]);
    };

    const clearSearch = () => {
        setSearchQuery("");
    };

    // Client-side search filtering
    const filteredDocuments = useMemo(() => {
        if (!searchQuery.trim()) return documents;

        const query = searchQuery.toLowerCase();
        return documents.filter((doc) => {
            return (
                doc.title.toLowerCase().includes(query) ||
                doc.attachments.some((attachment) =>
                    attachment.fileName.toLowerCase().includes(query)
                )
            );
        });
    }, [documents, searchQuery]);

    const filteredByType = selectedTypes.length
        ? filteredDocuments.filter((document) =>
              selectedTypes.includes(document.category)
          )
        : filteredDocuments;

    useEffect(() => {
        fetchDocuments();
    }, [patientId, selectedTypes, sortBy]);

    return {
        documents: filteredByType,
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
        refreshDocuments: fetchDocuments,
    };
}
