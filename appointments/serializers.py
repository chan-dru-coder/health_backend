from datetime import date as dt_date, datetime
from rest_framework import serializers
from django.db import transaction

from .models import Appointment, Prescription
from doctors.models import DoctorProfile, Slot
from doctors.serializers import DoctorListSerializer
from users.serializers import UserSerializer


class PrescriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Prescription
        fields = ('id', 'appointment', 'medical_notes', 'prescription_text', 'created_at')
        read_only_fields = ('id', 'created_at')


class AppointmentSerializer(serializers.ModelSerializer):
    patient = UserSerializer(read_only=True)
    doctor = DoctorListSerializer(read_only=True)
    prescription = PrescriptionSerializer(read_only=True)
    time_display = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = (
            'id',
            'patient',
            'doctor',
            'date',
            'time',
            'time_display',
            'status',
            'created_at',
            'updated_at',
            'prescription',
        )

    def get_time_display(self, obj):
        try:
            return obj.time.strftime("%I:%M %p")
        except Exception:
            return str(obj.time)


class AppointmentCreateSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(write_only=True)
    slot_id = serializers.IntegerField(write_only=True, required=False, allow_null=True)

    class Meta:
        model = Appointment
        fields = ('doctor_id', 'date', 'time', 'slot_id')

    def validate_date(self, value):
        if value < dt_date.today():
            raise serializers.ValidationError("Cannot book appointments for past dates.")
        return value

    def validate(self, attrs):
        doctor_id = attrs.get('doctor_id')
        apt_date = attrs.get('date')
        apt_time = attrs.get('time')
        slot_id = attrs.get('slot_id')

        try:
            doctor = DoctorProfile.objects.get(pk=doctor_id)
        except DoctorProfile.DoesNotExist:
            raise serializers.ValidationError({"doctor_id": "Doctor does not exist."})

        # Prevent double booking: check if doctor already has a non-cancelled/non-rejected appointment
        existing_appointment = Appointment.objects.filter(
            doctor=doctor,
            date=apt_date,
            time=apt_time
        ).exclude(status__in=['cancelled', 'rejected']).exists()

        if existing_appointment:
            raise serializers.ValidationError("This time slot is already booked for this doctor.")

        attrs['doctor_instance'] = doctor
        return attrs

    @transaction.atomic
    def create(self, validated_data):
        doctor = validated_data.pop('doctor_instance')
        validated_data.pop('doctor_id', None)
        slot_id = validated_data.pop('slot_id', None)
        apt_date = validated_data['date']
        apt_time = validated_data['time']
        patient = self.context['request'].user

        # Create the appointment
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            date=apt_date,
            time=apt_time,
            status='pending'
        )

        # Mark slot as booked if exists or slot_id provided
        if slot_id:
            Slot.objects.filter(id=slot_id, doctor=doctor).update(is_booked=True)
        else:
            Slot.objects.filter(
                doctor=doctor,
                date=apt_date,
                start_time=apt_time
            ).update(is_booked=True)

        return appointment
