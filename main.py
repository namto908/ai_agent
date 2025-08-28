"""
Main entry point for the AI Agent's interactive chat loop.
"""
from dotenv import load_dotenv

# Load environment variables from .env file at the very beginning
load_dotenv()

from ai_agent.graph import build_graph
from ai_agent.state import AgentState

def run_chat_loop():
    """
    Initializes the agent and runs an interactive chat loop in the terminal.
    """
    print("--- AI Agent Chat Interface ---")
    print("Agent is ready. Type your question.")
    print("Type 'exit' or 'quit' to end the chat.")
    
    # Build the graph once, it can be reused for multiple conversations
    app = build_graph()
    session_history = []
    session_profile = {}
    session_chat_history = []

    while True:
        try:
            question = input("\nYou: ")

            if question.lower() in ["exit", "quit", "bye"]:
                print("\nAgent: Goodbye!")
                break

            if not question.strip():
                continue

            # Create a new state for each conversation
            initial_state = AgentState(
                question=question,
                history=session_history,
                profile=session_profile,
                chat_history=session_chat_history,
            )

            print("Agent: Thinking...")
            
            # Use .invoke() for a simple request-response interaction
            # It runs the graph until the end and returns the final state.
            final_state = app.invoke(initial_state, {"recursion_limit": 50})

            # Print the final answer
            final_answer = final_state.get('final_answer', "Sorry, I encountered an issue and could not find an answer.")
            print(f"\nAgent: {final_answer}")

            # Optional: Print errors if any occurred during the run
            if final_state.get('errors'):
                print("\n--- Encountered Errors ---")
                for error in final_state['errors']:
                    print(f"- {error}")
                print("-------------------------")

            # Persist in-memory session history across turns
            session_history = final_state.get('history', session_history)
            session_profile = final_state.get('profile', session_profile)
            # Update chat history
            session_chat_history = list(session_chat_history) + [
                {"role": "user", "content": question},
                {"role": "assistant", "content": final_answer},
            ]

        except KeyboardInterrupt:
            print("\n\nAgent: Goodbye!")
            break
        except Exception as e:
            print(f"\nAn unexpected error occurred: {e}")
            print("Restarting the loop.")

if __name__ == "__main__":
    run_chat_loop()