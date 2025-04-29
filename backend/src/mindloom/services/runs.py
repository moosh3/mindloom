import uuid
from datetime import datetime
from typing import Optional, Dict, Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from mindloom.app.models.run import RunORM, RunStatus
# TODO: Adjust if your Pydantic create schema is named differently or located elsewhere
# from mindloom.app.schemas.run import RunCreate 

class RunService:
    """Service layer for Run related operations."""

    async def create_run(
        self,
        db: AsyncSession,
        *,
        runnable_id: uuid.UUID,
        runnable_type: str,
        input_variables: Optional[Dict[str, Any]] = None,
        user_id: Optional[uuid.UUID] = None # Optional: if you track which user initiated the run
    ) -> RunORM:
        """
        Creates a new run record in the database with PENDING status.

        Args:
            db: The AsyncSession for database interaction.
            runnable_id: The UUID of the agent or team being run.
            runnable_type: The type of runnable ('agent' or 'team').
            input_variables: The input data for the run.
            user_id: The ID of the user initiating the run (optional).

        Returns:
            The created RunORM object.
        """
        db_run = RunORM(
            runnable_id=runnable_id,
            runnable_type=runnable_type,
            input_variables=input_variables,
            user_id=user_id,
            status=RunStatus.PENDING, # Initial status
            created_at=datetime.utcnow()
        )
        db.add(db_run)
        await db.commit()
        await db.refresh(db_run)
        return db_run

    async def get_run(self, db: AsyncSession, run_id: uuid.UUID) -> Optional[RunORM]:
        """
        Fetches a specific run by its ID.

        Args:
            db: The AsyncSession for database interaction.
            run_id: The UUID of the run to fetch.

        Returns:
            The RunORM object if found, otherwise None.
        """
        result = await db.execute(select(RunORM).where(RunORM.id == run_id))
        return result.scalars().first()

    async def update_run_status(
        self,
        db: AsyncSession,
        run_id: uuid.UUID,
        status: RunStatus,
        output_data: Optional[Dict[str, Any]] = None
    ) -> Optional[RunORM]:
        """
        Updates the status and potentially the output of a run.
        Sets started_at or ended_at timestamps based on the status.

        Args:
            db: The AsyncSession for database interaction.
            run_id: The UUID of the run to update.
            status: The new RunStatus.
            output_data: The output data (for COMPLETED) or error info (for FAILED).

        Returns:
            The updated RunORM object if found and updated, otherwise None.
        """
        run = await self.get_run(db, run_id)
        if not run:
            return None # Or raise an exception

        run.status = status
        now = datetime.utcnow()

        if status == RunStatus.RUNNING and not run.started_at:
            run.started_at = now
        elif status in [RunStatus.COMPLETED, RunStatus.FAILED, RunStatus.CANCELLED]:
            if not run.started_at: # Should have been set when RUNNING, but set JIC
                 run.started_at = now
            run.ended_at = now
            run.output_data = output_data # Store output/error

        db.add(run) # Add the modified object to the session
        await db.commit()
        await db.refresh(run)
        return run

# You might want a singleton instance or use dependency injection
run_service = RunService()
