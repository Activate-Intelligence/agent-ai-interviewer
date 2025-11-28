import os
import json
from ..validator.agent import AgentSchema
from ..utils.webhook import call_webhook_with_success, call_webhook_with_error
# from ..utils.temp_db import temp_data
from ..config.logger import Logger
from ..agent.base_agent import base_agent

logger = Logger()

def format_json_array_to_markdown(json_array):
    """
    Format the final JSON array response into markdown
    """
    output = []
    output.append("### Conversation Summary:")

    for item in json_array:
        if 'Agent' in item and 'Contribution' in item:
            output.append(f"# {item['Agent']}")
            output.append(f"{item['Contribution']}")
            output.append("-" * 60)  # Add a separator for better readability

    return '\n'.join(output)

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
            print(f"payload===>: {payload}")
            # Get payload data
            payload = payload.dict()
            inputs = {
                'id': payload.get('id'),
                'webhookUrl': payload.get('webhookUrl')
            }

            for item in payload.get('inputs', []):
                inputs[item.get('name')] = item.get('data')
            print("INPUTS ===>", inputs)

            # Call base_agent with the inputs
            resp, model_response, resp_id, is_final = base_agent(inputs)
            print(f"Response from base_agent: {resp}")
            print(f"Model response: {model_response}")
            print(f"Is final: {is_final}")

            # The history should only contain the response ID
            response_id_history = resp_id

            if is_final:
                # This is the final response (JSON array)
                try:
                    # Parse the JSON array
                    json_array = json.loads(model_response)
                    formatted_output = format_json_array_to_markdown(json_array)

                    # Send the final completed webhook with the formatted output
                    call_webhook_with_success(payload.get('id'),{
                        "status": 'completed',
                        "data": {
                            "info": "Task successfully completed!",
                            "title": "Interviewer - Story",
                            "output": {
                                "name": "output",
                                "type": "longText",
                                "data": formatted_output
                            }
                        }
                    })
                except json.JSONDecodeError:
                    logger.error("Expected JSON array for final response but couldn't parse it")
                    call_webhook_with_error(payload.get('id'),"Failed to parse final response as JSON", 500)
            else:
                # This is an ongoing conversation with a question
                call_webhook_with_success(payload.get('id'),{
                    "status": 'completed',
                    "data": {
                        "title": "Interviewer"
                    }
                })

                call_webhook_with_success(payload.get('id'),{
                    "status": 'completed',
                    "data": {
                        "info": "Continuing the interview",
                        "title": "Interviewer - Question",
                        "output": {
                            "name": "next_task_awaiting_input",
                            "type": "nextTaskAwaitingInput",
                            "data": [{
                                "nextTask": {
                                    "agentIdentifier": "Project_XYZ",
                                    "taskDetails": {
                                        "task": "Dialog",
                                        "inputs": [{
                                            "name": "history",
                                            "type": "text",
                                            "data": response_id_history  # Only pass the response ID
                                        }, {
                                            "name": "output",
                                            "type": "longtext",
                                            "data": model_response
                                        }]
                                    }
                                }
                            }]
                        }
                    }
                })

            logger.info('Function execute: Execution complete', resp)
            return {"result": resp, "isComplete": is_final}

        except Exception as e:
            logger.error('Getting Error in ExecuteController.execute:', e)
            raise call_webhook_with_error(payload.get('id'),str(e), 500)