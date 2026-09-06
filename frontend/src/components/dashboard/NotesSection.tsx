import { useEffect, useRef, useState } from "react";

import { FaMicrophone, FaPause } from "react-icons/fa";

import { Button } from "@/components/ui/button";

import { API_ENDPOINTS, apiRequest } from "@/lib/api";

import { AudioState, useEncounterAudio } from "@/hooks/useEncounterAudio";
import { TranscriptionState } from "@/hooks/useTranscription";

import { PatientEncounter } from "@/types";

enum NoteEditState {
    VIEWING = "viewing",
    EDITING = "editing",
    SAVING = "saving",
}

interface NotesSectionProps {
    encounter: PatientEncounter;
    onEncounterUpdate: (encounter: PatientEncounter) => void;
    onAudioSubmitted?: () => void;
    transcriptionState?: TranscriptionState;
}

export function NotesSection({
    encounter,
    onEncounterUpdate,
    onAudioSubmitted,
    transcriptionState = TranscriptionState.IDLE,
}: NotesSectionProps) {
    const [note, setNote] = useState(encounter.note || "");
    const [editState, setEditState] = useState<NoteEditState>(
        NoteEditState.VIEWING
    );
    const [editedNote, setEditedNote] = useState("");
    const [lastSavedNote, setLastSavedNote] = useState(encounter.note || "");
    const [saveError, setSaveError] = useState<string | null>(null);
    const noteInputRef = useRef<HTMLTextAreaElement>(null);

    const {
        audioState,
        audioUrl,
        recordingError,
        submitError,
        startRecording,
        stopRecording,
        submitAudio,
        loadExistingAudio,
    } = useEncounterAudio(encounter.id);

    // Call parent's polling when audio is submitted successfully
    useEffect(() => {
        if (audioState === "submitted" && onAudioSubmitted) {
            onAudioSubmitted();
        }
    }, [audioState, onAudioSubmitted]);

    // Sync note state when encounter changes
    useEffect(() => {
        setNote(encounter.note || "");
        setLastSavedNote(encounter.note || "");
    }, [encounter.note]);

    // Handle transcription state changes
    useEffect(() => {
        // Don't overwrite if user is actively editing
        if (editState === NoteEditState.EDITING) {
            return;
        }

        if (transcriptionState === TranscriptionState.COMPLETE) {
            // When transcription completes, show the new note in viewing mode
            setEditState(NoteEditState.VIEWING);
            setNote(encounter.note || "");
            setLastSavedNote(encounter.note || "");
        } else if (transcriptionState === TranscriptionState.PARTIAL) {
            setEditState(NoteEditState.VIEWING);
            setNote(encounter.note || "");
            setLastSavedNote(encounter.note || "");
        } else if (transcriptionState === TranscriptionState.ERROR) {
            // When transcription fails, ensure we're in viewing mode to show the error
            setEditState(NoteEditState.VIEWING);
        }
    }, [transcriptionState, encounter.note, editState]);

    // Load audio only when encounter ID changes (not when note changes)
    useEffect(() => {
        loadExistingAudio();
    }, [encounter.id, loadExistingAudio]);

    useEffect(() => {
        if (editState === NoteEditState.EDITING) {
            setEditedNote(note);
            setTimeout(() => noteInputRef.current?.focus(), 0);
        }
    }, [editState, note]);

    const handleSave = async () => {
        setEditState(NoteEditState.SAVING);
        setSaveError(null);
        try {
            const res = await apiRequest(
                API_ENDPOINTS.encounterNote(encounter.id),
                {
                    method: "PATCH",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ content: editedNote }),
                }
            );
            if (!res.ok) throw new Error("Failed to save note");
            setNote(editedNote);
            setLastSavedNote(editedNote);
            onEncounterUpdate({ ...encounter, note: editedNote });
            setEditState(NoteEditState.VIEWING);
        } catch (e) {
            setSaveError("Failed to save note");
            setEditState(NoteEditState.EDITING);
        }
    };

    const handleCancel = () => {
        setEditedNote(lastSavedNote);
        setEditState(NoteEditState.VIEWING);
    };

    return (
        <div>
            <div className="flex items-center gap-2 mb-2">
                <div className="font-semibold">Notes</div>
                {audioState !== AudioState.RECORDING ? (
                    <Button
                        size="icon-sm"
                        variant="tertiary"
                        onClick={startRecording}
                        aria-label="Record"
                    >
                        <FaMicrophone />
                    </Button>
                ) : (
                    <Button
                        size="icon-sm"
                        variant="danger-primary"
                        onClick={stopRecording}
                        aria-label="Stop Recording"
                    >
                        <FaPause className="animate-pulse" />
                    </Button>
                )}
                <span className="text-xs text-slate-500">
                    {audioState === AudioState.RECORDING
                        ? "Recording..."
                        : transcriptionState === TranscriptionState.PENDING
                          ? "Processing transcript..."
                          : "Voice Recording"}
                </span>
                {audioUrl && (
                    <audio controls src={audioUrl} className="ml-2 h-10" />
                )}
            </div>
            {audioState === AudioState.RECORDED && (
                <div className="flex items-center gap-2 mb-3">
                    <span className="text-xs text-slate-600">Looks good?</span>
                    <Button size="sm" variant="primary" onClick={submitAudio}>
                        Submit Audio
                    </Button>
                </div>
            )}
            {audioState === AudioState.SUBMITTING && (
                <div className="flex items-center gap-2 mb-3">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                        />
                        <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                        />
                    </svg>
                    <span className="text-xs text-slate-600">Uploading...</span>
                </div>
            )}
            {audioState === AudioState.SUBMITTED && (
                <div className="text-xs text-green-600 mb-3">
                    Audio submitted successfully!
                </div>
            )}
            {transcriptionState === TranscriptionState.PENDING && (
                <div className="flex items-center gap-2 mb-3">
                    <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24">
                        <circle
                            className="opacity-25"
                            cx="12"
                            cy="12"
                            r="10"
                            stroke="currentColor"
                            strokeWidth="4"
                            fill="none"
                        />
                        <path
                            className="opacity-75"
                            fill="currentColor"
                            d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z"
                        />
                    </svg>
                    <span className="text-xs text-slate-600">
                        Waiting for transcription...
                    </span>
                </div>
            )}

            {transcriptionState === TranscriptionState.COMPLETE && (
                <div className="text-xs text-green-600 mb-3">
                    Transcription complete!
                </div>
            )}

            {transcriptionState === TranscriptionState.PARTIAL && (
                <div className="text-xs text-amber-600 mb-3">
                    Transcript saved. Summary generation did not complete.
                </div>
            )}

            {transcriptionState === TranscriptionState.ERROR && (
                <div className="text-xs text-red-600 mb-3">
                    Transcription failed. Please try again.
                </div>
            )}

            {audioState === AudioState.ERROR && submitError && (
                <div className="text-xs text-red-500 mb-3">{submitError}</div>
            )}
            {recordingError && (
                <div className="text-xs text-red-500 mb-1">
                    {recordingError}
                </div>
            )}

            {editState === NoteEditState.VIEWING ? (
                <>
                    <div className="whitespace-pre-wrap text-sm mb-2 border p-2 rounded">
                        {note || "No notes yet."}
                    </div>
                    <Button
                        size="sm"
                        variant="tertiary"
                        onClick={() => setEditState(NoteEditState.EDITING)}
                    >
                        Edit Note
                    </Button>
                </>
            ) : (
                <>
                    <textarea
                        ref={noteInputRef}
                        value={editedNote}
                        onChange={(e) => setEditedNote(e.target.value)}
                        className="w-full border p-2 rounded text-sm mb-2 min-h-[100px]"
                        placeholder="Type your notes here..."
                    />
                    <div className="flex items-center gap-2">
                        <Button
                            size="sm"
                            onClick={handleSave}
                            disabled={editState === NoteEditState.SAVING}
                            isLoading={editState === NoteEditState.SAVING}
                            loadingText="Saving..."
                        >
                            Save
                        </Button>
                        <Button
                            size="sm"
                            variant="ghost"
                            onClick={handleCancel}
                        >
                            Cancel
                        </Button>
                    </div>
                    {saveError && (
                        <div className="text-xs text-red-500 mt-1">
                            {saveError}
                        </div>
                    )}
                </>
            )}
        </div>
    );
}
