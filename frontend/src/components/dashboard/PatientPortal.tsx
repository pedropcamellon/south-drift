"use client";

import React, { useEffect, useState } from "react";

import type { PatientTimelineResponse } from "@/types/patientTimeline";

import { API_ENDPOINTS, apiJson } from "@/lib/api";

import { Patient } from "@/types";

import PatientHistoryTimeline from "./PatientHistoryTimeline";

interface PatientPortalProps {
    patient: Patient;
    onClose: () => void;
}

export default function PatientPortal({
    patient,
    onClose,
}: PatientPortalProps) {
    const [timeline, setTimeline] = useState<PatientTimelineResponse>({
        entries: [],
    });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        async function fetchTimeline() {
            setLoading(true);
            setError(null);
            try {
                const data = await apiJson<PatientTimelineResponse>(
                    API_ENDPOINTS.patientTimeline(patient.id)
                );
                setTimeline(data);
            } catch (error: unknown) {
                setError(
                    error instanceof Error ? error.message : "Unknown error"
                );
            } finally {
                setLoading(false);
            }
        }
        void fetchTimeline();
    }, [patient.id]);

    const encounters = timeline.entries.flatMap((entry) =>
        entry.kind === "encounter" ? [entry.encounter] : []
    );
    const recent = timeline.entries.slice(0, 3);

    return (
        <div className="fixed inset-0 bg-black bg-opacity-30 z-50 flex items-center justify-center">
            <div className="bg-white rounded-lg shadow-lg w-full max-w-2xl p-6 relative">
                <button
                    className="absolute top-2 right-2 text-slate-400 hover:text-slate-700"
                    onClick={onClose}
                >
                    &times;
                </button>
                <h2 className="text-xl font-bold mb-2">Patient Portal</h2>
                <div className="mb-4">
                    <div className="font-semibold">
                        {patient.firstName} {patient.lastName}
                    </div>
                    <div className="text-sm text-slate-500">
                        MRN: {patient.medicalRecordNumber} | Gender:{" "}
                        {patient.gender} | DOB:{" "}
                        {new Date(patient.dateOfBirth).toLocaleDateString()}
                    </div>
                    <div className="text-sm text-slate-500">
                        Contact: {patient.contactInfo}
                    </div>
                </div>
                <div className="mb-4 flex gap-4">
                    <div className="bg-blue-50 rounded p-3 flex-1">
                        <div className="text-xs text-slate-500">
                            Total Encounters
                        </div>
                        <div className="text-2xl font-bold text-blue-700">
                            {encounters.length}
                        </div>
                    </div>
                    <div className="bg-green-50 rounded p-3 flex-1">
                        <div className="text-xs text-slate-500">
                            Recent Activity
                        </div>
                        <ul className="text-sm mt-1">
                            {recent.map((entry) => (
                                <li key={`${entry.kind}-${entry.id}`}>
                                    {entry.title}{" "}
                                    <span className="text-xs text-slate-400">
                                        (
                                        {entry.kind === "encounter"
                                            ? entry.encounter.encounterType
                                            : "diagnostic report"}
                                        )
                                    </span>
                                </li>
                            ))}
                            {recent.length === 0 && (
                                <li className="text-slate-400">
                                    No recent activity
                                </li>
                            )}
                        </ul>
                    </div>
                </div>
                <div>
                    <h3 className="font-semibold mb-2">Encounter Timeline</h3>
                    {loading ? (
                        <div>Loading...</div>
                    ) : error ? (
                        <div className="text-red-600">{error}</div>
                    ) : (
                        <PatientHistoryTimeline entries={timeline.entries} />
                    )}
                </div>
            </div>
        </div>
    );
}
