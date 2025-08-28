"""
Streamlit demo: Basic chatbot UI for the AI Agent

Run:
  streamlit run ai_agent_project/streamlit_app.py
"""
from __future__ import annotations

import os
from typing import Any, Dict, List

from dotenv import load_dotenv
import streamlit as st

from ai_agent.graph import build_graph
from ai_agent.state import AgentState, Limits


def initialize_session() -> None:
    if "agent_app" not in st.session_state:
        st.session_state.agent_app = build_graph()
    if "chat_messages" not in st.session_state:
        st.session_state.chat_messages: List[Dict[str, str]] = []
    if "agent_history" not in st.session_state:
        st.session_state.agent_history: List[Dict[str, Any]] = []
    if "agent_profile" not in st.session_state:
        st.session_state.agent_profile: Dict[str, Any] = {}


def render_chat_history() -> None:
    for msg in st.session_state.chat_messages:
        with st.chat_message(msg.get("role", "assistant")):
            content = msg.get("content", "")
            # Use markdown for better formatting
            if len(content) > 500:  # Long content gets expandable section
                with st.expander("📄 Xem câu trả lời", expanded=True):
                    st.markdown(content)
            else:
                st.markdown(content)


def main() -> None:
    load_dotenv()  # Load environment variables early

    st.set_page_config(page_title="AI Agent Chatbot", page_icon="🤖", layout="wide")
    
    # Custom CSS for dark theme and better UX
    st.markdown("""
    <style>
    /* Dark theme for main app */
    .main {
        background-color: #0e1117;
        color: #fafafa;
    }
    
    /* Chat messages styling */
    .stChatMessage {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        background-color: #1e1e1e !important;
        border: 1px solid #333333;
    }
    
    .stChatMessage[data-testid="chatMessage"] {
        background-color: #1e1e1e !important;
    }
    
    /* Expander styling */
    .stExpander {
        border: 1px solid #333333;
        border-radius: 8px;
        margin: 0.5rem 0;
        background-color: #1e1e1e;
    }
    
    /* Markdown styling for dark theme */
    .stMarkdown {
        line-height: 1.6;
        color: #fafafa !important;
    }
    
    .stMarkdown p {
        margin-bottom: 0.5rem;
        color: #fafafa !important;
    }
    
    .stMarkdown ul, .stMarkdown ol {
        margin-bottom: 0.5rem;
        color: #fafafa !important;
    }
    
    .stMarkdown li {
        color: #fafafa !important;
    }
    
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4, .stMarkdown h5, .stMarkdown h6 {
        color: #ffffff !important;
        border-bottom: 1px solid #333333;
        padding-bottom: 0.5rem;
    }
    
    .stMarkdown code {
        background-color: #2d2d2d;
        padding: 0.2rem 0.4rem;
        border-radius: 3px;
        font-size: 0.9em;
        color: #ff6b6b !important;
        border: 1px solid #444444;
    }
    
    .stMarkdown pre {
        background-color: #1a1a1a;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #007bff;
        color: #fafafa !important;
        border: 1px solid #333333;
    }
    
    .stMarkdown pre code {
        color: #fafafa !important;
        background-color: transparent;
        padding: 0;
    }
    
    .stMarkdown blockquote {
        border-left: 4px solid #007bff;
        padding-left: 1rem;
        margin: 1rem 0;
        color: #cccccc !important;
        background-color: #1a1a1a;
        border-radius: 0 5px 5px 0;
    }
    
    .stMarkdown strong {
        color: #ffffff !important;
    }
    
    .stMarkdown em {
        color: #cccccc !important;
    }
    
    /* Table styling for better data display */
    .stMarkdown table {
        background-color: #1a1a1a;
        border: 1px solid #333333;
        border-radius: 8px;
        overflow: hidden;
        margin: 1rem 0;
    }
    
    .stMarkdown th {
        background-color: #2d2d2d !important;
        color: #ffffff !important;
        border: 1px solid #444444 !important;
        padding: 0.75rem !important;
        font-weight: bold !important;
    }
    
    .stMarkdown td {
        background-color: #1a1a1a !important;
        color: #fafafa !important;
        border: 1px solid #333333 !important;
        padding: 0.75rem !important;
    }
    
    .stMarkdown tr:nth-child(even) td {
        background-color: #222222 !important;
    }
    
    .stMarkdown tr:hover td {
        background-color: #2a2a2a !important;
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background-color: #1e1e1e;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        background-color: #1a1a1a;
        color: #fafafa;
        border: 1px solid #333333;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #007bff;
    }
    
    /* Button styling */
    .stButton > button {
        background-color: #007bff;
        color: #ffffff;
        border: none;
        border-radius: 5px;
    }
    
    .stButton > button:hover {
        background-color: #0056b3;
    }
    
    /* Success/Error message styling */
    .stSuccess {
        background-color: #1a1a1a;
        border: 1px solid #28a745;
        color: #28a745;
    }
    
    .stError {
        background-color: #1a1a1a;
        border: 1px solid #dc3545;
        color: #dc3545;
    }
    </style>
    """, unsafe_allow_html=True)
    
    st.title("🤖 AI Agent Chatbot")
    st.caption("💬 Nhập câu hỏi ở khung dưới. Agent sẽ tự lập kế hoạch, chạy tool và trả lời.")

    initialize_session()

    # Sidebar controls
    with st.sidebar:
        st.subheader("⚙️ Cài đặt")
        
        # User profile
        st.markdown("**👤 Hồ sơ người dùng**")
        name = st.text_input("Tên của bạn (tùy chọn)", st.session_state.agent_profile.get("name", ""))
        if name:
            st.session_state.agent_profile["name"] = name
        
        st.divider()
        
        # Chat controls
        st.markdown("**💬 Quản lý hội thoại**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Xóa hội thoại", use_container_width=True):
                st.session_state.chat_messages = []
                st.session_state.agent_history = []
                st.rerun()
        
        with col2:
            if st.button("📥 Xuất chat", use_container_width=True):
                # Export chat history
                chat_text = "\n\n".join([f"{msg['role']}: {msg['content']}" for msg in st.session_state.chat_messages])
                st.download_button(
                    label="💾 Tải xuống",
                    data=chat_text,
                    file_name=f"chat_history_{st.session_state.agent_profile.get('name', 'user')}.txt",
                    mime="text/plain"
                )
        
        st.divider()
        
        # Memory management
        st.markdown("**🧠 Quản lý Memory**")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("📊 Thống kê", use_container_width=True):
                try:
                    from ai_agent.memory import get_memory_manager
                    memory_manager = get_memory_manager()
                    user_id = st.session_state.agent_profile.get("name", "default_user")
                    stats = memory_manager.get_user_statistics(user_id)
                    
                    st.success("📊 Memory Statistics")
                    st.write(f"**Total Interactions:** {stats['total_interactions']}")
                    st.write(f"**Success Rate:** {stats['success_rate']}%")
                    
                    if stats['common_intents']:
                        st.write("**Common Intents:**")
                        for intent in stats['common_intents']:
                            st.write(f"- {intent['intent']}: {intent['count']} times")
                    
                    if stats['common_tools']:
                        st.write("**Common Tools:**")
                        for tool in stats['common_tools']:
                            st.write(f"- {tool['tool']}: {tool['count']} times")
                except Exception as e:
                    st.error(f"Error loading memory statistics: {e}")
        
        with col2:
            if st.button("🗑️ Xóa Memory", use_container_width=True):
                try:
                    from ai_agent.memory import get_memory_manager
                    memory_manager = get_memory_manager()
                    user_id = st.session_state.agent_profile.get("name", "default_user")
                    memory_manager.clear_user_memory(user_id)
                    st.success("Memory cleared successfully!")
                except Exception as e:
                    st.error(f"Error clearing memory: {e}")
        
        if st.button("📤 Xuất Memory", use_container_width=True):
            try:
                from ai_agent.memory import get_memory_manager
                memory_manager = get_memory_manager()
                user_id = st.session_state.agent_profile.get("name", "default_user")
                filename = memory_manager.export_memory(user_id)
                st.success(f"Memory exported to: {filename}")
            except Exception as e:
                st.error(f"Error exporting memory: {e}")
        
        st.divider()
        
        # Debug options
        st.markdown("**🔧 Tùy chọn debug**")
        if st.checkbox("Hiển thị lịch sử tác vụ"):
            with st.expander("📋 Lịch sử tác vụ"):
                st.json(st.session_state.agent_history)
        
        # Chat stats
        if st.session_state.chat_messages:
            st.divider()
            st.markdown("**📊 Thống kê**")
            total_messages = len(st.session_state.chat_messages)
            user_messages = len([m for m in st.session_state.chat_messages if m.get("role") == "user"])
            assistant_messages = len([m for m in st.session_state.chat_messages if m.get("role") == "assistant"])
            
            st.metric("Tổng tin nhắn", total_messages)
            st.metric("Tin nhắn người dùng", user_messages)
            st.metric("Tin nhắn AI", assistant_messages)

    # Display chat history
    render_chat_history()

    # Chat input with better UX
    st.markdown("---")
    user_input = st.chat_input("💬 Nhập câu hỏi của bạn... (Ví dụ: 'Xin chào!', 'Thời tiết Hà Nội hôm nay?', 'Giải thích về AI Agent')")
    if user_input:
        # Echo user message
        st.session_state.chat_messages.append({"role": "user", "content": user_input})
        with st.chat_message("user"):
            st.write(user_input)

        # Prepare state and invoke the agent
        with st.chat_message("assistant"):
            with st.spinner("Agent đang suy nghĩ..."):
                initial_state = AgentState(
                    question=user_input,
                    history=st.session_state.agent_history,
                    profile=st.session_state.agent_profile,
                    chat_history=st.session_state.chat_messages,
                    limits=Limits(max_steps=6, max_retries_per_step=2, time_budget_hint="ngắn"), # Default limits
                    tool_inventory=["sql.list_tables", "sql.custom_query", "google.search"] # Placeholder tools
                )
                try:
                    final_state = st.session_state.agent_app.invoke(initial_state, {"recursion_limit": 50})
                except Exception as e:
                    st.error(f"Đã xảy ra lỗi khi gọi agent: {e}")
                    return

                final_answer = final_state.get(
                    "final_answer",
                    "Xin lỗi, tôi gặp sự cố khi xử lý yêu cầu này.",
                )
                
                # Improved answer display with better UX
                if len(final_answer) > 500:
                    # Long answers get expandable section with preview
                    preview = final_answer[:200] + "..." if len(final_answer) > 200 else final_answer
                    st.markdown(f"**Tóm tắt:** {preview}")
                    with st.expander("📄 Xem câu trả lời đầy đủ", expanded=True):
                        st.markdown(final_answer)
                else:
                    # Short answers display directly
                    st.markdown(final_answer)

                # Show errors if any
                if final_state.get("errors"):
                    with st.expander("⚠️ Chi tiết lỗi trong tác vụ", expanded=False):
                        for i, err in enumerate(final_state["errors"], 1):
                            st.error(f"**Lỗi {i}:** {err}")
                
                # Show success message
                st.success("✅ Hoàn thành! Câu trả lời đã được tạo thành công.")

        # Persist back session state
        st.session_state.chat_messages.append({"role": "assistant", "content": final_answer})
        st.session_state.agent_history = final_state.get("history", st.session_state.agent_history)
        st.session_state.agent_profile = final_state.get("profile", st.session_state.agent_profile)


if __name__ == "__main__":
    main()


