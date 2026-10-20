from django.contrib import admin
from .models import Appointment, Prescription


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('id', 'patient', 'doctor', 'date', 'time', 'status', 'created_at')
    list_filter = ('status', 'date')
    search_fields = ('patient__full_name', 'patient__email', 'doctor__user__full_name')


@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'appointment', 'created_at')
    search_fields = ('appointment__patient__full_name', 'appointment__doctor__user__full_name')
