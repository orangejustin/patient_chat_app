"""
store requests
"""

from django.db import models
from patients.models import Patient

class AppointmentRequest(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    current_time = models.DateTimeField()
    requested_time = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.patient} requested appointment change to {self.requested_time}"
