import { ClinicalDocumentAttachmentView } from "@/types/clinicalDocument";

export interface DocumentViewerProps {
    document: ClinicalDocumentAttachmentView;
    scale: number;
    onLoadSuccess?: () => void;
    onLoadError?: (error: Error) => void;
}

export abstract class DocumentViewerHandler {
    abstract canHandle(mimeType: string): boolean;
    abstract getComponent(): React.ComponentType<DocumentViewerProps>;
    abstract getSupportedMimeTypes(): string[];
}

export interface ViewerMetadata {
    supportsZoom: boolean;
    supportsPagination: boolean;
    requiresDownload: boolean;
}
