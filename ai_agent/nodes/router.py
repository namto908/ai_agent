"""
Node: ROUTER
Classifies user intent and provides direct answers for simple queries.
"""
from ..state import AgentState
from ..prompts.router_prompt import get_router_prompt
from ..llm_client import get_llm_client

def route_question(state: AgentState) -> dict:
    """
    Determines the user's intent and decides whether to answer directly
    or proceed with the complex planning process.
    """
    print("--- Node: ROUTER ---")
    question = state.question
    prompt = get_router_prompt(question, state.chat_history)

    try:
        response = get_llm_client().invoke_chat_json(prompt)
        
        # Add detailed logging to debug the LLM's raw response
        print(f"LLM raw response for routing: {response}")
        
        # Add type checking for robustness
        if not isinstance(response, dict):
            raise TypeError(f"LLM response is not a dictionary, but {type(response)}")

        intent = response.get("intent", "complex_query")
        answer = response.get("answer")

        print(f"Intent classified as: '{intent}'")

        # Extract simple profile signals (e.g., name) from greeting like "tôi là X" / "I'm X"
        user_name = None
        try:
            import re
            # Vietnamese patterns
            for pat in [r"\btôi là\s+([A-Za-zÀ-ỹ\s]+)$", r"\bmình là\s+([A-Za-zÀ-ỹ\s]+)$"]:
                m = re.search(pat, question.strip(), flags=re.IGNORECASE)
                if m:
                    user_name = m.group(1).strip().strip('.')
                    break
            # English quick pattern
            if not user_name:
                m = re.search(r"\b(i am|i'm)\s+([A-Za-z\-']+)\b", question.strip(), flags=re.IGNORECASE)
                if m:
                    user_name = m.group(2).strip()
        except Exception:
            pass

        # Pass along an answer for simple intents to avoid extra LLM calls later
        result = {"intent": intent}
        if isinstance(answer, str) and answer.strip():
            result["final_answer"] = answer.strip()
        # Log history
        history_entry = {
            "type": "route",
            "question": question,
            "intent": intent,
            "has_direct_answer": bool(result.get("final_answer")),
        }
        # Merge profile
        new_profile = dict(state.profile or {})
        if user_name:
            new_profile["name"] = user_name

        result["history"] = state.history + [history_entry]
        result["profile"] = new_profile
        return result

    except BaseException as e:
        import traceback
        print("--- UNEXPECTED ROUTING ERROR ---")
        print(f"Error Type: {type(e)}")
        print(f"Error Value: {e}")
        print(f"Traceback:\n{traceback.format_exc()}")
        print("--- END OF ERROR ---")
        # In case of any error, default to the robust, complex query path
        return {"intent": "complex_query"}
