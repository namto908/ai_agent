"""
Node: DIRECT_ANSWER
Generates a simple, hardcoded answer for basic intents.
"""
from ..state import AgentState

def generate_direct_answer(state: AgentState) -> dict:
    """
    Provides a direct answer based on the classified intent.
    This avoids calling the LLM again for simple things.
    """
    print("--- Node: DIRECT_ANSWER ---")
    intent = state.intent
    # Memory-style questions: prefer using chat_history even if router returned an answer
    q_lower = (state.question or "").lower()
    memory_intents = [
        "vừa nói gì",
        "nhớ tôi nói gì",
        "nhớ tôi vừa nói",
        "what did i just say",
        "do you remember what i said",
    ]
    if any(p in q_lower for p in memory_intents):
        # Find last user utterance before this turn
        last_user = None
        for turn in reversed(state.chat_history or []):
            if turn.get("role") == "user":
                last_user = turn.get("content")
                break
        if last_user:
            return {"final_answer": f"Bạn vừa nói: '{last_user}'."}
        # If no history, fall back to a graceful message
        return {"final_answer": "Hiện tôi chưa có lịch sử cuộc trò chuyện trước đó trong phiên này."}

    # If router already provided an answer (and it's not a memory-style question), return it directly
    if state.final_answer:
        return {"final_answer": state.final_answer}

    answer = "Rất tiếc, tôi chưa hiểu câu hỏi của bạn."

    if intent == "greeting":
        name = (state.profile or {}).get("name")
        if name:
            answer = f"Chào {name}! Tôi là AI Agent, rất vui được gặp bạn. Tôi có thể giúp gì cho bạn hôm nay?"
        else:
            answer = "Chào bạn! Tôi là AI Agent, tôi có thể giúp gì cho bạn?"
    elif intent == "simple_question":
        # Một số câu phổ biến
        q = q_lower
        name = (state.profile or {}).get("name")
        if "tên gì" in q or "tên tôi" in q or "my name" in q:
            if name:
                answer = f"Bạn vừa giới thiệu tên là {name}. Tôi sẽ ghi nhớ trong phiên này."
            else:
                answer = "Bạn chưa giới thiệu tên. Bạn có thể nói: 'Tôi là [tên của bạn]'."
        else:
            answer = "Đây là một câu hỏi đơn giản. Tôi đang học cách để trả lời chúng. Hiện tại, bạn có thể hỏi tôi các câu hỏi phức tạp cần truy vấn dữ liệu."
    
    return {"final_answer": answer}
