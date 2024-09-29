"""
a basic bot 
"""

import re
from datetime import datetime
from .models import AppointmentRequest

HEALTH_TOPICS = ['health', 'medication', 'diet', 'exercise', 'symptoms', 'appointment', 'treatment']
SENSITIVE_TOPICS = ['politics', 'religion', 'finance', 'personal data']

def is_health_related(message):
    return any(topic in message.lower() for topic in HEALTH_TOPICS)

def is_sensitive(message):
    return any(topic in message.lower() for topic in SENSITIVE_TOPICS)

def extract_appointment_request(message):
    # Regex to detect date and time, including AM/PM format
    pattern = r'\b(next\s+\w+|\d{1,2}:\d{2}|\d{1,2}\s*(?:am|pm))\b'
    match = re.search(pattern, message.lower())
    if match:
        return match.group()
    return None

def generate_bot_response(message, patient):
    if is_sensitive(message):
        return "I'm sorry, but I'm not able to discuss that topic."
    elif is_health_related(message):
        appointment_time = extract_appointment_request(message)
        if appointment_time:
            # Save the request or flag it for review
            AppointmentRequest.objects.create(
                patient=patient,
                current_time=patient.next_appointment_datetime,
                requested_time=appointment_time
            )
            return f"I will convey your request to Dr. {patient.doctor_name}."
        else:
            return "Let's discuss your health concerns."
    else:
        return "Please focus on health-related topics so I can assist you better."