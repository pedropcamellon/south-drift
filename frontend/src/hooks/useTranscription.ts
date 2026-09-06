import { useCallback, useEffect, useRef, useState } from "react";

import { API_ENDPOINTS, apiJson } from "@/lib/api";

import {
    PatientEncounter,
    VoiceNoteWorkflowStatus,
    VoiceNoteWorkflowStatusResponse,
} from "@/types";

export enum TranscriptionState {
    IDLE = "idle",
    PENDING = "pending",
    COMPLETE = "complete",
    PARTIAL = "partial",
    ERROR = "error",
}

export function useTranscription() {
    const [transcriptionState, setTranscriptionState] =
        useState<TranscriptionState>(TranscriptionState.IDLE);
    const pollingTimeoutRef = useRef<NodeJS.Timeout | null>(null);
    const pollingAbortRef = useRef<AbortController | null>(null);

    const startPolling = useCallback(
        (
            encounterId: string,
            onUpdate: (encounter: PatientEncounter) => void
        ) => {
            // Abort any existing polling
            if (pollingAbortRef.current) {
                pollingAbortRef.current.abort();
            }
            if (pollingTimeoutRef.current) {
                clearTimeout(pollingTimeoutRef.current);
            }

            setTranscriptionState(TranscriptionState.PENDING);
            const abortController = new AbortController();
            pollingAbortRef.current = abortController;

            const poll = async () => {
                if (abortController.signal.aborted) return;

                try {
                    const data = await apiJson<VoiceNoteWorkflowStatusResponse>(
                        API_ENDPOINTS.encounterVoiceNoteStatus(encounterId)
                    );

                    if (data.encounter) {
                        onUpdate(data.encounter);
                    }

                    if (data.status === VoiceNoteWorkflowStatus.FAILED) {
                        setTranscriptionState(TranscriptionState.ERROR);
                        pollingAbortRef.current = null;
                        return;
                    }

                    if (data.status === VoiceNoteWorkflowStatus.PARTIAL) {
                        setTranscriptionState(TranscriptionState.PARTIAL);
                        pollingAbortRef.current = null;
                        return;
                    }

                    if (data.status === VoiceNoteWorkflowStatus.TRANSCRIBED) {
                        setTranscriptionState(TranscriptionState.COMPLETE);
                        pollingAbortRef.current = null;
                        return;
                    }

                    if (data.status === VoiceNoteWorkflowStatus.COMPLETED) {
                        setTranscriptionState(TranscriptionState.COMPLETE);
                        pollingAbortRef.current = null;
                        return;
                    }
                } catch (e) {
                    console.error("Polling error:", e);
                    setTranscriptionState(TranscriptionState.ERROR);
                    pollingAbortRef.current = null;
                    return;
                }

                // Continue polling
                if (!abortController.signal.aborted) {
                    pollingTimeoutRef.current = setTimeout(poll, 1000);
                }
            };

            // Start polling
            poll();

            // Stop after 2 minutes max
            setTimeout(() => {
                if (!abortController.signal.aborted) {
                    abortController.abort();
                    setTranscriptionState(TranscriptionState.IDLE);
                    pollingAbortRef.current = null;
                    if (pollingTimeoutRef.current) {
                        clearTimeout(pollingTimeoutRef.current);
                    }
                }
            }, 120000);
        },
        []
    );

    const stopPolling = useCallback(() => {
        if (pollingAbortRef.current) {
            pollingAbortRef.current.abort();
            pollingAbortRef.current = null;
        }
        if (pollingTimeoutRef.current) {
            clearTimeout(pollingTimeoutRef.current);
            pollingTimeoutRef.current = null;
        }
        setTranscriptionState(TranscriptionState.IDLE);
    }, []);

    // Cleanup on unmount
    useEffect(() => {
        return () => {
            if (pollingAbortRef.current) {
                pollingAbortRef.current.abort();
            }
            if (pollingTimeoutRef.current) {
                clearTimeout(pollingTimeoutRef.current);
            }
        };
    }, []);

    return {
        transcriptionState,
        startPolling,
        stopPolling,
    };
}
