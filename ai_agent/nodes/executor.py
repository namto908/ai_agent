import json
from typing import Dict, Any
from ..state import AgentState, Observation
from ..tools import knowledge_graph, rag, database, web, google_search
from ..tools import github as github_tool
import time # For latency metrics

def execute_action(state: AgentState) -> dict:
    print("--- Node: ACTION EXECUTION ---")
    print(f"State.plan type: {type(state.plan)}")
    print(f"State.plan: {state.plan}")
    
    # Validate plan and step_idx
    if not state.plan or not state.plan.steps:
        return {"errors": state.errors + ["No plan or steps available for execution"]}
    
    if state.step_idx >= len(state.plan.steps):
        # All steps completed, go to final synthesis
        return {"final_answer": "All steps in the plan have been completed successfully."}
    
    current_step = state.plan.steps[state.step_idx] # Assuming plan is a list of Step objects
    tool_name = current_step.action.value  # Use action.value to get the string
    tool_input = current_step.input
    
    # Placeholder for execution_context (session_id, trace_id, timeout, pii_policy)
    # For now, we'll use dummy values or retrieve from state if available
    execution_context = state.execution_context or {}

    start_time = time.time()
    
    result_data = {}
    error_data = None
    ok_status = True

    try:
        # --- Tool Execution Logic ---
        # PostgreSQL Tools
        if tool_name == "sql.list_tables":
            schemas = tool_input.get("schemas")
            include_system = tool_input.get("include_system", False)
            result_data = database.list_tables(schemas=schemas, include_system=include_system)
        elif tool_name == "sql.custom_query":
            result_data = database.execute_custom_query(**tool_input)
        elif tool_name == "sql.describe_table":
            result_data = database.describe_table(**tool_input)
        elif tool_name == "sql.get_table_info":
            result_data = database.get_table_info(**tool_input)
        elif tool_name == "sql.search_in_table":
            result_data = database.search_in_table(**tool_input)
        elif tool_name == "sql.get_distinct_values":
            result_data = database.get_distinct_values(**tool_input)
        elif tool_name == "sql.get_table_stats":
            result_data = database.get_table_statistics(**tool_input)
        elif tool_name == "sql.find_related_tables":
            result_data = database.find_related_tables(**tool_input)
        elif tool_name == "sql.get_schema":
            result_data = database.get_schema()
        
        # Milvus Tools
        elif tool_name == "milvus.list_collections":
            result_data = rag.list_milvus_collections(**tool_input)
        elif tool_name == "milvus.describe_index":
            result_data = rag.describe_milvus_index(**tool_input)
        elif tool_name == "rag.search":
            result_data = rag.search(**tool_input)
        
        # Neo4j Tools
        elif tool_name == "kg.query":
            result_data = knowledge_graph.query(**tool_input)
        
        # General Tools
        elif tool_name == "google.search":
            result_data = google_search.search(**tool_input)
        elif tool_name == "http.get":
            result_data = web.get(**tool_input)
        elif tool_name == "github.request":
            result_data = github_tool.request(**tool_input)
        elif tool_name == "plan.note":
            result_data = {"note": tool_input.get("note", "No note provided")}
        
        else:
            raise ValueError(f"Tool '{tool_name}' not implemented for direct execution.")

        # Ensure result_data is a dictionary
        if not isinstance(result_data, dict):
            result_data = {"result": result_data, "type": type(result_data).__name__}

    except Exception as e:
        ok_status = False
        error_data = {"summary": str(e), "detail": str(e)} # Basic error for now
        print(f"Error executing tool {tool_name}: {e}")
        result_data = {}  # Ensure result_data is a dict even on error

    end_time = time.time()
    latency_ms = (end_time - start_time) * 1000

    # Placeholder for metrics and safety
    metrics = {"latency_ms": latency_ms, "tokens_input": 0, "tokens_output": 0, "cost_estimate": 0}
    safety = {"pii_redacted": False, "notes": ""}

    observation = Observation(
        step_id=current_step.id or f"step_{state.step_idx}",  # Use fallback if id is None
        tool=tool_name,
        attempt=1, # Assuming first attempt for now
        ok=ok_status,
        data=result_data,
        error=error_data,
        metrics=metrics,
        safety=safety
    )
    
    # Update state with last_observation and add to observations list
    return {"last_observation": observation, "observations": state.observations + [observation]}