"use client";

import { useState } from "react";

// Types
import { ClinicalDocumentAttachmentView } from "@/types/clinicalDocument";
import { Download, ZoomIn, ZoomOut } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
} from "@/components/ui/dialog";

import { documentViewerFactory } from "./viewers/factory";

interface DocumentViewerModalProps {
    document: ClinicalDocumentAttachmentView;
    open: boolean;
    onClose: () => void;
}

export function DocumentViewerModal({
    document,
    open,
    onClose,
}: DocumentViewerModalProps) {
    const [scale, setScale] = useState(1.0);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [paginationInfo, setPaginationInfo] = useState<{
        current: number;
        total: number;
    } | null>(null);

    // Get appropriate viewer using factory pattern
    const viewerConfig = documentViewerFactory.getViewer(document);
    const ViewerComponent = viewerConfig.component;
    const { supportsZoom, supportsPagination, requiresDownload } =
        viewerConfig.metadata;

    const handleLoadSuccess = () => {
        setLoading(false);
        setError(null);
    };

    const handleLoadError = (err: Error) => {
        setError(err.message || "Failed to load document");
        setLoading(false);
    };

    const handleDownload = () => {
        window.open(document.fileUrl, "_blank");
    };

    const handleZoomIn = () => setScale((prev) => Math.min(prev + 0.2, 3.0));
    const handleZoomOut = () => setScale((prev) => Math.max(prev - 0.2, 0.5));
    const handleResetZoom = () => setScale(1.0);

    return (
        <Dialog open={open} onOpenChange={onClose}>
            <DialogContent className="max-w-[95vw] w-[95vw] max-h-[95vh] h-[95vh] overflow-hidden flex flex-col">
                <DialogHeader className="flex-shrink-0">
                    <div className="flex justify-between items-start">
                        <div>
                            <DialogTitle>{document.title}</DialogTitle>
                            <div className="flex gap-2 mt-2 text-sm text-muted-foreground">
                                <span className="bg-slate-100 rounded px-2 py-0.5">
                                    {document.category.replace("_", " ")}
                                </span>
                                <span>
                                    {new Date(
                                        document.createdAt
                                    ).toLocaleDateString()}
                                </span>
                                <span>
                                    {(
                                        document.attachment.byteSize / 1024
                                    ).toFixed(1)}{" "}
                                    KB
                                </span>
                                <span className="text-xs text-slate-400">
                                    {document.attachment.mimeType}
                                </span>
                            </div>
                        </div>
                    </div>
                </DialogHeader>

                {/* Toolbar */}
                <div className="flex justify-center gap-2 py-2 border-b flex-shrink-0">
                    {supportsZoom && (
                        <>
                            <Button
                                variant="tertiary"
                                size="sm"
                                onClick={handleZoomOut}
                                disabled={scale <= 0.5}
                            >
                                <ZoomOut className="w-4 h-4" />
                            </Button>
                            <Button
                                variant="tertiary"
                                size="sm"
                                onClick={handleResetZoom}
                                disabled={scale === 1.0}
                                className="min-w-[60px]"
                            >
                                {Math.round(scale * 100)}%
                            </Button>
                            <Button
                                variant="tertiary"
                                size="sm"
                                onClick={handleZoomIn}
                                disabled={scale >= 3.0}
                            >
                                <ZoomIn className="w-4 h-4" />
                            </Button>
                        </>
                    )}

                    {supportsPagination && paginationInfo && (
                        <div className="ml-4 flex items-center gap-2 text-sm text-muted-foreground">
                            <span>
                                Page {paginationInfo.current} of{" "}
                                {paginationInfo.total}
                            </span>
                        </div>
                    )}

                    <div className="ml-auto">
                        <Button
                            variant="tertiary"
                            size="sm"
                            onClick={handleDownload}
                        >
                            <Download className="w-4 h-4 mr-1" />
                            Download
                        </Button>
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-auto p-4">
                    {loading && (
                        <p className="text-center text-muted-foreground">
                            Loading document...
                        </p>
                    )}
                    {error && (
                        <p className="text-center text-red-500">{error}</p>
                    )}

                    <ViewerComponent
                        document={document}
                        scale={scale}
                        onLoadSuccess={handleLoadSuccess}
                        onLoadError={handleLoadError}
                        {...(supportsPagination && {
                            onPageChange: (current: number, total: number) =>
                                setPaginationInfo({ current, total }),
                        })}
                    />
                </div>
            </DialogContent>
        </Dialog>
    );
}
