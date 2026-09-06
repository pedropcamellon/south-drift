"use client";

import { useState } from "react";

// Types
import { ClinicalDocument } from "@/types/clinicalDocument";
import { AlertTriangle, Trash2 } from "lucide-react";

import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
} from "@/components/ui/alert-dialog";

interface DeleteDocumentDialogProps {
    document: ClinicalDocument | null;
    open: boolean;
    onClose: () => void;
    onConfirm: () => Promise<void>;
}

export function DeleteDocumentDialog({
    document,
    open,
    onClose,
    onConfirm,
}: DeleteDocumentDialogProps) {
    const [isDeleting, setIsDeleting] = useState(false);
    const attachment = document?.attachments[0];

    const handleConfirm = async () => {
        setIsDeleting(true);
        try {
            await onConfirm();
            onClose();
        } catch (error) {
            console.error("Delete failed:", error);
        } finally {
            setIsDeleting(false);
        }
    };

    if (!document) return null;

    return (
        <AlertDialog open={open} onOpenChange={onClose}>
            <AlertDialogContent>
                <AlertDialogHeader>
                    <div className="flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-red-500" />
                        <AlertDialogTitle>Delete Document</AlertDialogTitle>
                    </div>
                    <AlertDialogDescription className="space-y-2">
                        <p>
                            Are you sure you want to delete this document? This
                            action cannot be undone.
                        </p>
                        <div className="bg-slate-50 rounded p-3 mt-2">
                            <p className="font-medium text-sm text-slate-900">
                                {document.title}
                            </p>
                            <p className="text-xs text-slate-500 mt-1">
                                Category: {document.category.replace("_", " ")}{" "}
                                •{" "}
                                {new Date(
                                    document.createdAt
                                ).toLocaleDateString()}
                            </p>
                            {attachment && (
                                <p className="text-xs text-slate-500">
                                    File: {attachment.fileName}
                                </p>
                            )}
                        </div>
                    </AlertDialogDescription>
                </AlertDialogHeader>
                <AlertDialogFooter>
                    <AlertDialogCancel disabled={isDeleting}>
                        Cancel
                    </AlertDialogCancel>
                    <AlertDialogAction
                        onClick={handleConfirm}
                        disabled={isDeleting}
                        className="bg-red-500 hover:bg-red-600"
                    >
                        <Trash2 className="w-4 h-4 mr-2" />
                        {isDeleting ? "Deleting..." : "Delete Document"}
                    </AlertDialogAction>
                </AlertDialogFooter>
            </AlertDialogContent>
        </AlertDialog>
    );
}
