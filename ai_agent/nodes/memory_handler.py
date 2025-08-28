"""
Node: MEMORY HANDLER
Handles memory operations including retrieval and storage
"""
import hashlib
import uuid
from datetime import datetime
from typing import Dict, Any
from ..state import AgentState
from ..memory import get_memory_manager, MemoryEntry, MemoryQuery

def handle_memory(state: AgentState) -> dict:
    """
    Handle memory operations for the current interaction
    """
    print("--- Node: MEMORY HANDLER ---")
    
    memory_manager = get_memory_manager()
    
    # Generate memory ID
    memory_id = str(uuid.uuid4())
    
    # Get user ID from profile or generate default
    user_id = state.profile.get("user_id", "default_user")
    session_id = state.execution_context.session_id if state.execution_context else "default_session"
    
    # Search for similar memories
    similar_memories = memory_manager.search_similar_memories(
        question=state.question,
        user_id=user_id,
        limit=3
    )
    
    # Convert similar memories to dict format for state
    similar_memories_dict = []
    for memory in similar_memories:
        similar_memories_dict.append({
            "id": memory.id,
            "question": memory.question,
            "answer": memory.answer,
            "intent": memory.intent,
            "timestamp": memory.timestamp,
            "success": memory.success
        })
    
    # Create memory context from similar memories
    memory_context = ""
    if similar_memories:
        memory_context = "### 📚 Câu hỏi tương tự trước đây:\n\n"
        for i, memory in enumerate(similar_memories, 1):
            memory_context += f"**{i}. Câu hỏi:** {memory.question}\n"
            memory_context += f"**Trả lời:** {memory.answer[:200]}...\n"
            memory_context += f"**Thời gian:** {memory.timestamp}\n\n"
    
    return {
        "memory_id": memory_id,
        "similar_memories": similar_memories_dict,
        "memory_context": memory_context
    }

def store_memory(state: AgentState) -> dict:
    """
    Store the current interaction in memory
    """
    print("--- Node: MEMORY STORAGE ---")
    
    memory_manager = get_memory_manager()
    
    # Get user ID and session ID
    user_id = state.profile.get("user_id", "default_user")
    session_id = state.execution_context.session_id if state.execution_context else "default_session"
    
    # Extract tools used from observations
    tools_used = []
    if state.observations:
        for obs in state.observations:
            if obs.tool and obs.tool not in tools_used:
                tools_used.append(obs.tool)
    
    # Determine success based on errors and final answer
    success = len(state.errors) == 0 and state.final_answer is not None
    
    # Create metadata
    metadata = {
        "run_id": state.run_id,
        "intent": state.intent,
        "errors": state.errors,
        "profile": state.profile,
        "similar_memories_found": len(state.similar_memories)
    }
    
    # Create memory entry
    memory_entry = MemoryEntry(
        id=state.memory_id or str(uuid.uuid4()),
        session_id=session_id,
        user_id=user_id,
        timestamp=datetime.now().isoformat(),
        question=state.question,
        answer=state.final_answer or "No answer generated",
        intent=state.intent,
        tools_used=tools_used,
        success=success,
        metadata=metadata
    )
    
    # Store in memory
    memory_manager.add_memory(memory_entry)
    
    print(f"✅ Memory stored: {memory_entry.id}")
    
    return {"memory_stored": True, "memory_id": memory_entry.id}

def get_memory_statistics(user_id: str) -> Dict[str, Any]:
    """
    Get memory statistics for a user
    """
    memory_manager = get_memory_manager()
    return memory_manager.get_user_statistics(user_id)

def get_memory_summary(user_id: str) -> str:
    """
    Get a formatted memory summary for a user
    """
    memory_manager = get_memory_manager()
    return memory_manager.get_memory_summary(user_id)
