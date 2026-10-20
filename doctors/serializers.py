from rest_framework import serializers
from .models import DoctorProfile, Slot


class SlotSerializer(serializers.ModelSerializer):
    time_display = serializers.SerializerMethodField()

    class Meta:
        model = Slot
        fields = ('id', 'doctor', 'date', 'start_time', 'time_display', 'is_booked')
        read_only_fields = ('id', 'is_booked')

    def get_time_display(self, obj):
        try:
            return obj.start_time.strftime("%I:%M %p")
        except Exception:
            return str(obj.start_time)


class DoctorListSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)

    class Meta:
        model = DoctorProfile
        fields = (
            'id',
            'full_name',
            'email',
            'specialization',
            'qualification',
            'experience_years',
            'hospital_location',
            'about',
            'rating',
            'reviews_count',
            'profile_image',
            'consultation_fee',
        )


class DoctorDetailSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(source='user.full_name', read_only=True)
    email = serializers.EmailField(source='user.email', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
    available_dates = serializers.SerializerMethodField()

    class Meta:
        model = DoctorProfile
        fields = (
            'id',
            'user_id',
            'full_name',
            'email',
            'specialization',
            'qualification',
            'experience_years',
            'hospital_location',
            'about',
            'rating',
            'reviews_count',
            'profile_image',
            'consultation_fee',
            'available_dates',
        )
        read_only_fields = ('id', 'user_id', 'full_name', 'email', 'rating', 'reviews_count', 'available_dates')

    def validate_consultation_fee(self, value):
        if value < 0:
            raise serializers.ValidationError("Consultation fee cannot be negative.")
        if value > 100000:
            raise serializers.ValidationError("Consultation fee cannot exceed $100,000.")
        return value

    def get_available_dates(self, obj):
        from datetime import date
        today = date.today()
        # Return distinct upcoming dates that have free slots
        upcoming_dates = (
            Slot.objects.filter(doctor=obj, date__gte=today, is_booked=False)
            .values_list('date', flat=True)
            .distinct()
            .order_by('date')[:7]
        )
        return [d.strftime('%Y-%m-%d') for d in upcoming_dates]
