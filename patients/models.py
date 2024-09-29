from django.db import models
from django.utils import timezone
from datetime import datetime

class Patient(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    date_of_birth = models.DateField()
    phone_number = models.CharField(max_length=15)
    email = models.EmailField() 
    medical_condition = models.CharField(max_length=100)
    medication_regimen = models.TextField()
    last_appointment_datetime = models.DateTimeField(default=timezone.now)
    next_appointment_datetime = models.DateTimeField(default=timezone.now)
    doctor_name = models.CharField(max_length=100)

    def __str__(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    def get_age(self):
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))

    def get_last_appointment_readable(self):
        return self.last_appointment_datetime.strftime("%m/%d/%Y %I:%M%p")

    def get_next_appointment_readable(self):
        return self.next_appointment_datetime.strftime("%m/%d/%Y %I:%M%p")

    def save(self, *args, **kwargs):
        if not self.last_appointment_datetime.tzinfo:
            self.last_appointment_datetime = timezone.make_aware(self.last_appointment_datetime)
        if not self.next_appointment_datetime.tzinfo:
            self.next_appointment_datetime = timezone.make_aware(self.next_appointment_datetime)
        super().save(*args, **kwargs)