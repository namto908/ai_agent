import json
from typing import List, Dict, Any
from ..state import AgentState, Task
from ..prompts.intent_extraction_prompt import get_intent_extraction_prompt
from ..llm_client import get_llm_client

def extract_intent(state: AgentState) -> dict:
    print("--- Node: INTENT EXTRACTION ---")
    user_message = state.question # Assuming user's question is in state.question
    chat_history = state.chat_history # Assuming chat history is in state.chat_history
    org_policies = [] # Placeholder for organization policies
    defaults = {"deliverable_format": "markdown", "locale": "vi", "tone": "neutral"} # Placeholder for defaults
    tool_inventory = state.tool_inventory # Assuming tool inventory is in state.tool_inventory

    prompt = get_intent_extraction_prompt(user_message, chat_history, org_policies, defaults, tool_inventory)

    # Implement retry logic for JSON output
    for attempt in range(3): # Max 3 attempts
        try:
            response_json = get_llm_client().invoke_chat_json(prompt)
            print(f"LLM parsed JSON for Intent Extraction: {response_json}")

            # Validate against expected schema (basic check for now)
            # Validate against expected schema (basic check for now)
            # Map fields from LLM response to Task model fields
            if "intent" in response_json:
                response_json["intent_summary"] = response_json.pop("intent")
            
            # Map 'acceptance_criteria' to 'acceptance' if present
            if "acceptance_criteria" in response_json and "acceptance" not in response_json:
                response_json["acceptance"] = response_json.pop("acceptance_criteria")

            if not all(k in response_json for k in ["intent_summary", "acceptance", "priority"]):
                raise ValueError("Missing required fields in Intent Extraction JSON.")

            # If successful, return the task
            return {"task": Task(**response_json)}

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Intent Extraction failed (attempt {attempt + 1}): {e}")
            if attempt < 2: # If not last attempt, try to fix JSON
                print("Re-invoking LLM with original prompt to fix JSON.")
                # Re-invoke with original prompt
                prompt = get_intent_extraction_prompt(user_message, chat_history, org_policies, defaults, tool_inventory)
            else:
                print("Max retries reached for Intent Extraction. Returning error.")
                return {"errors": state.errors + [f"Intent Extraction failed after multiple retries: {e}"]}
        except Exception as e:
            print(f"An unexpected error occurred during Intent Extraction: {e}")
            return {"errors": state.errors + [f"Unexpected error in Intent Extraction: {e}"]}

    print(f"Intent Extraction returning errors: {state.errors + ["Intent Extraction failed due to unknown reason."]}")
    return {"errors": state.errors + ["Intent Extraction failed due to unknown reason."]}
