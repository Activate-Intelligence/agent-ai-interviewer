import os
import json
from ..validator.agent import AgentSchema
from ..utils.webhook import call_webhook_with_success, call_webhook_with_error
# from ..utils.temp_db import temp_data
from ..config.logger import Logger
from ..agent.base_agent import base_agent

logger = Logger()


class ExecuteController:
    """
    This class represents the controller for executing a task.
    """

    def execute(self, payload: AgentSchema) -> dict:
        """
        Executes the task using the provided payload.

        Args:
          payload (AgentSchema): The payload containing the data for the task.

        Returns:
          dict: The result of the task execution.

        Raises:
          Exception: If an error occurs during task execution.
        """

        try:
            logger.info('ExecuteController.execute() method called')
            # Get payload data
            payload = payload.dict()
            inputs = {'id': payload.get(
                'id'), 'webhookUrl': payload.get('webhookUrl')}

            for item in payload.get('inputs', []):
                inputs[item.get('name')] = item.get('data')

            # Here you can write your agent logic.
            # You can use the payload data to perform your task.
            resp, collection_id, block_id, metadata, processed_content, block_content_type = base_agent(inputs)


            # Call webhook with success
            call_webhook_with_success(payload.get('id'),{
                "status": 'completed',
                "data": {
                    "info": "Task successfully completed!",
                    "title": "Gimlet Collection Generated",
                    "output": resp
                }
            })

            logger.info('Function execute: Execution complete', resp)
            print({"result": resp, "collectionID": collection_id, "parentBlockId": block_id, "metadata": metadata, "blockContentOutput": processed_content, "blockContentType": block_content_type})

            return {"result": resp, "collectionID": collection_id, "parentBlockId": block_id, "metadata": metadata, "blockContentOutput": processed_content, "blockContentType": block_content_type}
        except Exception as e:
            logger.error('Getting Error in ExecuteController.execute:', e)
            raise call_webhook_with_error(payload.get('id'),str(e), 500)
