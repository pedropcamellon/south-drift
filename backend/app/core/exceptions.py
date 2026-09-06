"""Core utilities - Custom exceptions"""

from fastapi import HTTPException, status


class PatientNotFoundError(HTTPException):
    """Raised when a patient is not found"""

    def __init__(self, patient_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Patient with ID {patient_id} not found"
        )


class EncounterNotFoundError(HTTPException):
    """Raised when an encounter is not found."""

    def __init__(self, encounter_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Encounter with ID {encounter_id} not found",
        )


class DocumentNotFoundError(HTTPException):
    """Raised when a document is not found"""

    def __init__(self, document_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Document with ID {document_id} not found",
        )


class ClinicalDocumentNotFoundError(HTTPException):
    """Raised when a clinical document or its attachment is not found."""

    def __init__(self, document_id: str):
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Clinical document with ID {document_id} not found",
        )


class BlobStorageError(HTTPException):
    """Raised when blob storage operations fail"""

    def __init__(self, message: str = "Blob storage operation failed"):
        super().__init__(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=message)


class AIServiceError(HTTPException):
    """Raised when AI service operations fail"""

    def __init__(self, service: str, message: str = "AI service operation failed"):
        super().__init__(status_code=status.HTTP_502_BAD_GATEWAY, detail=f"{service}: {message}")
