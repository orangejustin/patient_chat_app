"""
Store messages in the database for persistence.
Patient field is a foreign key. It allows each Conversation to be associated with one Patient.
"""

from django.db import models
from patients.models import Patient
from ai_bot.knowledge_graph import KnowledgeGraph

class Conversation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation with {self.patient} on {self.started_at}"
    
    def add_welcome_message(self):
        welcome_message = f"Hi {self.patient.first_name}, what can I help you with today?"
        Message.objects.create(conversation=self, sender='bot', content=welcome_message)

    def restart(self):
        # delete all messages
        self.messages.all().delete()
        # clear the knowledge graph
        kg = KnowledgeGraph()
        kg.clear_graph()
        # add welcome message again
        self.add_welcome_message()

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10)  # 'patient' or 'bot'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} at {self.timestamp}: {self.content}"
