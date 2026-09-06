"use client";

import { Download } from "lucide-react";

import { Button } from "@/components/ui/button";

import { DocumentViewerProps } from "./types";

export function UnsupportedViewer({ document }: DocumentViewerProps) {
    const handleDownload = () => {
        if (document.fileUrl) {
            window.open(document.fileUrl, "_blank");
        }
    };

    return (
        <div className="text-center py-8">
            <p className="text-muted-foreground mb-4">
                Preview not available for{" "}
                {document.attachment.mimeType || "this file type"}.
            </p>
            <Button onClick={handleDownload}>
                <Download className="w-4 h-4 mr-2" />
                Download File
            </Button>
        </div>
    );
}

export const UnsupportedViewerMetadata = {
    supportsZoom: false,
    supportsPagination: false,
    requiresDownload: true,
};
