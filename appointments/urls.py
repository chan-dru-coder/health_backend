from django.urls import path
from .views import (
    AppointmentListCreateView,
    AppointmentCancelView,
    AppointmentStatusUpdateView,
    PrescriptionDetailView
)

urlpatterns = [
    path('', AppointmentListCreateView.as_view(), name='appointment_list_create'),
    path('<int:pk>/cancel/', AppointmentCancelView.as_view(), name='appointment_cancel'),
    path('<int:pk>/status/', AppointmentStatusUpdateView.as_view(), name='appointment_status'),
    path('<int:pk>/prescription/', PrescriptionDetailView.as_view(), name='appointment_prescription'),
]
