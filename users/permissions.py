from rest_framework import permissions


class IsPatient(permissions.BasePermission):
    """
    Allows access only to authenticated users with the 'patient' role.
    """
    message = "Access restricted to patients only."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'patient')


class IsDoctor(permissions.BasePermission):
    """
    Allows access only to authenticated users with the 'doctor' role.
    """
    message = "Access restricted to doctors only."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.role == 'doctor')


class IsOwnerOrRelatedDoctor(permissions.BasePermission):
    """
    Object-level permission:
    - Patient can view/cancel their own appointment.
    - Doctor can view/update status/prescribe for their assigned appointment.
    """
    def has_object_permission(self, request, view, obj):
        if not request.user or not request.user.is_authenticated:
            return False

        # Support both Appointment object and Prescription object
        appointment = getattr(obj, 'appointment', obj)

        is_patient = appointment.patient == request.user
        is_doctor = hasattr(appointment.doctor, 'user') and appointment.doctor.user == request.user

        return is_patient or is_doctor
