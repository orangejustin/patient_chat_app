"""
entity extraction

python ai_bot/entity_extraction.py

example:

You: i am taking lisinopril twice a day
Health Assistant Bot: {'medication': 'lisinopril', 'dosage': 'twice a day', 'frequency': 'daily'}
"""

import os
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from knowledge_graph import KnowledgeGraph

# Load OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize the LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", api_key=OPENAI_API_KEY)

# Define a Pydantic model for the output
class HealthEntity(BaseModel):
    medications: Optional[str] = Field(None, description="Names of medications, separated by 'and' if multiple")
    dosage: Optional[str] = Field(None, description="Dosage of the medication(s)")
    frequency: Optional[str] = Field(None, description="Frequency of taking the medication(s)")
    symptoms: Optional[str] = Field(None, description="Symptoms mentioned")
    conditions: Optional[str] = Field(None, description="Health conditions mentioned")
    diet: Optional[str] = Field(None, description="Diet information mentioned")
    appointment_time: Optional[str] = Field(None, description="Requested appointment time")

# Create a JSON output parser with the Pydantic model
json_parser = JsonOutputParser(pydantic_object=HealthEntity)

# Create a chat prompt template
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful AI health assistant bot. Extract health-related entities from the user's input and format them as JSON. Include fields for medications (as a single string, separating multiple medications with 'and'), dosage, frequency, symptoms, conditions, diet, and appointment_time."),
    ("human", "{input}")
])

# Create the chain
chain = prompt | llm | json_parser

def extract_entities(user_input: str) -> dict:
    try:
        response = chain.invoke({"input": user_input})
        # Initialize all fields with None
        result = {
            "medications": None,
            "dosage": None,
            "frequency": None,
            "symptoms": None,
            "conditions": None,
            "diet": None,
            "appointment_time": None
        }
        # Update only the fields that are present in the response
        for key, value in response.items():
            if value is not None and value != "":
                result[key] = value
        return result
    except Exception as e:
        print(f"An error occurred: {str(e)}")
        return {}

def store_entities_as_documents(entities: Dict[str, Any]):
    kg = KnowledgeGraph()
    patient_name = "Michael" # will change to the variable as input patient object

    # Convert entities to documents
    documents = []

    # Medications
    if entities['medications']:
        content = f"{patient_name}'s medications: {entities['medications']}"
        if entities['dosage']:
            content += f", dosage: {entities['dosage']}"
        if entities['frequency']:
            content += f", frequency: {entities['frequency']}"
        documents.append({
            "id": f"{patient_name}-medications",
            "text": content,
            "metadata": {"type": "medications", "patient": patient_name}
        })

    # Symptoms
    if entities['symptoms']:
        content = f"{patient_name} reported symptom(s): {entities['symptoms']}"
        documents.append({
            "id": f"{patient_name}-symptoms",
            "text": content,
            "metadata": {"type": "symptoms", "patient": patient_name}
        })

    # Conditions
    if entities['conditions']:
        content = f"{patient_name} has condition(s): {entities['conditions']}"
        documents.append({
            "id": f"{patient_name}-conditions",
            "text": content,
            "metadata": {"type": "conditions", "patient": patient_name}
        })

    # Diet
    if entities['diet']:
        content = f"{patient_name}'s diet information: {entities['diet']}"
        documents.append({
            "id": f"{patient_name}-diet",
            "text": content,
            "metadata": {"type": "diet", "patient": patient_name}
        })

    # Appointment Time
    if entities['appointment_time']:
        content = f"{patient_name} requested appointment time: {entities['appointment_time']}"
        documents.append({
            "id": f"{patient_name}-appointment-{entities['appointment_time']}",
            "text": content,
            "metadata": {"type": "appointment", "patient": patient_name}
        })

    # Add documents to vector store
    for doc in documents:
        kg.add_document(doc_id=doc["id"], text=doc["text"], metadata=doc["metadata"])



if __name__ == "__main__":
    print("Health Assistant Bot: Hello! How can I assist you with your health-related questions today?")

    # user_input = "I am taking lisinopril 2.5 mg once a day"
    # user_input = "I have a headache and I am taking ibuprofen"
    # user_input = "I am on a low-fat diet" 
    # user_input = "I have a headache and I am taking ibuprofen"
    # user_input = "i am taking lisinopril and ibuprofen twice a day"
    # user_input = "Can we reschedule the appointment to next Friday at 3 PM?"

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        response = extract_entities(user_input)
        
        # Check if any entities were extracted
        if any(value is not None for value in response.values()):
            print(f"Health Assistant Bot: {response}")
            store_entities_as_documents(response)
            print("Health Assistant Bot: I've stored that information in your health record.")
        else:
            print("Health Assistant Bot: I couldn't extract any health-related information from that. Can you provide more specific health-related details?")
    # while True:
    #     user_input = input("You: ")
    #     if user_input.lower() == 'exit':
    #         break
    #     response = extract_entities(user_input)
    #     if response:
    #         print(f"Health Assistant Bot: {response}")
    #     else:
    #         print("Health Assistant Bot: I couldn't extract any health-related information from that. Can you provide more specific health-related details?")



