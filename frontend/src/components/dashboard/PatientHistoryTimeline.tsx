"use client";

import { useCallback, useEffect, useState } from "react";

import type { PatientTimelineEntry } from "@/types/patientTimeline";
import { ChevronRight } from "lucide-react";

import { API_ENDPOINTS, apiJson } from "@/lib/api";

import { useTranscription } from "@/hooks/useTranscription";

import { PatientEncounter } from "@/types";

import EncounterDetailsModal from "./EncounterDetailsModal";

interface PatientHistoryTimelineProps {
    entries: PatientTimelineEntry[];
}

const typeColors: Record<PatientEncounter["encounterType"], string> = {
    outpatient: "#2563eb",
    telehealth: "#22c55e",
    telephone: "#f59e42",
    portal: "#a21caf",
    emergency: "#ef4444",
    inpatient: "#14b8a6",
};

export default function PatientHistoryTimeline({
    entries,
}: PatientHistoryTimelineProps) {
    const [selectedId, setSelectedId] = useState<string | null>(null);
    const [selectedEncounter, setSelectedEncounter] =
        useState<PatientEncounter | null>(null);

    const { transcriptionState, startPolling } = useTranscription();

    // Fetch the selected encounter.
    useEffect(() => {
        if (!selectedId) {
            setSelectedEncounter(null);
            return;
        }

        const fetchEncounter = async () => {
            try {
                const data = await apiJson<PatientEncounter>(
                    API_ENDPOINTS.encounter(selectedId)
                );
                setSelectedEncounter(data);
            } catch (e) {
                console.error("Failed to fetch encounter:", e);
            }
        };

        void fetchEncounter();
    }, [selectedId]);

    const handleSelectEncounter = useCallback((encounter: PatientEncounter) => {
        setSelectedEncounter(encounter);
        setSelectedId(encounter.id);
    }, []);

    // Memoize callback to prevent recreating on every render
    const handleAudioSubmitted = useCallback(() => {
        if (selectedId) {
            startPolling(selectedId, (updatedEncounter) => {
                setSelectedEncounter(updatedEncounter);
            });
        }
    }, [selectedId, startPolling]);

    if (entries.length === 0) {
        return <div className="text-slate-400">No history found.</div>;
    }

    return (
        <div className="relative pl-8">
            {/* Vertical line */}
            <div
                className="absolute left-3 top-0 bottom-0 w-0.5 bg-slate-200"
                style={{ zIndex: 0 }}
            />
            <div className="flex flex-col gap-8">
                {entries.map((item, idx) =>
                    item.kind === "encounter" ? (
                        <button
                            type="button"
                            key={item.id}
                            className="relative flex w-full items-start justify-between gap-4 rounded-lg border border-transparent py-3 pl-10 pr-3 text-left cursor-pointer group transition-colors hover:border-slate-200 hover:bg-slate-50 focus-visible:border-slate-300 focus-visible:bg-slate-50 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-slate-200"
                            onClick={() =>
                                handleSelectEncounter(item.encounter)
                            }
                            aria-label={`View details for ${item.encounter.title}`}
                        >
                            {/* Dot */}
                            <div
                                className="absolute left-2 top-4 w-4 flex flex-col items-center"
                                style={{ zIndex: 1 }}
                            >
                                <div
                                    className="w-4 h-4 rounded-full border-4 group-hover:scale-110 transition-transform"
                                    style={{
                                        borderColor:
                                            typeColors[
                                                item.encounter.encounterType
                                            ],
                                        background: "#fff",
                                    }}
                                />
                                {/* Only draw line below if not last */}
                                {idx !== entries.length - 1 && (
                                    <div className="w-0.5 flex-1 bg-slate-200 mt-0.5" />
                                )}
                            </div>
                            <div className="flex-1">
                                <div className="font-semibold text-base">
                                    {item.encounter.title}{" "}
                                    <span className="text-xs font-normal text-slate-400">
                                        ({item.encounter.encounterType})
                                    </span>
                                </div>
                                <div className="text-xs text-slate-500 mb-1">
                                    {new Date(
                                        item.encounter.startedAt
                                    ).toLocaleString()}{" "}
                                    &middot; {item.encounter.clinicianName}
                                </div>
                                <div className="text-sm text-slate-700">
                                    {item.encounter.description}
                                </div>
                            </div>
                            <div className="flex items-center gap-2 self-center pl-2 text-slate-400 transition-transform group-hover:translate-x-0.5 group-hover:text-slate-600 group-focus-visible:translate-x-0.5 group-focus-visible:text-slate-600">
                                <span className="hidden text-xs font-medium text-slate-500 sm:inline">
                                    View details
                                </span>
                                <ChevronRight className="h-4 w-4" />
                            </div>
                        </button>
                    ) : item.kind === "diagnostic_report" ? (
                        <div
                            key={item.id}
                            className="relative flex w-full items-start gap-4 py-3 pl-10 pr-3"
                        >
                            <div className="absolute left-2 top-4 w-4 flex flex-col items-center">
                                <div
                                    className="w-4 h-4 rounded-full border-4"
                                    style={{
                                        borderColor: "#a21caf",
                                        background: "#fff",
                                    }}
                                />
                            </div>
                            <div className="flex-1">
                                <div className="font-semibold text-base">
                                    {item.diagnosticReport.title}{" "}
                                    <span className="text-xs font-normal text-slate-400">
                                        (Lab Result)
                                    </span>
                                </div>
                                <div className="text-xs text-slate-500 mb-1">
                                    {new Date(item.occurredAt).toLocaleString()}
                                </div>
                                {item.diagnosticReport.conclusion && (
                                    <div className="text-sm text-slate-700">
                                        {item.diagnosticReport.conclusion}
                                    </div>
                                )}
                                {item.diagnosticReport.observations.length >
                                    0 && (
                                    <ul className="mt-2 text-sm text-slate-700">
                                        {item.diagnosticReport.observations.map(
                                            (observation) => (
                                                <li key={observation.id}>
                                                    {observation.display}:{" "}
                                                    {observation.value ??
                                                        observation.dataAbsentReason}
                                                    {observation.unit
                                                        ? ` ${observation.unit}`
                                                        : ""}
                                                </li>
                                            )
                                        )}
                                    </ul>
                                )}
                            </div>
                        </div>
                    ) : (
                        <div
                            key={item.id}
                            className="relative flex w-full items-start gap-4 py-3 pl-10 pr-3"
                        >
                            <div className="absolute left-2 top-4 w-4 flex flex-col items-center">
                                <div
                                    className="w-4 h-4 rounded-full border-4"
                                    style={{
                                        borderColor: "#0f766e",
                                        background: "#fff",
                                    }}
                                />
                            </div>
                            <div className="flex-1">
                                <div className="font-semibold text-base">
                                    {item.title}{" "}
                                    <span className="text-xs font-normal text-slate-400">
                                        (Imaging Study)
                                    </span>
                                </div>
                                <div className="text-xs text-slate-500 mb-1">
                                    {new Date(item.occurredAt).toLocaleString()}
                                </div>
                                <div className="text-sm text-slate-700">
                                    Modality:{" "}
                                    {item.imagingStudy.modality.toUpperCase()}
                                    {item.imagingStudy.externalStudyId
                                        ? ` | Study ID: ${item.imagingStudy.externalStudyId}`
                                        : ""}
                                </div>
                            </div>
                        </div>
                    )
                )}
            </div>
            {selectedEncounter && (
                <EncounterDetailsModal
                    encounter={selectedEncounter}
                    open={!!selectedEncounter}
                    onClose={() => {
                        setSelectedId(null);
                        setSelectedEncounter(null);
                    }}
                    onAudioSubmitted={handleAudioSubmitted}
                    transcriptionState={transcriptionState}
                />
            )}
        </div>
    );
}
