from django.shortcuts import render
from django.http import JsonResponse
from patients.models import Patient 
from .models import Conversation, Message
from ai_bot.bot import generate_bot_response
from ai_bot.models import AppointmentRequest

def chat_view(request):
    patient = Patient.objects.first()  # Retrieve the first (and only) patient
    conversation, created = Conversation.objects.get_or_create(patient=patient)
    messages = conversation.messages.all()
    appointment_requests = AppointmentRequest.objects.filter(patient=patient)

    if request.method == 'POST':
        user_message = request.POST.get('message')
        Message.objects.create(conversation=conversation, sender='patient', content=user_message)
        # Generate bot response using AI bot
        bot_response = generate_bot_response(user_message, patient)
        bot_message = Message.objects.create(conversation=conversation, sender='bot', content=bot_response)
        
        # Check if a new appointment request was made
        new_appointment_request = None
        latest_request = AppointmentRequest.objects.filter(patient=patient).last()
        if latest_request:
            new_appointment_request = {
                'current_time': latest_request.current_time.strftime("%Y-%m-%d %H:%M"),
                'requested_time': latest_request.requested_time
            }
        
        # Return JSON response with bot message and new appointment request
        return JsonResponse({
            'status': 'success',
            'bot_message': {
                'content': bot_message.content,
                'timestamp': bot_message.timestamp.strftime("%Y-%m-%d %H:%M")
            },
            'new_appointment_request': new_appointment_request
        })
    
    context = {
        'messages': messages,
        'patient': patient,
        'appointment_requests': appointment_requests,
    }
    return render(request, 'chat/chat.html', context)