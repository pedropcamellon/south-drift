"""Patient database model (SQLAlchemy)."""

from datetime import UTC, datetime
from typing import TYPE_CHECKING
from uuid import UUID, uuid4

from sqlalchemy import Date, DateTime, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base

if TYPE_CHECKING:
    from app.models.db.clinical import (
        ClinicalDocument,
        DiagnosticReport,
        Encounter,
        ImagingStudy,
        Observation,
    )


class Patient(Base):
    """Patient model for database persistence."""

    __tablename__ = "patient"

    # Primary key
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)

    # Required fields
    medical_record_number: Mapped[str] = mapped_column(
        String(50), unique=True, index=True, nullable=False
    )
    first_name: Mapped[str] = mapped_column(String(100), nullable=False)
    last_name: Mapped[str] = mapped_column(String(100), nullable=False)
    date_of_birth: Mapped[datetime] = mapped_column(Date, nullable=False)
    gender: Mapped[str] = mapped_column(String(20), nullable=False)
    contact_info: Mapped[str] = mapped_column(String(200), nullable=False)

    # Optional fields
    email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    address: Mapped[str | None] = mapped_column(String(500), nullable=True)
    emergency_contact: Mapped[str | None] = mapped_column(String(200), nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(UTC), nullable=False
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(UTC),
        onupdate=lambda: datetime.now(UTC),
        nullable=True,
    )

    # Relationships
    encounters: Mapped[list["Encounter"]] = relationship(cascade="all, delete-orphan")
    clinical_documents: Mapped[list["ClinicalDocument"]] = relationship(
        cascade="all, delete-orphan"
    )
    diagnostic_reports: Mapped[list["DiagnosticReport"]] = relationship(
        cascade="all, delete-orphan"
    )
    observations: Mapped[list["Observation"]] = relationship(cascade="all, delete-orphan")
    imaging_studies: Mapped[list["ImagingStudy"]] = relationship(cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<Patient(id={self.id}, mrn={self.medical_record_number}, name={self.first_name} {self.last_name})>"
