# ai_bot/bot.py

from ai_bot.langchain_integration import get_bot_response, get_bot_response_based_on_entities
from django.utils import timezone
from collections import defaultdict

from ai_bot.agent import agent_app, AgentState  # Import the agent and state

# Session state storage (use a more robust storage in production, e.g., Redis)
session_states = defaultdict(lambda: None)

def generate_bot_response(message, patient, session_id="default"):
    # Retrieve or initialize the state for the session
    state = session_states.get(session_id)
    if not state:
        state = AgentState(
            input=message,
            patient=patient,
            session_id=session_id
        )
        session_states[session_id] = state
    else:
        state.input = message  # Update the input with the user's message

    # Run the agent synchronously
    result = agent_app.invoke(state)

    if result.get("follow_up_question"):
        return result["follow_up_question"]
    else:
        # del session_states[session_id]
        return result["response"]