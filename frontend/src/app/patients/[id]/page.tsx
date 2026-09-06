"use client";

import { useParams } from "next/navigation";

import type { PatientTimelineResponse } from "@/types/patientTimeline";
import useSWR from "swr";

import { PatientClinicalDocumentsPanel } from "@/components/clinicalDocuments/PatientClinicalDocumentsPanel";
import DashboardLayout from "@/components/dashboard/DashboardLayout";
import { NewEncounterDialog } from "@/components/dashboard/NewEncounterDialog";
import PatientHistoryTimeline from "@/components/dashboard/PatientHistoryTimeline";
import { Card } from "@/components/ui/card";

import { API_ENDPOINTS, fetcher } from "@/lib/api";

// Types
import { Patient, PatientEncounter } from "@/types";

export default function PatientPage() {
    const params = useParams();
    const id =
        typeof params.id === "string"
            ? params.id
            : Array.isArray(params.id)
              ? params.id[0]
              : "";

    const {
        data: patient,
        error: patientError,
        isLoading: patientLoading,
    } = useSWR<Patient>(id ? API_ENDPOINTS.patient(id) : null, fetcher);
    const {
        data: timelinePage,
        error: timelineError,
        isLoading: timelineLoading,
    } = useSWR<PatientTimelineResponse>(
        id ? API_ENDPOINTS.patientTimeline(id) : null,
        fetcher
    );

    if (patientLoading || timelineLoading) {
        return (
            <DashboardLayout>
                <div className="p-6">Loading...</div>
            </DashboardLayout>
        );
    }
    if (patientError || !patient) {
        return (
            <DashboardLayout>
                <div className="p-6 text-red-600">Patient not found.</div>
            </DashboardLayout>
        );
    }
    if (timelineError || !timelinePage) {
        return (
            <DashboardLayout>
                <div className="p-6 text-red-600">
                    Failed to load patient history.
                </div>
            </DashboardLayout>
        );
    }
    const timeline = timelinePage.entries;
    const encounters = timeline.flatMap((entry) =>
        entry.kind === "encounter" ? [entry.encounter] : []
    );
    const recent = timeline.slice(0, 3);

    return (
        <DashboardLayout>
            <div className="p-6">
                <Card className="p-8">
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

                    <div>
                        <h3 className="font-semibold mb-2">Documents</h3>
                        <PatientClinicalDocumentsPanel patientId={patient.id} />
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
                        <div className="flex items-center justify-between mb-4">
                            <h3 className="font-semibold">
                                Encounter Timeline
                            </h3>
                            <NewEncounterDialog
                                patientId={patient.id}
                                patientName={`${patient.firstName} ${patient.lastName}`}
                            />
                        </div>
                        <PatientHistoryTimeline entries={timeline} />
                    </div>
                </Card>
            </div>
        </DashboardLayout>
    );
}
