import { useCallback, useRef, useState } from "react";

import { API_ENDPOINTS, apiJson, apiRequest } from "@/lib/api";

import type { PatientEncounter } from "@/types";

const MIN_RECORDING_DURATION_MS = 1000;

export enum AudioState {
    IDLE = "idle",
    LOADED = "loaded", // Audio loaded from backend
    RECORDING = "recording",
    RECORDED = "recorded",
    SUBMITTING = "submitting",
    SUBMITTED = "submitted",
    ERROR = "error",
}

export function useEncounterAudio(encounterId: string) {
    const [audioState, setAudioState] = useState<AudioState>(AudioState.IDLE);
    const [audioUrl, setAudioUrl] = useState<string | null>(null);
    const [recordingError, setRecordingError] = useState<string | null>(null);
    const [submitError, setSubmitError] = useState<string | null>(null);
    const [mediaRecorder, setMediaRecorder] = useState<MediaRecorder | null>(
        null
    );

    const audioChunks = useRef<Blob[]>([]);
    const recordingStartedAt = useRef<number | null>(null);
    const recordedDurationMs = useRef<number>(0);

    const startRecording = async () => {
        setRecordingError(null);
        setSubmitError(null);
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true,
            });
            const recorder = new window.MediaRecorder(stream);
            audioChunks.current = [];
            recordingStartedAt.current = Date.now();
            recordedDurationMs.current = 0;

            recorder.ondataavailable = (e) => {
                if (e.data.size > 0) {
                    audioChunks.current.push(e.data);
                }
            };

            recorder.onstop = () => {
                const startedAt = recordingStartedAt.current;
                const durationMs = startedAt ? Date.now() - startedAt : 0;
                recordedDurationMs.current = durationMs;
                recorder.stream.getTracks().forEach((track) => track.stop());

                if (durationMs <= MIN_RECORDING_DURATION_MS) {
                    setAudioUrl(null);
                    setRecordingError(
                        "Recordings must be longer than 1 second."
                    );
                    setMediaRecorder(null);
                    setAudioState(AudioState.IDLE);
                    return;
                }

                const audioBlob = new Blob(audioChunks.current, {
                    type: "audio/webm",
                });
                setAudioUrl(URL.createObjectURL(audioBlob));
                setMediaRecorder(null);
                setAudioState(AudioState.RECORDED);
            };

            recorder.start();
            setMediaRecorder(recorder);
            setAudioState(AudioState.RECORDING);
        } catch (err) {
            setRecordingError("Microphone access denied or unavailable.");
            setAudioState(AudioState.ERROR);
        }
    };

    const stopRecording = () => {
        if (mediaRecorder && audioState === AudioState.RECORDING) {
            mediaRecorder.stop();
        }
    };

    const submitAudio = async () => {
        setSubmitError(null);

        if (!audioUrl) {
            setSubmitError("No audio to submit");
            return;
        }

        if (recordedDurationMs.current <= MIN_RECORDING_DURATION_MS) {
            setAudioUrl(null);
            setRecordingError("Recordings must be longer than 1 second.");
            setAudioState(AudioState.IDLE);
            return;
        }

        let audioBlob: Blob;
        try {
            audioBlob = await fetch(audioUrl).then((r) => r.blob());
        } catch {
            setSubmitError("Failed to load audio blob");
            setAudioState(AudioState.ERROR);
            return;
        }

        setAudioState(AudioState.SUBMITTING);

        try {
            const formData = new FormData();
            formData.append("audio", audioBlob, "audio.webm");

            const res = await apiRequest(
                `${API_ENDPOINTS.encounter(encounterId)}/audio`,
                {
                    method: "POST",
                    body: formData,
                }
            );

            if (!res.ok) {
                let errorMsg = "Failed to submit audio";
                try {
                    const err = await res.json();
                    errorMsg = err?.error || errorMsg;
                } catch {}
                throw new Error(errorMsg);
            }

            setAudioState(AudioState.SUBMITTED);
            // Parent component will handle polling for transcription
        } catch (e: any) {
            setSubmitError(e?.message || "Submission failed");
            setAudioState(AudioState.ERROR);
        }
    };

    const cleanup = () => {
        setAudioState(AudioState.IDLE);
        setAudioUrl(null);
        setRecordingError(null);
        setSubmitError(null);
        recordedDurationMs.current = 0;
        recordingStartedAt.current = null;
    };

    const loadExistingAudio = useCallback(async () => {
        try {
            const data = await apiJson<{
                audioMetadata?: PatientEncounter["audioMetadata"];
            }>(API_ENDPOINTS.encounter(encounterId));
            if (data.audioMetadata) {
                const audioRes = await apiRequest(
                    `${API_ENDPOINTS.encounter(encounterId)}/audio`
                );
                if (audioRes.ok) {
                    const audioBlob = await audioRes.blob();
                    setAudioUrl(URL.createObjectURL(audioBlob));
                    setAudioState(AudioState.LOADED);
                }
            }
        } catch {
            // Ignore errors loading existing audio
        }
    }, [encounterId]);

    return {
        audioState,
        audioUrl,
        recordingError,
        submitError,
        startRecording,
        stopRecording,
        submitAudio,
        cleanup,
        loadExistingAudio,
    };
}
