"""Database seeding runner script.

Run with: python -m app.seed_db
"""

import asyncio

from app.core.database import async_session_maker, create_db_and_tables
from app.seed import (
    seed_clinical_documents,
    seed_diagnostic_reports,
    seed_encounters,
    seed_imaging_studies,
    seed_patients,
    seed_users,
)
from app.services.storage import get_storage


async def main():
    """Create tables and seed all data."""
    print("Creating database tables...")
    await create_db_and_tables()

    print("\nSeeding database...")

    # Seed users
    async with async_session_maker() as session:
        await seed_users(session)

    # Seed patients, encounters, and documents
    async with async_session_maker() as session:
        print("[DEBUG seed_db] Calling seed_patients...")
        patients = await seed_patients(session)
        print(f"[DEBUG seed_db] seed_patients returned {len(patients) if patients else 0} patients")
        print(f"[DEBUG seed_db] patients is: {patients}")
        print(f"[DEBUG seed_db] bool(patients) = {bool(patients)}")

        if patients:
            print("[DEBUG seed_db] Patients exist, calling seed_encounters...")
            await seed_encounters(session, patients)
            print("[DEBUG seed_db] Calling seed_diagnostic_reports...")
            await seed_diagnostic_reports(session, patients)
            await seed_imaging_studies(session, patients)
            print("[DEBUG seed_db] Calling seed_clinical_documents...")
            storage = await get_storage()
            await seed_clinical_documents(session, storage, patients)
        else:
            print("[DEBUG seed_db] No patients found, skipping encounters and documents")

    print("\nDatabase seeding complete!")


if __name__ == "__main__":
    asyncio.run(main())
