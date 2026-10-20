from datetime import date
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import generics, filters
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from users.permissions import IsDoctor

from .models import DoctorProfile, Slot
from .serializers import DoctorListSerializer, DoctorDetailSerializer, SlotSerializer


class DoctorListView(generics.ListAPIView):
    """
    List doctors with search by name/specialization and filter by specialization.
    Publicly accessible.
    """
    queryset = DoctorProfile.objects.select_related('user').all()
    serializer_class = DoctorListSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['specialization']
    search_fields = ['user__full_name', 'specialization', 'hospital_location', 'qualification', 'about']
    ordering_fields = ['rating', 'experience_years', 'consultation_fee']
    ordering = ['-rating', 'user__full_name']


class DoctorProfileMeView(APIView):
    """
    GET /api/doctors/me/ - Get current logged-in doctor's profile
    PATCH /api/doctors/me/ - Update current logged-in doctor's profile (consultation_fee, about, hospital, etc.)
    """
    permission_classes = [IsAuthenticated, IsDoctor]

    def get(self, request):
        try:
            doctor = request.user.doctor_profile
        except DoctorProfile.DoesNotExist:
            return Response({'error': 'Doctor profile not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = DoctorDetailSerializer(doctor)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def patch(self, request):
        try:
            doctor = request.user.doctor_profile
        except DoctorProfile.DoesNotExist:
            return Response({'error': 'Doctor profile not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DoctorDetailSerializer(doctor, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Doctor profile updated successfully.',
                'doctor': serializer.data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DoctorDetailView(generics.RetrieveUpdateAPIView):
    """
    Retrieve single doctor profile details (public).
    Update doctor profile (authenticated doctor owner only).
    """
    queryset = DoctorProfile.objects.select_related('user').all()
    serializer_class = DoctorDetailSerializer

    def get_permissions(self):
        if self.request.method in ['PATCH', 'PUT']:
            return [IsAuthenticated(), IsDoctor()]
        return [AllowAny()]

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        if instance.user != request.user:
            return Response(
                {'error': 'You do not have permission to edit this doctor profile.'},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({
            'message': 'Doctor profile updated successfully.',
            'doctor': serializer.data
        }, status=status.HTTP_200_OK)


class DoctorSlotsView(APIView):
    """
    Get available slots for a specific doctor.
    GET /api/doctors/{id}/slots/?date=YYYY-MM-DD
    """
    permission_classes = [AllowAny]

    def get(self, request, pk):
        try:
            doctor = DoctorProfile.objects.get(pk=pk)
        except DoctorProfile.DoesNotExist:
            return Response({'error': 'Doctor not found.'}, status=status.HTTP_404_NOT_FOUND)

        date_str = request.query_params.get('date')
        if date_str:
            try:
                target_date = date.fromisoformat(date_str)
            except ValueError:
                return Response({'error': 'Invalid date format. Use YYYY-MM-DD.'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            target_date = date.today()

        slots = Slot.objects.filter(
            doctor=doctor,
            date=target_date,
            is_booked=False
        ).order_by('start_time')

        serializer = SlotSerializer(slots, many=True)
        return Response({
            'doctor_id': doctor.id,
            'doctor_name': doctor.user.full_name,
            'date': target_date.strftime('%Y-%m-%d'),
            'slots': serializer.data
        }, status=status.HTTP_200_OK)
