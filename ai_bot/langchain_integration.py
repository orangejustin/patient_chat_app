"""
langchain integration

python ai_bot/langchain_integration.py
"""

import os
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from langchain.prompts import PromptTemplate


# Load OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY) # change your chat llm from https://python.langchain.com/docs/integrations/llms/

# Create a chat prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI health assistant bot. You only respond to health-related topics and politely decline to discuss unrelated, sensitive, or controversial topics."),
    MessagesPlaceholder(variable_name="history"),
    ("human", "{input}")
])

# Create the chain
chain = prompt | llm

# Create a simple in-memory chat message history
class InMemoryChatMessageHistory(BaseChatMessageHistory):
    def __init__(self):
        self.messages = []

    def add_message(self, message: BaseMessage) -> None:
        self.messages.append(message)

    def clear(self) -> None:
        self.messages = []

# Create a function to get session history
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in get_session_history.sessions:
        get_session_history.sessions[session_id] = InMemoryChatMessageHistory()
    return get_session_history.sessions[session_id]

# Initialize the sessions dictionary
get_session_history.sessions = {}

# Create a RunnableWithMessageHistory
runnable_chain = RunnableWithMessageHistory(
    chain,
    get_session_history=get_session_history,
    input_messages_key="input",
    history_messages_key="history"
)

def get_bot_response(user_input: str, session_id: str = "default") -> str:
    response = runnable_chain.invoke(
        {"input": user_input},
        config={"configurable": {"session_id": session_id}}
    )
    return response

if __name__ == "__main__":
    print("Welcome to the AI Bot. Type 'exit' to stop.")
    session_id = "michael_session_1"  # generate unique session IDs for each user
    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = get_bot_response(user_input, session_id)
        print(f"Bot: {response.content}")