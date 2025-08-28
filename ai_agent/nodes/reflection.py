import json
from typing import Dict, Any
from ..state import AgentState
from ..prompts.reflection_prompt import get_reflection_prompt
from ..llm_client import get_llm_client

def reflect_on_execution(state: AgentState) -> dict:
    print("--- Node: REFLECTION ---")
    task_acceptance = state.task.acceptance
    plan = state.plan # Assuming state.plan is the full plan object from Plan Generation
    
    # Handle case where last_observation might be None
    if state.last_observation:
        last_observation = state.last_observation.dict() # Convert Pydantic model to dict
    else:
        last_observation = {} # Default empty dict if no observation
    
    progress_summary = state.progress_summary.dict() if state.progress_summary else {} # Convert Pydantic model to dict

    prompt = get_reflection_prompt(task_acceptance, plan.dict(), last_observation, progress_summary)

    # Implement retry logic for JSON output
    for attempt in range(3): # Max 3 attempts
        try:
            response_json = get_llm_client().invoke_chat_json(prompt)

            # Validate against expected schema (basic check for now)
            if not all(k in response_json for k in ["status", "message"]):
                raise ValueError("Missing required fields in Reflection JSON.")

            # Update state with reflection results
            result = {
                "reflection_status": response_json.get("status"),
                "reflection_message": response_json.get("message"),
                "reflection_adjustment": response_json.get("adjustment"),
                "reflection_evidence": response_json.get("evidence"),
                "acceptance_progress": response_json.get("acceptance_progress")
            }
            
            # Update step_idx based on reflection status
            status = response_json.get("status")
            if status == "continue" and state.plan and state.step_idx < len(state.plan.steps) - 1:
                # Move to next step
                result["step_idx"] = state.step_idx + 1
                result["has_more_steps"] = True
                result["all_criteria_met"] = False
            elif status == "done" or status == "success":
                # Task completed
                result["all_criteria_met"] = True
                result["has_more_steps"] = False
            else:
                # Keep current step for retry/replan
                result["has_more_steps"] = state.step_idx < len(state.plan.steps) - 1 if state.plan else False
                result["all_criteria_met"] = False
            
            return result

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Reflection failed (attempt {attempt + 1}): {e}")
            if attempt < 2: # If not last attempt, try to fix JSON
                print("Re-invoking LLM with original prompt to fix JSON.")
                # Re-invoke with original prompt
                prompt = get_reflection_prompt(task_acceptance, plan.dict(), last_observation, progress_summary)
            else:
                print("Max retries reached for Reflection. Returning error.")
                return {"errors": state.errors + [f"Reflection failed after multiple retries: {e}"]}
        except Exception as e:
            print(f"An unexpected error occurred during Reflection: {e}")
            return {"errors": state.errors + [f"Unexpected error in Reflection: {e}"]}

    return {"errors": state.errors + ["Reflection failed due to unknown reason."]}
