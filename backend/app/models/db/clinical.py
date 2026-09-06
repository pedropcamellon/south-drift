"""Clinical persistence primitives with explicit ownership and provenance."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base

if TYPE_CHECKING:
    from app.models.db.patient import Patient


class Encounter(Base):
    __tablename__ = "encounter"
    __table_args__ = (
        CheckConstraint(
            "ended_at IS NULL OR ended_at >= started_at",
            name="ck_encounter_time_range",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patient.id", ondelete="CASCADE"), nullable=False, index=True
    )
    encounter_type: Mapped[str] = mapped_column(String(30), nullable=False)
    purpose: Mapped[str] = mapped_column(String(30), nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    ended_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    location: Mapped[str | None] = mapped_column(String(200), nullable=True)
    clinician_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    clinician_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    audio_metadata: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    structured_summary: Mapped[dict[str, object] | None] = mapped_column(JSON, nullable=True)
    chief_complaint: Mapped[str | None] = mapped_column(Text, nullable=True)
    clinical_assessment: Mapped[str | None] = mapped_column(Text, nullable=True)
    treatment_plan: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_compliant: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_by: Mapped[str] = mapped_column(String(100), nullable=False, default="system")
    updated_by: Mapped[str | None] = mapped_column(String(100), nullable=True)
    prior_encounter_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("encounter.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=True,
    )

    patient: Mapped["Patient"] = relationship("Patient", back_populates="encounters")
    narratives: Mapped[list["EncounterNarrative"]] = relationship(
        back_populates="encounter", cascade="all, delete-orphan"
    )


class EncounterNarrative(Base):
    __tablename__ = "encounter_narrative"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patient.id", ondelete="CASCADE"), nullable=False, index=True
    )
    encounter_id: Mapped[UUID] = mapped_column(
        ForeignKey("encounter.id", ondelete="CASCADE"), nullable=False, index=True
    )
    content: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    encounter: Mapped["Encounter"] = relationship(back_populates="narratives")


class ClinicalDocument(Base):
    __tablename__ = "clinical_document"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patient.id", ondelete="CASCADE"), nullable=False, index=True
    )
    encounter_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("encounter.id", ondelete="SET NULL"), nullable=True, index=True
    )
    category: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    authored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    attachments: Mapped[list["Attachment"]] = relationship(
        back_populates="clinical_document", cascade="all, delete-orphan"
    )


class Attachment(Base):
    __tablename__ = "attachment"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    clinical_document_id: Mapped[UUID] = mapped_column(
        ForeignKey("clinical_document.id", ondelete="CASCADE"), nullable=False, index=True
    )
    storage_key: Mapped[str] = mapped_column(String(500), unique=True, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    mime_type: Mapped[str] = mapped_column(String(100), nullable=False)
    byte_size: Mapped[int] = mapped_column(Integer, nullable=False)
    checksum: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    clinical_document: Mapped["ClinicalDocument"] = relationship(back_populates="attachments")


class DiagnosticReport(Base):
    __tablename__ = "diagnostic_report"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patient.id", ondelete="CASCADE"), nullable=False, index=True
    )
    originating_encounter_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("encounter.id", ondelete="SET NULL"), nullable=True, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    issued_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    conclusion: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    observations: Mapped[list["Observation"]] = relationship(
        back_populates="diagnostic_report", cascade="all, delete-orphan"
    )


class Observation(Base):
    __tablename__ = "observation"
    __table_args__ = (
        CheckConstraint(
            "(value IS NULL) != (data_absent_reason IS NULL)",
            name="ck_observation_value_or_absence_reason",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patient.id", ondelete="CASCADE"), nullable=False, index=True
    )
    diagnostic_report_id: Mapped[UUID] = mapped_column(
        ForeignKey("diagnostic_report.id", ondelete="CASCADE"), nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(String(30), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(200), nullable=False)
    display: Mapped[str] = mapped_column(String(200), nullable=False)
    value_type: Mapped[str] = mapped_column(String(30), nullable=False)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(100), nullable=True)
    data_absent_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    effective_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )

    diagnostic_report: Mapped["DiagnosticReport"] = relationship(back_populates="observations")


class ImagingStudy(Base):
    __tablename__ = "imaging_study"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    patient_id: Mapped[UUID] = mapped_column(
        ForeignKey("patient.id", ondelete="CASCADE"), nullable=False, index=True
    )
    originating_encounter_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("encounter.id", ondelete="SET NULL"), nullable=True, index=True
    )
    clinical_document_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("clinical_document.id", ondelete="SET NULL"), nullable=True, index=True
    )
    diagnostic_report_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("diagnostic_report.id", ondelete="SET NULL"), nullable=True, index=True
    )
    modality: Mapped[str] = mapped_column(String(30), nullable=False)
    performed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    external_study_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )


class ClinicalProvenance(Base):
    __tablename__ = "clinical_provenance"
    __table_args__ = (
        UniqueConstraint("resource_type", "resource_id", "version", name="uq_provenance_version"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    resource_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    source_system: Mapped[str | None] = mapped_column(String(100), nullable=True)
    external_id: Mapped[str | None] = mapped_column(String(200), nullable=True)
    authored_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    received_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    recorded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    author_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    recorder_id: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[str] = mapped_column(String(100), nullable=False, default="1")


class ResourceRelationship(Base):
    __tablename__ = "resource_relationship"
    __table_args__ = (
        UniqueConstraint(
            "source_resource_type",
            "source_resource_id",
            "target_resource_type",
            "target_resource_id",
            "relationship_type",
            name="uq_resource_relationship",
        ),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    source_resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    source_resource_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    target_resource_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    target_resource_id: Mapped[UUID] = mapped_column(nullable=False, index=True)
    relationship_type: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
