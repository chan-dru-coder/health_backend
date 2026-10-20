from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from doctors.models import DoctorProfile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    doctor_id = serializers.SerializerMethodField()
    consultation_fee = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'role', 'doctor_id', 'consultation_fee')
        read_only_fields = ('id', 'doctor_id', 'consultation_fee')

    def get_doctor_id(self, obj):
        if obj.role == 'doctor' and hasattr(obj, 'doctor_profile'):
            return obj.doctor_profile.id
        return None

    def get_consultation_fee(self, obj):
        if obj.role == 'doctor' and hasattr(obj, 'doctor_profile'):
            return float(obj.doctor_profile.consultation_fee)
        return None


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)
    specialization = serializers.CharField(write_only=True, required=False, allow_blank=True, default='General Physician')
    qualification = serializers.CharField(write_only=True, required=False, allow_blank=True, default='MBBS')

    class Meta:
        model = User
        fields = ('id', 'email', 'full_name', 'password', 'role', 'specialization', 'qualification')
        extra_kwargs = {
            'email': {'required': True},
            'full_name': {'required': True},
            'role': {'required': True},
        }

    def validate_email(self, value):
        normalized_email = value.lower().strip()
        if User.objects.filter(email__iexact=normalized_email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return normalized_email

    def validate_password(self, value):
        if len(value) < 6:
            raise serializers.ValidationError("Password must be at least 6 characters long.")
        return value

    def create(self, validated_data):
        specialization = validated_data.pop('specialization', 'General Physician') or 'General Physician'
        qualification = validated_data.pop('qualification', 'MBBS') or 'MBBS'
        password = validated_data.pop('password')
        role = validated_data.get('role', 'patient')

        user = User.objects.create_user(password=password, **validated_data)

        if role == 'doctor':
            DoctorProfile.objects.create(
                user=user,
                specialization=specialization,
                qualification=qualification,
                experience_years=5,
                hospital_location="MediConnect Central Clinic, Metro City",
                about=f"Dr. {user.full_name} is a dedicated {specialization} with extensive clinical experience.",
                rating=5.0,
                reviews_count=1
            )

        return user


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    username_field = 'email'

    def validate(self, attrs):
        # Email normalization
        if 'email' in attrs:
            attrs['email'] = attrs['email'].lower().strip()
        data = super().validate(attrs)

        user_serializer = UserSerializer(self.user)
        data['user'] = user_serializer.data
        return data
