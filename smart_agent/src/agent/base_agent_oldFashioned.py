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
        tmp_prompt_path = '/tmp/Prompt/CZP_MCP_Server_Prompt.yaml'
        if os.path.exists(tmp_prompt_path):
            return tmp_prompt_path
        else:
            return 'Prompt/CZP_MCP_Server_Prompt.yaml'
    else:
        # In prod mode, only use Prompt folder
        return 'Prompt/CZP_MCP_Server_Prompt.yaml'


def llm(input, instructions, thread_id=None):
    prompt_file_path = get_prompt_file_path()
    filename = prompt_file_path.split('/')[-1]

    text_value = "the text has been passed in the previous message" if thread_id else input

    # Create the basic replacements dictionary
    replacements = {
        "text": instructions
    }

    # Add original_text to replacements if provided
    # if original_text is not None:
    #     replacements["original_input"] = original_text

    tools=[
                {
                "type": "mcp",
                "server_label": "czp",
                "server_url": "https://1wvvwl22c1.execute-api.eu-central-1.amazonaws.com/prod/mcp",
                "allowed_tools": [
                    "parliamentary_analysis",
                    "search_documents",
                    "execute_cypher_query",
                    "get_database_info",
                    "format_update_email",
                    "update_prompts_cache"
                ],
                "require_approval": "never"
                }
            ]
    
    # Extract prompts
    system_prompt, user_prompt, model_params = extract_prompts(prompt_file_path, **replacements)
    print(system_prompt)
    print(user_prompt)

    if thread_id:
        # For continuing conversations, use only user prompt with previous_response_id
        response = client.responses.create(
            model=model_params['name'],
            text={
                "verbosity": model_params['verbosity'],
            },
            reasoning={
                "effort": model_params['effort'],
                "summary": "detailed"
            },
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            tools=tools,
            store=True,
            metadata={
                "project": "OldFashioned",
                "agent": "Old Fashioned - CZP MCP Server",
                "prompt": filename,
            },
            previous_response_id=thread_id
        )
    else:
        # For new conversations, use both system and user prompts
        response = client.responses.create(
            model=model_params['name'],
            text={
                "verbosity": model_params['verbosity'],
            },
            reasoning={
                "effort": model_params['effort'],
                "summary": "detailed"
            },
            input=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            tools=tools,
            store=True,
            metadata={
                "project": "OldFashioned",
                "agent": "Old Fashioned - CZP MCP Server",
                "prompt": filename,
            }
        )

    # Extracting and cleaning the GPT response
    print(f"the response from the llm is: {response}")
    result = response.output_text

    # 2) Reasoning summary (human-readable)
    all_summary_texts = []
    print(f"Response output items: {len(getattr(response, 'output', []))}")

    for i, item in enumerate(getattr(response, "output", [])):
        print(f"Item {i}: type={getattr(item, 'type', None)}, has_summary={hasattr(item, 'summary')}")
        if getattr(item, "type", None) == "reasoning":
            summary_parts = getattr(item, "summary", None) or []
            print(f"Found reasoning item {i} with {len(summary_parts)} summary parts")

            if summary_parts:  # Only process if there are actual parts
                # concatenate any summary_text parts from this reasoning item
                texts = []
                for j, part in enumerate(summary_parts):
                    part_type = getattr(part, "type", None)
                    part_text = getattr(part, "text", "")
                    print(f"  Part {j}: type={part_type}, text_length={len(part_text)}")
                    if part_type == "summary_text" and part_text:
                        texts.append(part_text)

                if texts:
                    item_summary = "\n".join(texts)
                    all_summary_texts.append(item_summary)
                    print(f"Extracted summary from reasoning item {i}, length: {len(item_summary)}")
                else:
                    print(f"  No valid summary_text parts found in reasoning item {i}")
            else:
                print(f"  Reasoning item {i} has empty summary")

    # Combine all summary texts from all reasoning items
    summary_text = "\n\n".join(all_summary_texts) if all_summary_texts else None
    print(f"Final combined summary text length: {len(summary_text) if summary_text else 0}")
        
    # result = json.loads(result)

    return result, summary_text, response.id


    
def base_agent(payload):
    try:

        # Check environment mode
        mode = get_environment_mode()
        print(f"Running in {mode} mode")
        
        # Download the latest prompt files only in dev mode
        if mode == "dev":
            print("Dev mode: Downloading latest prompt files")
            promptDownloader()
        else:
            print("Prod mode: Skipping prompt download")
                                
        instructions = payload.get("instructions")
        content = payload.get("payload", " ")
        response_id = payload.get("threadId")

        # Get agent configuration
        agent_config_doc = fetch_agent_config()
        print(f"the agent config: {agent_config_doc}")
        agent_name = agent_config_doc.get('name', 'UnknownAgent')

        # Generate request ID
        request_id = payload.get('request_id', f"req-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        print(f"Request ID: {request_id}")

        print("Calling press_release_rewiter")
        mcp_output, explanation, response_id = llm(
            content,
            instructions,
            thread_id=response_id,
        )


        call_webhook_with_success(payload.get('id'), {
                "status": 'inprogress',
                "data": {
                    "info": "Task successfully completed!",
                    "output": {"name": "explanation", "type": "longText", "data": explanation}
                }
            })
        call_webhook_with_success(payload.get('id'), {
                "status": 'inprogress',
                "data": {
                    "info": "Task successfully completed!",
                    "output": {"name": "threadId", "type": "shortText", "data": response_id}
                }
            })
        # Replace with your output name, type and data.
        resp = {"name": "output", "type": "longText", "data": mcp_output}

        return resp, explanation, response_id

    except Exception as e:
        print(f"Error in base_agent_gimlet: {e}")
        # raise call_webhook_with_error(str(e), 500) # OLD VERSION SINGLE THREADED
        raise call_webhook_with_error(payload.get('id'), str(e), 500) # MULTI THREADED