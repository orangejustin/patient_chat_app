from django.shortcuts import render, redirect
from patients.models import Patient
from .models import Conversation, Message

def chat_view(request):
    patient = Patient.objects.first()  # Retrieve the first (and only) patient
    conversation, created = Conversation.objects.get_or_create(patient=patient)
    messages = conversation.messages.all()

    if request.method == 'POST':
        user_message = request.POST.get('message')
        Message.objects.create(conversation=conversation, sender='patient', content=user_message)
        # Placeholder bot response
        bot_response = f"Echo: {user_message}"
        Message.objects.create(conversation=conversation, sender='bot', content=bot_response)
        return redirect('chat')
    
    context = {
        'messages': messages,
        'patient': patient,
        # 'patient_name': patient_name,
    }
    return render(request, 'chat/chat.html', context)