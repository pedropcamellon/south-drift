/**
 * Custom hook for interaction form logic
 * Handles form state, validation, submission, and error handling
 */
import { useState } from "react";

import { mutate } from "swr";

import { API_ENDPOINTS, apiRequest } from "@/lib/api";

export interface EncounterFormData {
    encounterType: string;
    purpose: string;
    title: string;
    description: string;
    startedAt: string;
    location: string;
    clinicianId: string;
    clinicianName: string;
}

interface UseInteractionFormProps {
    patientId: string;
    onSuccess?: () => void;
}

interface UseInteractionFormReturn {
    formData: EncounterFormData;
    loading: boolean;
    error: string | null;
    setFormData: React.Dispatch<React.SetStateAction<EncounterFormData>>;
    updateField: (field: keyof EncounterFormData, value: string) => void;
    handleSubmit: (e: React.FormEvent) => Promise<void>;
    resetForm: () => void;
}

const getInitialFormData = (): EncounterFormData => ({
    encounterType: "outpatient",
    purpose: "follow_up",
    title: "",
    description: "",
    startedAt: new Date().toISOString().slice(0, 16),
    location: "",
    clinicianId: "",
    clinicianName: "",
});

export function useEncounterForm({
    patientId,
    onSuccess,
}: UseInteractionFormProps): UseInteractionFormReturn {
    const [formData, setFormData] =
        useState<EncounterFormData>(getInitialFormData());
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const updateField = (field: keyof EncounterFormData, value: string) => {
        setFormData((prev) => ({ ...prev, [field]: value }));
    };

    const resetForm = () => {
        setFormData(getInitialFormData());
        setError(null);
    };

    const validate = (): boolean => {
        if (!formData.encounterType || !formData.title || !formData.startedAt) {
            setError("Please fill in all required fields (Type, Title, Date)");
            return false;
        }
        return true;
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setError(null);

        if (!validate()) {
            return;
        }

        setLoading(true);

        try {
            const payload = {
                patientId,
                encounterType: formData.encounterType,
                purpose: formData.purpose,
                status: "completed",
                title: formData.title,
                description: formData.description || undefined,
                startedAt: new Date(formData.startedAt).toISOString(),
                location: formData.location || undefined,
                clinicianId: formData.clinicianId || undefined,
                clinicianName: formData.clinicianName || undefined,
                isCompliant: true,
            };

            const response = await apiRequest(API_ENDPOINTS.encounters, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                },
                body: JSON.stringify(payload),
            });

            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(
                    errorData.detail ||
                        `Failed to create interaction: ${response.statusText}`
                );
            }

            // Refresh interactions list for this patient
            await mutate(API_ENDPOINTS.encountersByPatient(patientId));

            // Success callback
            if (onSuccess) {
                onSuccess();
            }

            resetForm();
        } catch (err) {
            console.error("Error creating interaction:", err);
            setError(
                err instanceof Error
                    ? err.message
                    : "Failed to create interaction"
            );
        } finally {
            setLoading(false);
        }
    };

    return {
        formData,
        loading,
        error,
        setFormData,
        updateField,
        handleSubmit,
        resetForm,
    };
}
