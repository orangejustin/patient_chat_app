conda activate patient_chat_app

python manage.py runserver

.env 
- settings.py DATABASES configs

python manage.py shell

from patients.models import Patient
from django.utils import timezone
from datetime import datetime

# Delete all existing patients if needed
# Patient.objects.all().delete()

patient = Patient.objects.create(
    first_name='Michael',
    last_name='Davidson',
    date_of_birth=datetime(1980, 1, 1).date(),
    phone_number='858-539-0000',
    email='zechengl@example.com',
    medical_condition='Hypertension',
    medication_regimen='Lisinopril 10mg once daily',
    last_appointment_datetime=timezone.make_aware(datetime(2024, 9, 15, 10, 0)),
    next_appointment_datetime=timezone.make_aware(datetime(2024, 10, 15, 10, 0)),
    doctor_name='John Smith'
)


python manage.py runserver