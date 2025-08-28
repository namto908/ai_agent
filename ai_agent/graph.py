from langgraph.graph import StateGraph, END
from .state import AgentState
from .nodes.intent_extraction import extract_intent
from .nodes.router import route_question
from .nodes.planner import generate_plan
from .nodes.executor import execute_action
from .nodes.reflection import reflect_on_execution
from .nodes.replan_repair import replan_or_repair
from .nodes.synthesizer import synthesize_final_answer
from .nodes.memory_handler import handle_memory, store_memory

# --- Conditional Edge Logic --- #

def after_action_execution(state: AgentState) -> str:
    """
    Decides the next step after action execution.
    """
    # For now, always go to reflection after execution
    return "reflection"

def after_reflection(state: AgentState) -> str:
    """
    Decides the next step after reflection.
    """
    # Get reflection status from state attributes
    reflection_status = getattr(state, 'reflection_status', None)
    all_criteria_met = getattr(state, 'all_criteria_met', None)
    has_more_steps = getattr(state, 'has_more_steps', None)
    can_replan_repair = getattr(state, 'can_replan_repair', None)
    
    # Logic for routing after reflection
    if reflection_status == "done" or reflection_status == "success":
        return "final_synthesis"
    elif reflection_status == "continue":
        # Check if there are more steps to execute
        if has_more_steps:
            return "action_execution"
        else:
            # No more steps, go to final synthesis
            return "final_synthesis"
    elif reflection_status == "replan":
        return "replan_repair"
    else:
        # Default to final synthesis
        return "final_synthesis"

def after_replan_repair(state: AgentState) -> str:
    """
    Decides the next step after replan/repair.
    """
    # Always go back to plan_generation after replan/repair
    return "plan_generation"

def after_router(state: AgentState) -> str:
    """
    Decides the next step after router.
    """
    # If router provided a direct answer, go to final synthesis
    if state.final_answer:
        return "final_synthesis"
    # If intent is simple, go to intent extraction for basic processing
    elif getattr(state, 'intent', 'complex_query') in ['greeting', 'simple_question']:
        return "intent_extraction"
    # Otherwise, go to intent extraction for complex processing
    else:
        return "intent_extraction"

def after_intent_extraction(state: AgentState) -> str:
    """
    Decides the next step after intent extraction.
    """
    if state.errors:
        return "final_synthesis"
    else:
        return "memory_handler"

def after_memory_handler(state: AgentState) -> str:
    """
    Decides the next step after memory handling.
    """
    return "plan_generation"

def after_plan_generation(state: AgentState) -> str:
    """
    Decides the next step after plan generation.
    """
    if state.errors or not state.plan: # Check for errors or if plan is None
        return "final_synthesis"
    else:
        return "action_execution"

def after_final_synthesis(state: AgentState) -> str:
    """
    Decides the next step after final synthesis.
    """
    return "memory_storage"

def after_memory_storage(state: AgentState) -> str:
    """
    Decides the next step after memory storage.
    """
    return END

# --- Graph Definition --- #

def build_graph():
    """
    Builds the LangGraph state machine for the Plan-Act-Reflect Agent.
    """
    workflow = StateGraph(AgentState)

    # Add all nodes
    workflow.add_node("router", route_question)
    workflow.add_node("intent_extraction", extract_intent)
    workflow.add_node("memory_handler", handle_memory)
    workflow.add_node("plan_generation", generate_plan)
    workflow.add_node("action_execution", execute_action)
    workflow.add_node("reflection", reflect_on_execution)
    workflow.add_node("replan_repair", replan_or_repair)
    workflow.add_node("final_synthesis", synthesize_final_answer)
    workflow.add_node("memory_storage", store_memory)

    # Set the entry point
    workflow.set_entry_point("router")

    # Define Edges
    workflow.add_conditional_edges(
        "router",
        after_router,
        {
            "final_synthesis": "final_synthesis",
            "intent_extraction": "intent_extraction"
        }
    )
    
    workflow.add_conditional_edges(
        "intent_extraction",
        after_intent_extraction,
        {
            "final_synthesis": "final_synthesis",
            "memory_handler": "memory_handler"
        }
    )
    
    workflow.add_conditional_edges(
        "memory_handler",
        after_memory_handler,
        {
            "plan_generation": "plan_generation"
        }
    )
    workflow.add_conditional_edges(
        "plan_generation",
        after_plan_generation,
        {
            "final_synthesis": "final_synthesis",
            "action_execution": "action_execution"
        }
    )
    workflow.add_conditional_edges(
        "final_synthesis",
        after_final_synthesis,
        {
            "memory_storage": "memory_storage"
        }
    )
    
    workflow.add_conditional_edges(
        "memory_storage",
        after_memory_storage,
        {
            END: END
        }
    )

    workflow.add_conditional_edges(
        "action_execution",
        after_action_execution,
        {
            "reflection": "reflection"
        }
    )

    workflow.add_conditional_edges(
        "reflection",
        after_reflection,
        {
            "final_synthesis": "final_synthesis",
            "action_execution": "action_execution",
            "replan_repair": "replan_repair"
        }
    )

    workflow.add_conditional_edges(
        "replan_repair",
        after_replan_repair,
        {
            "plan_generation": "plan_generation"
        }
    )

    # Compile the graph
    return workflow.compile()