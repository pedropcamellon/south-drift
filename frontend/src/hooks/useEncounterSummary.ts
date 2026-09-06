import { useCallback, useState } from "react";

import {
    formatSoapSummary,
    generateSummary,
} from "@/services/summarizationService";

import { StructuredSummary } from "@/types";

export enum SummaryState {
    IDLE = "idle",
    GENERATING = "generating",
    SUCCESS = "success",
    ERROR = "error",
}

interface UseEncounterSummaryResult {
    summary: string;
    summaryState: SummaryState;
    summaryError: string | null;
    generateSummaryFromTranscript: (
        transcript: string,
        encounterType?: string
    ) => Promise<void>;
    setSummary: (summary: string) => void;
    clearError: () => void;
}

export function useEncounterSummary(
    onSummaryGenerated?: (
        summary: string,
        structuredData: StructuredSummary
    ) => void
): UseEncounterSummaryResult {
    const [summary, setSummary] = useState<string>("");
    const [summaryState, setSummaryState] = useState<SummaryState>(
        SummaryState.IDLE
    );
    const [summaryError, setSummaryError] = useState<string | null>(null);

    const generateSummaryFromTranscript = useCallback(
        async (transcript: string, encounterType?: string) => {
            if (!transcript || transcript.trim().length === 0) {
                setSummaryState(SummaryState.ERROR);
                setSummaryError(
                    "No transcript available. Please add a note or record audio first."
                );
                return;
            }

            setSummaryState(SummaryState.GENERATING);
            setSummaryError(null);

            try {
                const response = await generateSummary({
                    transcript,
                    format: "soap",
                    encounter_type: encounterType,
                });

                const formattedSummary = formatSoapSummary(
                    response.structured_data
                );
                setSummary(formattedSummary);
                setSummaryState(SummaryState.SUCCESS);

                // Notify parent component of successful generation
                onSummaryGenerated?.(
                    formattedSummary,
                    response.structured_data
                );
            } catch (e: any) {
                setSummaryState(SummaryState.ERROR);
                setSummaryError(e?.message || "Failed to generate summary");
            }
        },
        [onSummaryGenerated]
    );

    const clearError = useCallback(() => {
        setSummaryError(null);
        if (summaryState === SummaryState.ERROR) {
            setSummaryState(SummaryState.IDLE);
        }
    }, [summaryState]);

    return {
        summary,
        summaryState,
        summaryError,
        generateSummaryFromTranscript,
        setSummary,
        clearError,
    };
}
