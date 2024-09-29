from django.shortcuts import render
from patients.models import Patient

def chat_view(request):
    patient = Patient.objects.first()  # Retrieve the first (and only) patient
    if patient is None:
        # Handle the case where no patient exists
        patient_name = "Guest"
    else:
        patient_name = f"{patient.first_name} {patient.last_name}"

    messages = []  # Placeholder for messages
    if request.method == 'POST':
        user_message = request.POST.get('message')
        # For now, we'll just echo the message back
        bot_response = f"Echo: {user_message}"
        messages.append({'sender': 'patient', 'content': user_message, 'timestamp': 'Now'})
        messages.append({'sender': 'bot', 'content': bot_response, 'timestamp': 'Now'})

    context = {
        'messages': messages,
        'patient': patient,
        'patient_name': patient_name,
    }
    return render(request, 'chat/chat.html', context)