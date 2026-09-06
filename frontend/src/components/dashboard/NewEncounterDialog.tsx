"use client";

import { useState } from "react";

import { Plus } from "lucide-react";

import { EncounterForm } from "@/components/dashboard/EncounterForm";
import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";

import { useEncounterForm } from "@/hooks/useEncounterForm";

interface NewEncounterDialogProps {
    patientId: string;
    patientName?: string;
}

export function NewEncounterDialog({
    patientId,
    patientName,
}: NewEncounterDialogProps) {
    const [open, setOpen] = useState(false);
    const form = useEncounterForm({
        patientId,
        onSuccess: () => setOpen(false),
    });
    return (
        <Dialog
            open={open}
            onOpenChange={(isOpen) => {
                setOpen(isOpen);
                if (!isOpen) form.resetForm();
            }}
        >
            <DialogTrigger asChild>
                <Button>
                    <Plus className="h-4 w-4" />
                    New Encounter
                </Button>
            </DialogTrigger>
            <DialogContent className="max-h-[90vh] max-w-2xl overflow-y-auto">
                <DialogHeader>
                    <DialogTitle>Add Encounter</DialogTitle>
                    <DialogDescription>
                        Create an encounter record
                        {patientName ? ` for ${patientName}` : ""}.
                    </DialogDescription>
                </DialogHeader>
                <form onSubmit={form.handleSubmit}>
                    <EncounterForm
                        formData={form.formData}
                        onChange={form.updateField}
                        error={form.error}
                    />
                    <DialogFooter className="mt-6">
                        <Button
                            type="button"
                            variant="secondary"
                            onClick={() => setOpen(false)}
                            disabled={form.loading}
                        >
                            Cancel
                        </Button>
                        <Button
                            type="submit"
                            isLoading={form.loading}
                            loadingText="Creating"
                        >
                            Create Encounter
                        </Button>
                    </DialogFooter>
                </form>
            </DialogContent>
        </Dialog>
    );
}
