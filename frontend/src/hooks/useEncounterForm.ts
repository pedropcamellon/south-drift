"use client";

import { useState } from "react";

import { mutate } from "swr";

import { API_ENDPOINTS, apiRequest } from "@/lib/api";

import type { EncounterPurpose, EncounterType } from "@/types";

export interface EncounterFormData {
    encounterType: EncounterType;
    purpose: EncounterPurpose;
    title: string;
    description: string;
    startedAt: string;
    location: string;
    clinicianId: string;
    clinicianName: string;
}

interface UseEncounterFormProps {
    patientId: string;
    onSuccess?: () => void;
}

const initialFormData = (): EncounterFormData => ({
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
}: UseEncounterFormProps) {
    const [formData, setFormData] =
        useState<EncounterFormData>(initialFormData());
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const updateField = (field: keyof EncounterFormData, value: string) => {
        setFormData((current) => ({ ...current, [field]: value }));
    };

    const resetForm = () => {
        setFormData(initialFormData());
        setError(null);
    };

    const handleSubmit = async (event: React.FormEvent) => {
        event.preventDefault();
        setError(null);
        if (!formData.encounterType || !formData.title || !formData.startedAt) {
            setError("Please fill in all required fields.");
            return;
        }

        setLoading(true);
        try {
            const response = await apiRequest(API_ENDPOINTS.encounters, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
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
                }),
            });
            if (!response.ok) {
                const body = await response.json().catch(() => ({}));
                throw new Error(
                    body.detail ||
                        `Failed to create encounter: ${response.statusText}`
                );
            }
            await mutate(API_ENDPOINTS.encountersByPatient(patientId));
            await mutate(API_ENDPOINTS.patientTimeline(patientId));
            onSuccess?.();
            resetForm();
        } catch (reason) {
            console.error("Error creating encounter:", reason);
            setError(
                reason instanceof Error
                    ? reason.message
                    : "Failed to create encounter"
            );
        } finally {
            setLoading(false);
        }
    };

    return { formData, loading, error, updateField, handleSubmit, resetForm };
}
