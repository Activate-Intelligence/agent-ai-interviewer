# from ..utils.temp_db import temp_data
from ..config.logger import Logger
from ..utils.webhook import call_webhook_with_error, call_webhook_with_success
from openai import OpenAI
import openai
from .prompt_extract import extract_prompts
import os
from datetime import datetime
from .get_prompt_from_git import main as promptDownloader
import json
from .agent_config import fetch_agent_config


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


def llm(context, inquiry):
    prompt_file_path = get_prompt_file_path()
    replacements = {"context": context, "inquiry": inquiry}
    system_prompt, user_prompt, model_params= extract_prompts(prompt_file_path,
                                                 **replacements)
    print("---"*30)
    print(f"system_prompt: {system_prompt}, user_prompt: {user_prompt}, model_params: {model_params}")
    print("---"*30)
    
    try:
        response = client.responses.create(
            model=model_params['name'],
            input=[
                {
                    "role": "system",
                    "content": system_prompt
                },
                {
                    "role": "user",
                    "content": user_prompt  
                },
            ],
            temperature=model_params['temperature'])

        # Extracting and cleaning the GPT response
        result = response.output_text
        return result
    except Exception as e:
        print(f"Error calling OpenAI API: {e}")
        return None

    
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
        
        # Get agent configuration
        agent_config_doc = fetch_agent_config()
        print(f"the agent config: {agent_config_doc}")
        agent_name = agent_config_doc.get('name', 'UnknownAgent')

        # Generate request ID
        request_id = payload.get(
            'request_id', f"req-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        print(f"Request ID: {request_id}")

    
        selected_text = payload.get("selectedText")
        instructions = payload.get("instructions")
        result = llm(selected_text, instructions)
        
        call_webhook_with_success(
            payload.get('id'), {
            "status": "inprogress",
            "data": {
                "title": f"Fetching the inputs",
                "info": "Processing",
            },
        })

        resp = {"name": "result", "type": "markdown", "data": result}

        call_webhook_with_success(payload.get('id'), {
            "status": "inprogress",
            "data": {
                "title": f"Check your revised text",
                "info": "Check the result",
            },
        })

        return resp
        
        
    except Exception as e:
        print(f"Error in base_agent_mojito: {e}")
        # raise call_webhook_with_error(str(e), 500) # OLD VERSION SINGLE THREADED
        call_webhook_with_error(payload.get('id'), str(e), 500) # MULTI THREADED