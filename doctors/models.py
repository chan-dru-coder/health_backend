from django.db import models
from django.conf import settings


class DoctorProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='doctor_profile'
    )
    specialization = models.CharField(max_length=100, default='General Physician')
    qualification = models.CharField(max_length=100, default='MBBS')
    experience_years = models.PositiveIntegerField(default=5)
    hospital_location = models.CharField(max_length=255, default='MediConnect Hospital, Metro City')
    about = models.TextField(blank=True, default='')
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=4.9)
    reviews_count = models.PositiveIntegerField(default=120)
    profile_image = models.CharField(max_length=500, blank=True, default='')
    consultation_fee = models.DecimalField(max_digits=8, decimal_places=2, default=500.00)

    class Meta:
        ordering = ['-rating', 'user__full_name']

    def __str__(self):
        return f"Dr. {self.user.full_name} - {self.specialization}"


class Slot(models.Model):
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='slots'
    )
    date = models.DateField()
    start_time = models.TimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        ordering = ['date', 'start_time']
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'date', 'start_time'],
                name='unique_doctor_date_time_slot'
            )
        ]

    def __str__(self):
        status = "Booked" if self.is_booked else "Available"
        return f"{self.doctor.user.full_name} | {self.date} {self.start_time.strftime('%H:%M')} ({status})"
