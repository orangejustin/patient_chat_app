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


# Load OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY) # change your chat llm from https://python.langchain.com/docs/integrations/llms/

# Create a chat prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", """You are a helpful AI health assistant bot. You are assisting {patient_name}, who is {patient_age} years old. 
    Their last appointment was on: {last_appointment}
    Their next appointment is scheduled for: {next_appointment}
    Their doctor's name is: {doctor_name}

    Focus on responding to health-related topics such as:
    • General health and lifestyle inquiries
    • Questions about the patient's medical condition, medication regimen, diet, etc.
    • Requests from the patient to their doctor such as medication changes
    • Appointment and Treatment Protocol Requests
    
    For general greetings, provide a brief welcome and immediately guide the user towards the health-related topics you can assist with.
    
    For health-related queries, provide informative and helpful responses, tailored to {patient_name}'s specific situation when relevant.
    
    If the query is not directly related to the patient's health or the bot's core functionalities, politely redirect the conversation by saying something like: "I understand you're interested in [topic], but I'm designed to assist with your health-related concerns. Is there anything about your health, medications, appointments, or medical condition that you'd like to discuss?"

    Always steer the conversation back to the bot's main purposes: discussing the patient's health, medications, appointments, and medical conditions."""),
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

def get_bot_response(user_input: str, patient, session_id: str = "default") -> str:
    prompt_variables = {
        "patient_name": patient.get_full_name(),
        "patient_age": patient.get_age(),
        "medical_condition": patient.medical_condition,
        "medication_regimen": patient.medication_regimen,
        "last_appointment": patient.get_last_appointment_readable(),
        "next_appointment": patient.get_next_appointment_readable(),
        "doctor_name": patient.doctor_name,
        "input": user_input,
    }
    response = runnable_chain.invoke(
        prompt_variables,
        config={"configurable": {"session_id": session_id}}
    )
    return response.content

def get_bot_response_based_on_entities(entities_input, patient, session_id: str = "default"):
    # Prepare the information obtained from entities
    entity_info = "The patient has provided the following information: " + entities_input
    
    # Prepare the prompt for the AI
    user_input = f"{entity_info}\nPlease reply in under few lines regarding the specific information. It could be an analysis of the usage/frequency of a medication, or about the patient's health condition."
    
    # Prepare the prompt variables
    prompt_variables = {
        "patient_name": patient.get_full_name(),
        "patient_age": patient.get_age(),
        "last_appointment": patient.get_last_appointment_readable(),
        "next_appointment": patient.get_next_appointment_readable(),
        "doctor_name": patient.doctor_name,
        "input": user_input
    }
    
    # Use runnable_chain to get the AI response
    response = runnable_chain.invoke(
        prompt_variables,
        config={"configurable": {"session_id": session_id}}
    )
    
    return response.content

if __name__ == "__main__":
    print("Welcome to the AI Bot. Type 'exit' to stop.")
    session_id = "michael_session_1"  # generate unique session IDs for each user

    # Dummy patient data
    class DummyPatient:
        def __init__(self):
            self.doctor_name = "Dr. Smith"

        def get_full_name(self):
            return "John Doe"

        def get_age(self):
            return 35

        def get_last_appointment_readable(self):
            return "2023-03-15"

        def get_next_appointment_readable(self):
            return "2023-09-15"
    
    patient = DummyPatient()

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = get_bot_response(user_input, patient, session_id)
        print(f"Bot: {response.content}")
