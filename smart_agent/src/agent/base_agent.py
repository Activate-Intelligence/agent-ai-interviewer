from ..config.logger import Logger
from ..utils.webhook import call_webhook_with_error, call_webhook_with_success
from openai import OpenAI
from .prompt_extract import extract_prompts
import os
from datetime import datetime
from .agent_config import fetch_agent_config
import json

# Configuration flag - Change this to switch between dev and prod modes
ENVIRONMENT_MODE = "dev"  # Change to "prod" for production or dev for development

openai_api_key = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=openai_api_key)

COMPLETION_MARKER = "[CONVERSATION_COMPLETE]"


def get_environment_mode():
    """Get the current environment mode (dev or prod)"""
    return ENVIRONMENT_MODE.lower()


def get_prompt_file_path():
    """Get the appropriate prompt file path based on environment mode"""
    mode = get_environment_mode()

    if mode == "dev":
        # In dev mode, try /tmp/Prompt first, fallback to Prompt
        tmp_prompt_path = '/tmp/Prompt/ClientDiscovery.yaml'
        if os.path.exists(tmp_prompt_path):
            return tmp_prompt_path
        else:
            return 'Prompt/ClientDiscovery.yaml'
    else:
        # In prod mode, only use Prompt folder
        return 'Prompt/ClientDiscovery.yaml'


def detect_completion(response_text):
    """Detect if the conversation is complete based on the model's response"""
    return COMPLETION_MARKER in response_text


def clean_response(response_text):
    """Remove completion marker from response text for display"""
    return response_text.replace(COMPLETION_MARKER, "").strip()


def interviewer(user_input, previous_response_id=None):
    """
    Conduct an interview turn using OpenAI's GPT-5.1 Responses API with thread continuity.

    GPT-5.1 uses the Responses API which supports:
    - previous_response_id for passing chain of thought between turns
    - reasoning.effort parameter (none, low, medium, high)
    - text.verbosity parameter (low, medium, high)

    Args:
        user_input: The user's message
        previous_response_id: The ID of the previous response for thread continuity

    Returns:
        tuple: (model_response, response_id, is_complete)
    """
    prompt_file_path = get_prompt_file_path()

    # Extract prompts with user input replacement
    replacements = {"user_input": user_input}
    system_prompt, user_prompt, model_params = extract_prompts(
        prompt_file_path,
        **replacements
    )

    print("---" * 30)
    print(f"Model: {model_params['name']}")
    print(f"Previous Response ID: {previous_response_id}")
    print(f"Reasoning Effort: {model_params.get('reasoning_effort', 'none')}")
    print(f"Verbosity: {model_params.get('verbosity', 'medium')}")
    print(f"User Input: {user_input[:100]}...")
    print("---" * 30)

    try:
        # Build the API call parameters for GPT-5.1 Responses API
        api_params = {
            "model": model_params['name'],
            "max_output_tokens": model_params.get('max_tokens', 2048),
            "reasoning": {
                "effort": model_params.get('reasoning_effort', 'none')
            },
            "text": {
                "verbosity": model_params.get('verbosity', 'medium')
            }
        }

        # Only add temperature when reasoning effort is 'none'
        if model_params.get('reasoning_effort', 'none') == 'none':
            api_params["temperature"] = model_params.get('temperature', 0.7)

        if previous_response_id:
            # Continue existing thread - pass previous_response_id for CoT continuity
            api_params["previous_response_id"] = previous_response_id
            api_params["input"] = [
                {"role": "user", "content": user_prompt}
            ]
        else:
            # Start new conversation with system prompt
            api_params["input"] = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]

        response = client.responses.create(**api_params)

        # Extract response text from the GPT-5.1 response object
        # GPT-5.1 returns output_text directly or in output items
        response_text = ""
        if hasattr(response, 'output_text'):
            response_text = response.output_text
        else:
            # Fallback to iterating over output items
            for item in response.output:
                if item.type == "message":
                    for content in item.content:
                        if hasattr(content, 'text'):
                            response_text += content.text
                        elif content.type == "output_text":
                            response_text += content.text

        # Check if conversation is complete
        is_complete = detect_completion(response_text)

        # Clean the response for display
        clean_text = clean_response(response_text)

        print(f"Response ID: {response.id}")
        print(f"Is Complete: {is_complete}")
        print(f"Response: {clean_text[:200]}...")

        return clean_text, response.id, is_complete

    except Exception as e:
        print(f"Error calling OpenAI GPT-5.1 Responses API: {e}")
        # Fallback to Chat Completions API if Responses API fails
        return fallback_chat_completion(system_prompt, user_prompt, model_params, previous_response_id)


