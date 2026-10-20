from django.contrib import admin
from .models import DoctorProfile, Slot


@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'specialization', 'qualification', 'experience_years', 'hospital_location', 'rating')
    list_filter = ('specialization',)
    search_fields = ('user__full_name', 'user__email', 'specialization', 'hospital_location')


@admin.register(Slot)
class SlotAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'date', 'start_time', 'is_booked')
    list_filter = ('date', 'is_booked')
    search_fields = ('doctor__user__full_name',)
