"""Clear the synthetic patient-owned clinical graph from development data."""

import asyncio

from sqlalchemy import delete

from app.core.database import async_session_maker
from app.models.db import Patient


async def main():
    """Clear patients and database-cascaded clinical records, retaining users."""
    async with async_session_maker() as session:
        await session.execute(delete(Patient))
        await session.commit()
        print("Cleared synthetic patients and patient-owned clinical records")


if __name__ == "__main__":
    asyncio.run(main())