def fallback_chat_completion(system_prompt, user_prompt, model_params, conversation_history=None):
    """
    Fallback to Chat Completions API if Responses API is not available.
    Uses a simple conversation history stored as JSON string.
    """
    try:
        messages = []

        if conversation_history:
            try:
                # Try to parse conversation history from JSON
                history = json.loads(conversation_history)
                messages = history
            except (json.JSONDecodeError, TypeError):
                # If not valid JSON, start fresh with system prompt
                messages = [{"role": "system", "content": system_prompt}]
        else:
            messages = [{"role": "system", "content": system_prompt}]

        # Add the new user message
        messages.append({"role": "user", "content": user_prompt})

        # Use gpt-4o as fallback if gpt-5.1 responses API fails
        fallback_model = "gpt-4o"

        response = client.chat.completions.create(
            model=fallback_model,
            messages=messages,
            temperature=model_params.get('temperature', 0.7),
            max_tokens=model_params.get('max_tokens', 2048)
        )

        response_text = response.choices[0].message.content.strip()

        # Check if conversation is complete
        is_complete = detect_completion(response_text)

        # Clean the response for display
        clean_text = clean_response(response_text)

        # Add assistant response to history for next turn
        messages.append({"role": "assistant", "content": response_text})

        # Use JSON-encoded history as the "response_id" for fallback
        history_id = json.dumps(messages)

        return clean_text, history_id, is_complete

    except Exception as e:
        print(f"Error in fallback chat completion: {e}")
        raise


def base_agent(payload):
    """
    Main agent function implementing the Daiquiri pattern for multi-turn conversations.

    Inputs expected:
        - userInput: The user's message (required)
        - history: The previous response ID or conversation history (optional)
        - output: The previous agent response (optional, for context)

    Returns:
        tuple: (resp, model_response, response_id, is_complete, summary)
    """
    try:
        print(payload)

        # Check environment mode
        mode = get_environment_mode()
        print(f"Running in {mode} mode")

        # Get agent configuration
        agent_config_doc = fetch_agent_config()
        print(f"Agent config: {agent_config_doc}")
        agent_name = agent_config_doc.get('name', 'Client Discovery Interview')

        # Generate request ID
        request_id = payload.get(
            'request_id', f"req-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        print(f"Request ID: {request_id}")

        # Extract inputs
        user_input = payload.get('userInput', '')
        previous_response_id = payload.get('history')  # Thread ID from previous turn
        previous_output = payload.get('output', '')  # Previous response (for reference)

        # Handle empty or initial user input
        if not user_input or user_input.strip() == '':
            # If no user input, this is the start - use a greeting trigger
            user_input = "Hello, I'd like to start the discovery conversation."

        call_webhook_with_success(
            payload.get('id'), {
                "status": "inprogress",
                "data": {
                    "title": "Processing your message",
                    "info": "Conducting discovery interview...",
                },
            })

        # Call the interviewer using GPT-5.1
        model_response, response_id, is_complete = interviewer(
            user_input,
            previous_response_id
        )

        # Generate summary if conversation is complete
        summary = None
        if is_complete:
            # The summary should be included in the model_response since we instructed
            # the model to provide a closing summary
            summary = model_response

        # Send outputs via webhook
        call_webhook_with_success(payload.get('id'), {
            "status": "inprogress",
            "data": {
                "output": {
                    "name": "output",
                    "type": "longText",
                    "data": model_response
                }
            }
        })

        call_webhook_with_success(payload.get('id'), {
            "status": "inprogress",
            "data": {
                "output": {
                    "name": "history",
                    "type": "longText",
                    "data": response_id
                }
            }
        })

        if is_complete:
            call_webhook_with_success(payload.get('id'), {
                "status": "inprogress",
                "data": {
                    "output": {
                        "name": "isComplete",
                        "type": "boolean",
                        "data": True
                    }
                }
            })

            if summary:
                call_webhook_with_success(payload.get('id'), {
                    "status": "inprogress",
                    "data": {
                        "output": {
                            "name": "summary",
                            "type": "longText",
                            "data": summary
                        }
                    }
                })

        # Prepare response
        resp = {"name": "output", "type": "longText", "data": model_response}

        return resp, model_response, response_id, is_complete, summary

    except Exception as e:
        print(f"Error in base_agent: {e}")
        call_webhook_with_error(payload.get('id'), str(e), 500)
        raise
