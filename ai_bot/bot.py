"""
a basic bot

python ai_bot/bot.py
"""

from ai_bot.langchain_integration import get_bot_response
from ai_bot.entity_extraction import extract_entities, store_entities_as_documents
# from ai_bot.knowledge_graph import store_entities_in_neo4j
from ai_bot.models import AppointmentRequest
from django.utils import timezone

def generate_bot_response(message, patient):
    # Get the assistant's response
    response = get_bot_response(message, patient).content

    # Extract the entities from the patient's message
    entities = extract_entities(message)
    
    if entities:
        # Store the entities in the neo4j database
        store_entities_as_documents(entities, patient.get_full_name())

        # Check if an appointment time was requested
        appointment_time = entities.get('appointment_time')
        if appointment_time:
            # Create an AppointmentRequest
            AppointmentRequest.objects.create(
                patient=patient,
                current_time=patient.next_appointment_datetime,
                requested_time=appointment_time
            )
            return f"I will convey your request to Dr. {patient.doctor_name}."
    #         response += f"\n\nI've noted your request for an appointment change to {appointment_time}. I will convey this to Dr. {patient.doctor_name}."

    return response