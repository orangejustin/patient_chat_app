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
from prompts import entity_extraction_prompt

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
    ("system", entity_extraction_prompt),
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

def store_entities_as_documents(entities: Dict[str, Any], patient_name: str):
    kg = KnowledgeGraph()

    # Add patient node
    kg.add_entity('Patient', {'name': patient_name})

    for entity_type, value in entities.items():
        if value:
            if entity_type == 'medications':
                medications = value.split(' and ')
                for medication in medications:
                    kg.add_entity('Medication', {'name': medication})
                    kg.add_relationship('Patient', {'name': patient_name}, 'TAKES', 'Medication', {'name': medication})
                    
                    if entities['dosage']:
                        kg.add_entity('Dosage', {'value': entities['dosage']})
                        kg.add_relationship('Medication', {'name': medication}, 'HAS_DOSAGE', 'Dosage', {'value': entities['dosage']})
                    
                    if entities['frequency']:
                        kg.add_entity('Frequency', {'value': entities['frequency']})
                        kg.add_relationship('Medication', {'name': medication}, 'HAS_FREQUENCY', 'Frequency', {'value': entities['frequency']})
            
            elif entity_type in ['symptoms', 'conditions']:
                kg.add_entity(entity_type.capitalize(), {'name': value})
                kg.add_relationship('Patient', {'name': patient_name}, 'HAS', entity_type.capitalize(), {'name': value})
            
            elif entity_type == 'diet':
                kg.add_entity('Diet', {'description': value})
                kg.add_relationship('Patient', {'name': patient_name}, 'FOLLOWS', 'Diet', {'description': value})
            
            elif entity_type == 'appointment_time':
                kg.add_entity('Appointment', {'time': value})
                kg.add_relationship('Patient', {'name': patient_name}, 'SCHEDULES', 'Appointment', {'time': value})

    # Refresh the schema after adding new entities and relationships
    kg.refresh_schema()




if __name__ == "__main__":
    print("Health Assistant Bot: Hello! How can I assist you with your health-related questions today?")

    kg = KnowledgeGraph()
    patient_name = "Michael Davidson"  # This should be set dynamically based on the current patient

    while True:
        user_input = input("You: ")
        if user_input.lower() == 'exit':
            break
        
        if user_input.lower().startswith('query:'):
            # If the input starts with 'query:', use it as a direct question for the graph
            question = user_input[6:].strip()
            response = kg.ask(question)
            print(f"Health Assistant Bot: {response['result']}")
        else:
            # Otherwise, process it as usual for entity extraction
            response = extract_entities(user_input)
            
            if any(value is not None for value in response.values()):
                print(f"Health Assistant Bot: Extracted information: {response}")
                store_entities_as_documents(response, patient_name)
                print("Health Assistant Bot: I've stored that information in your health record.")
            else:
                print("Health Assistant Bot: I couldn't extract any health-related information from that. Can you provide more specific health-related details?")


