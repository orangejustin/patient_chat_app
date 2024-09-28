from django.shortcuts import render

def chat_view(request):
    messages = []  # Placeholder for messages
    if request.method == 'POST':
        user_message = request.POST.get('message')
        # For now, we'll just echo the message back
        bot_response = f"Echo: {user_message}"
        messages.append({'sender': 'patient', 'content': user_message, 'timestamp': 'Now'})
        messages.append({'sender': 'bot', 'content': bot_response, 'timestamp': 'Now'})
    return render(request, 'chat/chat.html', {'messages': messages})
