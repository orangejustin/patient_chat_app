"""
Store messages in the database for persistence.
Patient field is a foreign key. It allows each Conversation to be associated with one Patient.
"""

from django.db import models
from patients.models import Patient

class Conversation(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    started_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Conversation with {self.patient} on {self.started_at}"

class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.CharField(max_length=10)  # 'patient' or 'bot'
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.sender} at {self.timestamp}: {self.content}"
