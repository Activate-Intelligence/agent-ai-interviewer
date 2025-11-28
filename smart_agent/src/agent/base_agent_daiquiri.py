# from ..utils.temp_db import temp_data
from ..config.logger import Logger
from ..utils.webhook import call_webhook_with_error, call_webhook_with_success
from openai import OpenAI
import os
import json
import yaml
from .prompt_extract import extract_prompts
from .get_prompt_from_git import main as promptDownloader

logger = Logger()

# Configuration flag - Change this to switch between dev and prod modes
ENVIRONMENT_MODE = "dev"  # Change to "prod" for production or dev for development

openai_api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

def get_environment_mode():
    """Get the current environment mode (dev or prod)"""
    return ENVIRONMENT_MODE.lower()

def get_prompt_file_path():
    """Get the appropriate prompt file path based on environment mode"""
    mode = get_environment_mode()
    
    if mode == "dev":
        # In dev mode, try /tmp/Prompt first, fallback to Prompt
        tmp_prompt_path = '/tmp/Prompt/GimletGPT.yaml'
        if os.path.exists(tmp_prompt_path):
            return tmp_prompt_path
        else:
            return 'Prompt/GimletGPT.yaml'
    else:
        # In prod mode, only use Prompt folder
        return 'Prompt/GimletGPT.yaml'



def interviewer(user_input, conversation="", previous_response_id=None):
    """
    Function to handle the interview process
    - For new conversations: creates a new chat with system prompt and user input
    - For continuing conversations: uses the previous_response_id with only user input

    Returns: question text, response ID, and whether this is the final response
    """
    prompt_file_path = get_prompt_file_path()
    filename = prompt_file_path.split('/')[-1]

    # Set up replacements dictionary
    replacements = {"answer": user_input}

    if previous_response_id:
        # For continuing conversations, we only need the user prompt
        # Extract just the user prompt with the replacements
        _, user_prompt, model_params = extract_prompts(prompt_file_path, **replacements)

        # Continue existing conversation using just the response ID
        response = client.responses.create(
            model=model_params['model'],
            text={
                "format": {
                    "type": "text"  # Use text format for questions
                }
            },
            input=[{
                "role": "user",
                "content": user_prompt
            }],
            temperature=model_params['temperature'],
            store=True,
            metadata={
                "project": "Project_XYZZ",
                "agent": "XYZZ",
                "prompt": filename
            },
            previous_response_id=previous_response_id)
    else:
        # For new conversations, extract both system and user prompts
        system_prompt, user_prompt, model_params = extract_prompts(prompt_file_path,
                                                     **replacements)

        # Start a new conversation with both system and user prompts
        response = client.responses.create(
            model=model_params['model'],
            text={
                "format": {
                    "type": "text"  # Use text format for questions
                }
            },
            input=[{
                "role": "system",
                "content": system_prompt
            }, {
                "role": "user",
                "content": user_prompt
            }],
            temperature=model_params['temperature'],
            store=True,
            metadata={
                "project": "Project_XYZ",
                "agent": "XYZ",
            })

    # Extract the response text and ID
    result = response.output_text
    resp_id = response.id

    print("response:", response)

    # Check if the response is a JSON array (indicating it's the final response)
    is_final = False
    try:
        # Try to parse as JSON to see if it's the final response
        json_data = json.loads(result)
        if isinstance(json_data, list):
            is_final = True
    except json.JSONDecodeError:
        # Not JSON, so it's a regular question
        pass

    return result, resp_id, is_final


def base_agent(payload):
    try:
        # Check environment mode
        mode = get_environment_mode()
        print(f"Running in {mode} mode")
        
        # Download the latest prompt files only in dev mode
        if mode == "dev":
            print("Dev mode: Downloading latest prompt files")
            # promptDownloader()
        else:
            print("Prod mode: Skipping prompt download")

        # Extract data from payload
        user_input = payload.get("userInput", "")
        previous_response_id = payload.get(
            "history", "")  # This now directly contains the response ID

        # Call the interviewer function
        model_response, resp_id, is_final = interviewer(
            user_input, previous_response_id=previous_response_id)

        # For tracking on our side, we'll maintain the conversation
        conversation = ""

        # If we have a model response and it's not the final one, add it to our tracking
        if model_response and not is_final:
            conversation += f"Q: {model_response}\n"

        # Prepare the response for the controller
        # Note: The conversation is just for logging, not for passing back as history
        resp = {
            "name": "output",
            "type": "markdown",
            "data": f"{conversation}"
        }

        # Return the response ID directly (not as part of a conversation string)
        return resp, model_response, resp_id, is_final

    except Exception as e:
        logger.error('Error in base_agent:', e)
        # raise call_webhook_with_error(str(e), 500) # OLD VERSION SINGLE THREADED
        call_webhook_with_error(payload.get('id'), str(e), 500) # MULTI THREADED
