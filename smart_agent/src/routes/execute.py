from fastapi import APIRouter
from queue import Queue, Empty
from threading import Thread
from dotenv import load_dotenv

# Relative imports
from ..controllers.ExecuteController import ExecuteController
from ..controllers.StatusController import StatusController
from ..validator.agent import ApiResponse, AgentSchema
from ..utils.temp_db import add_job
from ..utils.helper import update_task_status

import os
import time

load_dotenv()

router = APIRouter(tags=['Agent execution'])


def _execute_worker(request_data: dict, result_q: Queue):
    schema = AgentSchema(**request_data)
    try:
        res = ExecuteController().execute(schema)
    except Exception as e:
        res = {"status": "error", "message": str(e)}
    finally:
        result_q.put(res)


@router.post('/execute', response_model=ApiResponse)
def execute_agent(request: AgentSchema):
    # 1. capacity check
    status = StatusController().can_execute()
    if status['status'] != 'available':
        return {'result': status}

    # 2. Register job in DynamoDB immediately so status is visible
    job_record = {
        'id': request.id,
        'webhookUrl': request.webhookUrl,
        'pid': os.getpid(),
        'status': 'inprogress',
        'timestamp': int(time.time()),
        'isExecutionContinue': True,
        'agent_name': os.getenv('AGENT_NAME', ''),
        'agent_type': os.getenv('AGENT_TYPE', ''),
        'environment': os.getenv('ENVIRONMENT', '')
    }
    add_job(job_record)

    # 3. prepare the thread-safe queue and worker (after we persist the job)
    result_q = Queue()
    thread = Thread(target=_execute_worker, args=(request.dict(), result_q))
    thread.start()

    # 4. Wait for the thread to finish
    thread.join()

    # 5. Retrieve result from queue
    try:
        result = result_q.get_nowait()
    except Empty:
        result = {
            "status": "error",
            "message": "No response received from thread worker."
        }

    # 6. Persist final status instead of deleting the job
    try:
        final_status = result.get("status", "completed") if isinstance(result, dict) else "completed"
        final_data = result.get("data", result) if isinstance(result, dict) else {"result": result}
        update_task_status(str(request.id), final_status, final_data)
    except Exception:
        # Best-effort; avoid breaking the response on persistence issues
        pass

    return result
