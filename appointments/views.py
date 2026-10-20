from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.pagination import PageNumberPagination

from .models import Appointment, Prescription
from .serializers import (
    AppointmentSerializer,
    AppointmentCreateSerializer,
    PrescriptionSerializer
)
from doctors.models import Slot
from users.permissions import IsPatient, IsDoctor, IsOwnerOrRelatedDoctor


class AppointmentPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 50


class AppointmentListCreateView(APIView):
    """
    GET /api/appointments/ - List appointments for the current user (patient or doctor)
    POST /api/appointments/ - Book a new appointment (patient only)
    """
    permission_classes = [IsAuthenticated]
    pagination_class = AppointmentPagination

    def get(self, request):
        status_param = request.query_params.get('status')
        user = request.user

        if user.role == 'doctor':
            if hasattr(user, 'doctor_profile'):
                queryset = Appointment.objects.filter(doctor=user.doctor_profile)
            else:
                queryset = Appointment.objects.none()
        else:
            queryset = Appointment.objects.filter(patient=user)

        if status_param:
            queryset = queryset.filter(status=status_param.lower())

        queryset = queryset.select_related('patient', 'doctor', 'doctor__user', 'prescription').order_by('-date', '-time')

        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AppointmentSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = AppointmentSerializer(queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def post(self, request):
        if request.user.role != 'patient':
            return Response(
                {'error': 'Only patients can book appointments.'},
                status=status.HTTP_403_FORBIDDEN
            )

        serializer = AppointmentCreateSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            appointment = serializer.save()
            output_serializer = AppointmentSerializer(appointment)
            return Response(output_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AppointmentCancelView(APIView):
    """
    PATCH /api/appointments/{id}/cancel/
    Patient only - cancels pending or accepted appointments and frees the slot.
    """
    permission_classes = [IsAuthenticated, IsPatient]

    def patch(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk, patient=request.user)
        except Appointment.DoesNotExist:
            return Response(
                {'error': 'Appointment not found or not owned by you.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if appointment.status in ['cancelled', 'rejected', 'completed']:
            return Response(
                {'error': f"Cannot cancel an appointment that is already {appointment.status}."},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = 'cancelled'
        appointment.save()

        # Free the slot
        Slot.objects.filter(
            doctor=appointment.doctor,
            date=appointment.date,
            start_time=appointment.time
        ).update(is_booked=False)

        serializer = AppointmentSerializer(appointment)
        return Response({
            'message': 'Appointment cancelled successfully.',
            'appointment': serializer.data
        }, status=status.HTTP_200_OK)


class AppointmentStatusUpdateView(APIView):
    """
    PATCH /api/appointments/{id}/status/
    Doctor only - accept, reject, or complete appointment.
    """
    permission_classes = [IsAuthenticated, IsDoctor]

    def patch(self, request, pk):
        try:
            appointment = Appointment.objects.get(pk=pk, doctor=request.user.doctor_profile)
        except (Appointment.DoesNotExist, AttributeError):
            return Response(
                {'error': 'Appointment not found or you are not the assigned doctor.'},
                status=status.HTTP_404_NOT_FOUND
            )

        new_status = request.data.get('status')
        if not new_status or new_status not in ['accepted', 'rejected', 'completed']:
            return Response(
                {'error': "Invalid status. Must be one of: 'accepted', 'rejected', 'completed'."},
                status=status.HTTP_400_BAD_REQUEST
            )

        appointment.status = new_status
        appointment.save()

        # If rejected, free the slot
        if new_status == 'rejected':
            Slot.objects.filter(
                doctor=appointment.doctor,
                date=appointment.date,
                start_time=appointment.time
            ).update(is_booked=False)

        serializer = AppointmentSerializer(appointment)
        return Response({
            'message': f"Appointment status updated to '{new_status}'.",
            'appointment': serializer.data
        }, status=status.HTTP_200_OK)


class PrescriptionDetailView(APIView):
    """
    GET /api/appointments/{id}/prescription/ - View prescription (patient or doctor of this appointment)
    POST /api/appointments/{id}/prescription/ - Create/update prescription and complete appointment (doctor only)
    """
    permission_classes = [IsAuthenticated, IsOwnerOrRelatedDoctor]

    def get_appointment(self, pk):
        try:
            return Appointment.objects.select_related('patient', 'doctor', 'doctor__user').get(pk=pk)
        except Appointment.DoesNotExist:
            return None

    def get(self, request, pk):
        appointment = self.get_appointment(pk)
        if not appointment:
            return Response({'error': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)

        self.check_object_permissions(request, appointment)

        try:
            prescription = appointment.prescription
            serializer = PrescriptionSerializer(prescription)
            return Response(serializer.data, status=status.HTTP_200_OK)
        except Prescription.DoesNotExist:
            return Response({'error': 'No prescription found for this appointment.'}, status=status.HTTP_404_NOT_FOUND)

    def post(self, request, pk):
        appointment = self.get_appointment(pk)
        if not appointment:
            return Response({'error': 'Appointment not found.'}, status=status.HTTP_404_NOT_FOUND)

        # Ensure requesting user is the doctor of this appointment
        if request.user.role != 'doctor' or not hasattr(request.user, 'doctor_profile') or appointment.doctor != request.user.doctor_profile:
            return Response(
                {'error': 'Only the assigned doctor can add a prescription.'},
                status=status.HTTP_403_FORBIDDEN
            )

        medical_notes = request.data.get('medical_notes', '').strip()
        prescription_text = request.data.get('prescription_text', '').strip()

        if not medical_notes or not prescription_text:
            return Response(
                {'error': 'Both medical notes and prescription text are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        prescription, created = Prescription.objects.update_or_create(
            appointment=appointment,
            defaults={
                'medical_notes': medical_notes,
                'prescription_text': prescription_text
            }
        )

        # Mark appointment completed
        appointment.status = 'completed'
        appointment.save()

        serializer = PrescriptionSerializer(prescription)
        return Response({
            'message': 'Prescription saved and appointment marked as completed.',
            'prescription': serializer.data
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)
