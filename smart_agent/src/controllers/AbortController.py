import os
import time

from ..utils.temp_db import get_job, remove_job, update_job_fields
from ..utils.error_handling import error_handler
from ..config.logger import Logger

logger = Logger()


class AbortController:
    """
    The `AbortController` class provides methods to control the execution flow and stop the execution.
    """

    @classmethod
    def execution_abort(cls, job_id: str) -> dict:
        """
        Stops the execution and returns a success message.
        """
        try:
            logger.info("AbortController.execution_abort() called for %s", job_id)
            job = get_job(job_id)

            if not job:
                return {"result": f"No running execution with id {job_id}", "status": "not_found"}

            # Mark as aborted immediately so capacity frees up
            try:
                update_job_fields(job_id, {
                    "status": "aborted",
                    "isExecutionContinue": False,
                    "updated_at": int(time.time())
                })
            except Exception:
                # Non-fatal; we still attempt removal
                pass

            # Attempt to remove the job record (best-effort)
            removed = remove_job(job_id)
            if removed:
                logger.info("Removed job %s after abort", job_id)
            else:
                logger.warning("Failed to remove job %s after abort; status set to aborted", job_id)

            return {"result": f"Execution {job_id} stopped successfully", "status": "success"}

        except Exception as e:
            logger.error('Error in AbortController.execution_abort: %s', e)
            raise error_handler(e, 500)
