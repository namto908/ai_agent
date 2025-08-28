import json
from typing import List, Dict, Any
from ..state import AgentState, Step, Plan # Import Plan
from ..prompts.plan_generation_prompt import get_plan_generation_prompt
from ..llm_client import get_llm_client

def generate_plan(state: AgentState) -> dict:
    print("--- Node: PLAN GENERATION ---")
    task = state.task
    tool_inventory = state.tool_inventory
    limits = state.limits

    # Handle case where limits might be None
    limits_dict = limits.dict() if limits else {}
    prompt = get_plan_generation_prompt(task.dict(), tool_inventory, limits_dict)

    # Implement retry logic for JSON output
    for attempt in range(3): # Max 3 attempts
        try:
            response_json = get_llm_client().invoke_chat_json(prompt)
            print(f"LLM parsed JSON for Plan Generation: {response_json}")

            # Handle different JSON structures from LLM
            plan_data = None
            
            # Case 1: Direct structure with rationale, steps, plan_score
            if all(k in response_json for k in ["rationale", "steps", "plan_score"]):
                plan_data = response_json
            # Case 2: Nested structure with "plan" wrapper
            elif "plan" in response_json and isinstance(response_json["plan"], dict):
                plan_data = response_json["plan"]
                # Add default rationale if missing
                if "rationale" not in plan_data:
                    plan_data["rationale"] = "Plan generated based on task requirements"
            else:
                raise ValueError("Invalid JSON structure. Expected either direct fields or 'plan' wrapper.")

            # Validate required fields
            if not all(k in plan_data for k in ["steps", "plan_score"]):
                raise ValueError("Missing required fields in Plan Generation JSON.")

            # Convert steps to Step objects
            plan_steps = []
            for step_data in plan_data.get("steps", []):
                # Map LLM output fields to Step model fields
                mapped_step = {}
                
                # Map title/description
                if "title" in step_data:
                    mapped_step["title"] = step_data["title"]
                elif "description" in step_data:
                    mapped_step["title"] = step_data["description"]
                else:
                    mapped_step["title"] = f"Step {len(plan_steps) + 1}"
                
                # Map action/tool
                if "action" in step_data:
                    mapped_step["action"] = step_data["action"]
                elif "tool" in step_data:
                    mapped_step["action"] = step_data["tool"]
                else:
                    mapped_step["action"] = "sql.query"  # Default action
                
                # Map input
                if "input" in step_data:
                    mapped_step["input"] = step_data["input"]
                else:
                    mapped_step["input"] = {}
                
                # Map expect/success_criteria
                if "expect" in step_data:
                    mapped_step["expect"] = step_data["expect"]
                elif "success_criteria" in step_data:
                    mapped_step["expect"] = {"success_criteria": step_data["success_criteria"]}
                else:
                    mapped_step["expect"] = {}
                
                # Copy other fields
                for field in ["timeout_s", "max_retries", "id", "description", "reason", "tool", "success_criteria", "depends_on"]:
                    if field in step_data:
                        mapped_step[field] = step_data[field]
                
                plan_steps.append(Step(**mapped_step))
            plan_data["steps"] = plan_steps

            # Return a Plan object
            return {"plan": Plan(**plan_data)}

        except (json.JSONDecodeError, ValueError) as e:
            print(f"Plan Generation failed (attempt {attempt + 1}): {e}")
            if attempt < 2: # If not last attempt, try to fix JSON
                print("Re-invoking LLM with original prompt to fix JSON.")
                # Re-invoke with original prompt
                prompt = get_plan_generation_prompt(task.dict(), tool_inventory, limits_dict)
            else:
                print("Max retries reached for Plan Generation. Returning error.")
                return {"errors": state.errors + [f"Plan Generation failed after multiple retries: {e}"]}
        except Exception as e:
            print(f"An unexpected error occurred during Plan Generation: {e}")
            return {"errors": state.errors + [f"Unexpected error in Plan Generation: {e}"]}

    return {"errors": state.errors + ["Plan Generation failed due to unknown reason."]}
