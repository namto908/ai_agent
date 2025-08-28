import json
from typing import Dict, Any
from ..state import AgentState, Step
from ..prompts.replan_repair_prompt import get_replan_repair_prompt
from ..llm_client import get_llm_client

def replan_or_repair(state: AgentState) -> dict:
    print("--- Node: REPLAN/REPAIR ---")
    task = state.task.dict()
    plan = state.plan.dict() # Assuming state.plan is the full plan object from Plan Generation
    failure_context = state.failure_context.dict() if state.failure_context else {}
    tool_inventory = state.tool_inventory

    prompt = get_replan_repair_prompt(task, plan, failure_context, tool_inventory)

        # Use JSON mode for consistent output
    try:
        response_json = get_llm_client().invoke_chat_json(prompt)

        # Validate against expected schema (basic check for now)
        if not all(k in response_json for k in ["strategy", "rationale", "updated_plan"]):
            raise ValueError("Missing required fields in Replan/Repair JSON.")

        # Convert steps to Step objects in updated_plan
        updated_plan_steps = []
        for step_data in response_json.get("updated_plan", {}).get("steps", []):
            # Map LLM output fields to Step model fields
            mapped_step = {}
            if "title" in step_data:
                mapped_step["title"] = step_data["title"]
            elif "description" in step_data:
                mapped_step["title"] = step_data["description"]
            else:
                mapped_step["title"] = f"Step {len(updated_plan_steps) + 1}"

            if "action" in step_data:
                mapped_step["action"] = step_data["action"]
            elif "tool" in step_data:
                mapped_step["action"] = step_data["tool"]
            else:
                # Don't set a default action - let Pydantic validation handle it
                continue  # Skip this step if no action is provided

            if "input" in step_data:
                mapped_step["input"] = step_data["input"]
            else:
                mapped_step["input"] = {}

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

            updated_plan_steps.append(Step(**mapped_step))
        response_json["updated_plan"]["steps"] = updated_plan_steps

        # Update state with replan/repair results
        return {
            "replan_strategy": response_json.get("strategy"),
            "replan_rationale": response_json.get("rationale"),
            "plan": response_json.get("updated_plan"), # Update the plan in state
            "loop_avoidance": response_json.get("loop_avoidance")
        }

    except (json.JSONDecodeError, ValueError) as e:
        print(f"Replan/Repair failed: {e}")
        return {"errors": state.errors + [f"Replan/Repair failed: {e}"]}
    except Exception as e:
        print(f"An unexpected error occurred during Replan/Repair: {e}")
        return {"errors": state.errors + [f"Unexpected error in Replan/Repair: {e}"]}
