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
from ai_bot.knowledge_graph import KnowledgeGraph
from ai_bot.prompts import entity_extraction_prompt

# Load OpenAI API key from environment variable
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Initialize the LLM
llm = ChatOpenAI(model="gpt-4o-mini", api_key=OPENAI_API_KEY)

# Define a Pydantic model for the output
class HealthEntity(BaseModel):
    medications: Optional[str] = Field(None, description="Names of medications, separated by commas if multiple")
    dosage: Optional[str] = Field(None, description="Dosage of the medication(s)")
    frequency: Optional[str] = Field(None, description="Frequency/number of times per day of taking the medication(s)")
    family_history: Optional[str] = Field(None, description="Relevant family (like parents, siblings) medical history")
    health_issues: Optional[str] = Field(None, description="Current health problems, including both diagnosed conditions and reported symptoms of only the patient not family history")
    appointment_time: Optional[str] = Field(None, description="Requested appointment time")
    # for the purpose of to dynamically query additional data about the patient
    lab_tests: Optional[str] = Field(None, description="Lab tests mentioned or requested, separated by commas")
    doctor_notes: Optional[str] = Field(None, description="Relevant notes or comments mentioned by the doctor")
    weight: Optional[str] = Field(None, description="Patient's weight")
    height: Optional[str] = Field(None, description="Patient's height")
    blood_pressure: Optional[str] = Field(None, description="Blood pressure reading (e.g., '120/80')")
    heart_rate: Optional[str] = Field(None, description="Heart rate in beats per minute")
    temperature: Optional[str] = Field(None, description="Body temperature")
    allergies: Optional[str] = Field(None, description="Known allergies, separated by commas")
    lifestyle_factors: Optional[str] = Field(None, description="Lifestyle factors like smoking, alcohol consumption, exercise habits")
    immunizations: Optional[str] = Field(None, description="Immunization history, separated by commas")

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
            "family_history": None,
            "health_issues": None,
            "appointment_time": None,
            "lab_tests": None,
            "doctor_notes": None,
            "weight": None,
            "height": None,
            "blood_pressure": None,
            "heart_rate": None,
            "temperature": None,
            "allergies": None,
            "lifestyle_factors": None,
            "immunizations": None
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

    family_history_added = False 
    
    for entity_type, value in entities.items():
        if value: # if the value is not None
            if entity_type == 'medications':
                medications = value.split(', ')
                for medication in medications:
                    kg.add_entity('Medication', {'name': medication})
                    kg.add_relationship('Patient', {'name': patient_name}, 'TAKES', 'Medication', {'name': medication})
                    
                    if entities['dosage']:
                        kg.add_entity('Dosage', {'value': entities['dosage']})
                        kg.add_relationship('Medication', {'name': medication}, 'HAS_DOSAGE', 'Dosage', {'value': entities['dosage']})
                    
                    if entities['frequency']:
                        kg.add_entity('Frequency', {'value': entities['frequency']})
                        kg.add_relationship('Medication', {'name': medication}, 'HAS_FREQUENCY', 'Frequency', {'value': entities['frequency']})
            
            elif entity_type == 'family_history':
                family_history_added = True 
                kg.add_entity('FamilyHistory', {'description': value})
                kg.add_relationship('Patient', {'name': patient_name}, 'HAS_FAMILY_HISTORY', 'FamilyHistory', {'description': value})


            elif entity_type == 'health_issues' and not family_history_added: # Only process if family history was not added
                issues = value.split(', ')
                for issue in issues:
                    kg.add_entity('HealthIssue', {'description': issue})
                    kg.add_relationship('Patient', {'name': patient_name}, 'HAS', 'HealthIssue', {'description': issue})
            
            elif entity_type == 'appointment_time':
                kg.add_entity('Appointment', {'time': value})
                kg.add_relationship('Patient', {'name': patient_name}, 'SCHEDULES', 'Appointment', {'time': value})
            
            elif entity_type == 'lab_tests':
                tests = value.split(', ')
                for test in tests:
                    kg.add_entity('LabTest', {'name': test})
                    kg.add_relationship('Patient', {'name': patient_name}, 'HAS_LAB_TEST', 'LabTest', {'name': test})
            
            elif entity_type == 'doctor_notes':
                kg.add_entity('DoctorNote', {'content': value})
                kg.add_relationship('Patient', {'name': patient_name}, 'HAS_NOTE', 'DoctorNote', {'content': value})
            
            elif entity_type in ['weight', 'height', 'blood_pressure', 'heart_rate', 'temperature']:
                vital_data = {
                    'weight': entities.get('weight') if entities.get('weight') is not None else '',
                    'height': entities.get('height') if entities.get('height') is not None else '',
                    'blood_pressure': entities.get('blood_pressure') if entities.get('blood_pressure') is not None else '',
                    'heart_rate': entities.get('heart_rate') if entities.get('heart_rate') is not None else '',
                    'temperature': entities.get('temperature') if entities.get('temperature') is not None else ''
                }
                kg.add_entity('Vital', vital_data)
                kg.add_relationship('Patient', {'name': patient_name}, 'HAS_VITAL', 'Vital', vital_data)
            
            elif entity_type == 'allergies':
                allergies = value.split(', ')
                for allergy in allergies:
                    kg.add_entity('Allergy', {'name': allergy})
                    kg.add_relationship('Patient', {'name': patient_name}, 'HAS_ALLERGY', 'Allergy', {'name': allergy})
            
            elif entity_type == 'lifestyle_factors':
                factors = value.split(', ')
                for factor in factors:
                    kg.add_entity('LifestyleFactor', {'description': factor})
                    kg.add_relationship('Patient', {'name': patient_name}, 'HAS_LIFESTYLE_FACTOR', 'LifestyleFactor', {'description': factor})
            
            elif entity_type == 'immunizations':
                immunizations = value.split(', ')
                for immunization in immunizations:
                    kg.add_entity('Immunization', {'name': immunization, 'date': ''})  # Date is left empty as it's not provided in the current schema
                    kg.add_relationship('Patient', {'name': patient_name}, 'HAS_IMMUNIZATION', 'Immunization', {'name': immunization})

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


