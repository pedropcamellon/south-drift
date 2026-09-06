import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

import type { TranscriptionState } from "@/hooks/useTranscription";

import type { PatientEncounter } from "@/types";

import { ChartReviewSection } from "./ChartReviewSection";
import { NotesSection } from "./NotesSection";
import { SummarySection } from "./SummarySection";

interface EncounterDetailsModalProps {
    encounter: PatientEncounter;
    open: boolean;
    onClose: () => void;
    onAudioSubmitted: () => void;
    transcriptionState: TranscriptionState;
}

export default function EncounterDetailsModal({
    encounter,
    open,
    onClose,
    onAudioSubmitted,
    transcriptionState,
}: EncounterDetailsModalProps) {
    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="flex max-h-[85vh] w-full max-w-2xl flex-col">
                <DialogHeader>
                    <DialogTitle>Encounter Details</DialogTitle>
                </DialogHeader>
                <div className="flex flex-col gap-4 overflow-y-auto pr-3">
                    <SummarySection
                        encounter={encounter}
                        note={encounter.note || ""}
                        onEncounterUpdate={() => {}}
                    />
                    <NotesSection
                        encounter={encounter}
                        onEncounterUpdate={() => {}}
                        onAudioSubmitted={onAudioSubmitted}
                        transcriptionState={transcriptionState}
                    />
                    <ChartReviewSection encounterId={encounter.id} />
                </div>
                <div className="flex justify-end border-t pt-4">
                    <Button variant="secondary" onClick={onClose}>
                        Close
                    </Button>
                </div>
            </DialogContent>
        </Dialog>
    );
}
