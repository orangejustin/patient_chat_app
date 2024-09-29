// Function to scroll to the latest message
function scrollToLatestMessage() {
    var chatMessages = document.getElementById('chat-messages');
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function createMessageElement(sender, content, timestamp) {
    var newMessage = document.createElement('div');
    newMessage.className = `message ${sender}`;
    newMessage.innerHTML = `
        <span>${timestamp} - ${sender}:</span>
        <p>${content}</p>
    `;
    return newMessage;
}

function updateAppointmentRequests(newRequest) {
    var appointmentRequestsContainer = document.getElementById('appointment-requests');
    var noRequestsMessage = appointmentRequestsContainer.querySelector('p');
    
    if (noRequestsMessage && noRequestsMessage.textContent === 'No appointment requests.') {
        noRequestsMessage.remove();
    }

    var newRequestElement = document.createElement('p');
    newRequestElement.textContent = `You requested to change your appointment from ${newRequest.current_time} to ${newRequest.requested_time}.`;
    appointmentRequestsContainer.appendChild(newRequestElement);
}

function onDOMLoaded() {
    scrollToLatestMessage();

    var chatMessages = document.getElementById('chat-messages');
    var observer = new MutationObserver(function(mutations) {
        scrollToLatestMessage();
    });

    observer.observe(chatMessages, { childList: true, subtree: true });

    var form = document.querySelector('.message-form');
    if (form) {
        form.addEventListener('submit', function(event) {
            event.preventDefault();

            var messageInput = form.querySelector('input[name="message"]');
            var messageContent = messageInput.value;

            if (messageContent.trim() === '') return;

            messageInput.value = '';

            var userMessage = createMessageElement('patient', messageContent, new Date().toLocaleString());
            chatMessages.appendChild(userMessage);

            // Send message to server
            fetch('', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
                },
                body: `message=${encodeURIComponent(messageContent)}`
            })
            .then(response => response.json())
            .then(data => {
                if (data.status === 'success') {
                    var botMessage = createMessageElement('bot', data.bot_message.content, data.bot_message.timestamp);
                    chatMessages.appendChild(botMessage);
                    
                    // Update appointment requests if a new request was made
                    if (data.new_appointment_request) {
                        updateAppointmentRequests(data.new_appointment_request);
                    }
                }
            })
            .catch(error => console.error('Error:', error));
        });
    }
}

// Use DOMContentLoaded instead of window.onload
document.addEventListener('DOMContentLoaded', onDOMLoaded);
