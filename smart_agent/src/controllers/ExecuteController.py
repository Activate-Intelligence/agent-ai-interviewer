import os
import json
from ..validator.agent import AgentSchema
from ..utils.webhook import call_webhook_with_success, call_webhook_with_error
from ..config.logger import Logger
from ..agent.base_agent import base_agent

logger = Logger()


class ExecuteController:
    """
    Controller for executing the Client Discovery Interview agent.
    Implements the Daiquiri pattern for multi-turn conversations.
    """

    def execute(self, payload: AgentSchema) -> dict:
        """
        Executes the interview task using the provided payload.

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
            print(f"payload -> {payload}")

            # Prepare inputs
            inputs = {
                'id': payload.get('id'),
                'webhookUrl': payload.get('webhookUrl')
            }

            # Extract all inputs from the payload
            for item in payload.get('inputs', []):
                inputs[item.get('name')] = item.get('data')

            # Call the base agent (Daiquiri pattern)
            resp, model_response, response_id, is_complete, summary = base_agent(inputs)

            # Determine completion status and prepare webhook response
            if is_complete:
                # Conversation is complete - send completed status
                call_webhook_with_success(payload.get('id'), {
                    "status": "completed",
                    "data": {
                        "info": "Discovery interview completed!",
                        "output": {
                            "name": "output",
                            "type": "longText",
                            "data": model_response
                        }
                    }
                })
            else:
                # Conversation continues - signal next task awaiting input
                call_webhook_with_success(payload.get('id'), {
                    "status": "completed",
                    "data": {
                        "output": {
                            "name": "next_task_awaiting_input",
                            "type": "nextTaskAwaitingInput",
                            "data": [{
                                "nextTask": {
                                    "agentIdentifier": "Client Discovery Interview",
                                    "taskDetails": {
                                        "inputs": [
                                            {
                                                "name": "history",
                                                "data": response_id
                                            },
                                            {
                                                "name": "output",
                                                "data": model_response
                                            }
                                        ]
                                    }
                                }
                            }]
                        }
                    }
                })

            logger.info('Function execute: Execution complete', {
                "response": model_response[:100] if model_response else "",
                "is_complete": is_complete
            })

            return {
                "result": resp,
                "isComplete": is_complete,
                "history": response_id,
                "summary": summary
            }

        except Exception as e:
            logger.error('Error in ExecuteController.execute:', e)
            call_webhook_with_error(payload.get('id'), str(e), 500)
            raise
