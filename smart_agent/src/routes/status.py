from fastapi import APIRouter, Query
from ..controllers.StatusController import StatusController
from ..validator.status import ApiResponse

# prefix="/discover",
router = APIRouter(tags=['Agent Status'])

# Simple health check endpoint for ALB (no parameters required)
@router.get('/status')
def health_check():
  return {"status": "healthy", "service": "agent"}

# Task-specific status endpoint (requires ID parameter)
@router.get('/status/{task_id}', response_model=ApiResponse)
def get_task_status(task_id: str):
  return StatusController.get_status(task_id)

# Legacy endpoint with query parameter (for backward compatibility)
@router.get('/task-status', response_model=ApiResponse)
def discover(id: str = Query(..., description="Task ID")):
  return StatusController.get_status(id)

